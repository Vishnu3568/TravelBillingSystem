"""
Execution engine dispatching plan tasks via adapter registry or registered task executors.
"""
from __future__ import annotations
import threading
import time
from typing import Dict, Any, List, Optional, Tuple
from app.services.amip.interfaces.supervisor_interfaces import IExecutionEngine, ITaskExecutor
from app.services.amip.adapters.adapter_registry import AdapterRegistry
from app.services.amip.models.execution_plan import ExecutionPlan
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.agent_record import AgentExecutionRecord
from app.services.amip.models.agent_vote import AgentVote
from app.services.amip.models.enums import AgentStatus, ExecutionStatus
from app.services.amip.supervisor.events import (
    WorkflowStarted,
    WorkflowCompleted,
)
from app.services.amip.supervisor.supervisor_state import SupervisorState, SupervisorMetrics
from app.services.amip.exceptions import (
    UnsupportedTask,
    TaskExecutionFailed,
    ExecutionCancelled,
    WorkflowTimeout,
)
from app.services.amip.utils.time_utils import current_utc_timestamp, calculate_duration_ms


class ExecutionEngine(IExecutionEngine):
    """Executes task plans in dependency order while managing state, timeouts, and timeline updates."""

    def __init__(
        self,
        executors: Optional[List[ITaskExecutor]] = None,
        adapter_registry: Optional[AdapterRegistry] = None,
    ):
        self._executors: List[ITaskExecutor] = list(executors) if executors is not None else []
        if adapter_registry is not None:
            self.adapter_registry = adapter_registry
        elif executors is not None:
            self.adapter_registry = AdapterRegistry(register_defaults=False)
        else:
            self.adapter_registry = AdapterRegistry(register_defaults=True)

        self._cancelled_workflows: Dict[str, bool] = {}
        self._lock: threading.RLock = threading.RLock()

    def register_executor(self, executor: ITaskExecutor) -> None:
        """Registers a task executor."""
        with self._lock:
            self._executors.append(executor)

    def cancel(self, workflow_id: str) -> bool:
        """Flags a workflow for cancellation."""
        with self._lock:
            self._cancelled_workflows[workflow_id] = True
            return True

    def is_cancelled(self, workflow_id: str) -> bool:
        """Checks whether workflow cancellation was requested."""
        with self._lock:
            return self._cancelled_workflows.get(workflow_id, False)

    def find_executor(self, task: ExecutionTask) -> Optional[ITaskExecutor]:
        """Finds matching registered executor for a task."""
        with self._lock:
            for ex in self._executors:
                if ex.supports(task):
                    return ex
            return None

    def execute_plan(
        self,
        plan: ExecutionPlan,
        context: Any,
        blackboard: Any,
        timeout_ms: Optional[float] = None,
    ) -> Tuple[List[AgentVote], SupervisorState, SupervisorMetrics]:
        """Executes task graph and collects votes, updating supervisor state and timeline."""
        if not plan:
            raise ValueError("ExecutionPlan cannot be null.")

        workflow_id = plan.workflow_id
        start_ts = current_utc_timestamp()

        state = SupervisorState(
            workflow_id=workflow_id,
            overall_status=ExecutionStatus.RUNNING,
        )
        metrics = SupervisorMetrics(workflow_id=workflow_id)
        durations: List[float] = []
        collected_votes: List[AgentVote] = []

        ordered_tasks = plan.ordered_tasks()
        total_tasks = len(ordered_tasks)

        event_start = WorkflowStarted(
            workflow_id=workflow_id,
            total_tasks=total_tasks,
            request_summary=plan.request_summary,
        )
        blackboard.put(f"event_{event_start.event_type}", event_start.to_dict())

        for task in ordered_tasks:
            if self.is_cancelled(workflow_id):
                state.overall_status = ExecutionStatus.CANCELLED
                raise ExecutionCancelled(workflow_id, "Plan execution cancelled by user")

            if timeout_ms and timeout_ms > 0:
                elapsed_ms = calculate_duration_ms(start_ts)
                if elapsed_ms > timeout_ms:
                    state.overall_status = ExecutionStatus.FAILED
                    raise WorkflowTimeout(workflow_id, timeout_ms)

            state.current_task = task.task_id
            state.running_tasks.append(task.task_id)
            task_start_ts = current_utc_timestamp()

            agent_key = task.required_agents[0] if task.required_agents else task.task_type.value
            adapter = self.adapter_registry.resolve(agent_key) or self.adapter_registry.resolve(task.task_type.value)

            try:
                if adapter:
                    res_dict = adapter.execute(task, context)
                    task_end_ts = current_utc_timestamp()
                    dur_ms = res_dict.get("duration_ms", calculate_duration_ms(task_start_ts, task_end_ts))
                    durations.append(dur_ms)

                    conf = float(res_dict.get("confidence", 0.90))
                    summary_text = res_dict.get("output_summary", "Adapter executed successfully")
                    rec_action = "APPROVE" if res_dict.get("status") == "SUCCESS" else "REVIEW"

                    vote = AgentVote(
                        agent_name=res_dict.get("agent_name", agent_key),
                        confidence=conf,
                        vote=rec_action,
                        reason=summary_text,
                        warnings=res_dict.get("warnings", []),
                    )
                    artifacts = {"result": res_dict}
                else:
                    executor = self.find_executor(task)
                    if not executor:
                        state.failed_tasks.append(task.task_id)
                        state.overall_status = ExecutionStatus.FAILED
                        raise UnsupportedTask(task.task_id, str(task.task_type))

                    vote, artifacts = executor.execute(task, context, blackboard)
                    task_end_ts = current_utc_timestamp()
                    dur_ms = calculate_duration_ms(task_start_ts, task_end_ts)
                    durations.append(dur_ms)

                    rec = AgentExecutionRecord(
                        agent_name=task.required_agents[0] if task.required_agents else "UnknownAgent",
                        start_time=task_start_ts,
                        end_time=task_end_ts,
                        duration_ms=dur_ms,
                        status=AgentStatus.SUCCESS,
                        input_summary=f"Executing task '{task.task_name}' ({task.task_id})",
                        output_summary=vote.reason,
                    )
                    context.timeline.append(rec)

                collected_votes.append(vote)
                blackboard.put(f"vote_{vote.agent_name}", vote.to_dict())
                for k, v in artifacts.items():
                    blackboard.put(k, v)

                state.running_tasks.remove(task.task_id)
                state.completed_tasks.append(task.task_id)
                state.update_progress(total_tasks)

            except (UnsupportedTask, ExecutionCancelled, WorkflowTimeout):
                raise
            except Exception as task_err:
                task_end_ts = current_utc_timestamp()
                dur_ms = calculate_duration_ms(task_start_ts, task_end_ts)
                durations.append(dur_ms)

                state.running_tasks.remove(task.task_id)
                state.failed_tasks.append(task.task_id)
                metrics.tasks_failed += 1
                state.update_progress(total_tasks)

                if plan.policy.strict_order:
                    state.overall_status = ExecutionStatus.FAILED
                    raise TaskExecutionFailed(task.task_id, agent_key, str(task_err))

        state.current_task = None
        state.overall_status = ExecutionStatus.COMPLETED
        total_dur_ms = calculate_duration_ms(start_ts)

        metrics.total_execution_time_ms = total_dur_ms
        metrics.calculate_metrics(durations, total_tasks)

        event_done = WorkflowCompleted(
            workflow_id=workflow_id,
            status=state.overall_status.value,
            total_duration_ms=total_dur_ms,
            tasks_completed=len(state.completed_tasks),
            tasks_failed=len(state.failed_tasks),
        )
        blackboard.put(f"event_{event_done.event_type}", event_done.to_dict())

        return collected_votes, state, metrics

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on registered adapters and executors."""
        with self._lock:
            adapters_list = list(self.adapter_registry.list_adapters().keys())
            return {
                "registered_adapters_count": len(adapters_list),
                "registered_adapters": adapters_list,
                "registered_executors_count": len(self._executors),
            }
