"""
AMIP Execution Engine.
Manages sequential and parallel execution of plan tasks using registered ITaskExecutors.
Pure orchestrator - Handles dispatch, timing, timeouts, and timeline updates.
"""
from __future__ import annotations
import threading
import time
from typing import Dict, Any, List, Optional, Tuple
from app.services.amip.interfaces.supervisor_interfaces import IExecutionEngine, ITaskExecutor
from app.services.amip.models.execution_plan import ExecutionPlan
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.agent_record import AgentExecutionRecord
from app.services.amip.models.agent_vote import AgentVote
from app.services.amip.models.enums import AgentStatus, ExecutionStatus, PlanningStrategy
from app.services.amip.supervisor.events import (
    WorkflowStarted,
    WorkflowCompleted,
    TaskStarted,
    TaskCompleted,
    TaskFailed,
    TaskCancelled,
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
    """
    Executes tasks in an ExecutionPlan by delegating to registered ITaskExecutors.
    Supports sequential execution, dependency topological ordering, and timeout handling.
    """

    def __init__(self, executors: Optional[List[ITaskExecutor]] = None):
        self._executors: List[ITaskExecutor] = list(executors) if executors else []
        self._cancelled_workflows: Dict[str, bool] = {}
        self._lock: threading.RLock = threading.RLock()

    def register_executor(self, executor: ITaskExecutor) -> None:
        """Registers a new task executor (thread-safe)."""
        with self._lock:
            self._executors.append(executor)

    def cancel(self, workflow_id: str) -> bool:
        """Flags a workflow ID for cancellation (thread-safe)."""
        with self._lock:
            self._cancelled_workflows[workflow_id] = True
            return True

    def is_cancelled(self, workflow_id: str) -> bool:
        """Checks if a workflow has been cancelled (thread-safe)."""
        with self._lock:
            return self._cancelled_workflows.get(workflow_id, False)

    def find_executor(self, task: ExecutionTask) -> Optional[ITaskExecutor]:
        """Finds a registered executor that supports the given task (thread-safe)."""
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
        """
        Executes plan tasks in dependency order, updating timeline, blackboard, and supervisor state.
        Returns Tuple[List[AgentVote], SupervisorState, SupervisorMetrics].
        """
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

        # 1. Resolve ordered tasks via topological sort
        ordered_tasks = plan.ordered_tasks()
        total_tasks = len(ordered_tasks)

        # Emit WorkflowStarted event
        event_start = WorkflowStarted(
            workflow_id=workflow_id,
            total_tasks=total_tasks,
            request_summary=plan.request_summary,
        )
        blackboard.put(f"event_{event_start.event_type}", event_start.to_dict())

        # 2. Execute tasks sequentially or in parallel depending on strategy
        for task in ordered_tasks:
            # Check cancellation
            if self.is_cancelled(workflow_id):
                state.overall_status = ExecutionStatus.CANCELLED
                raise ExecutionCancelled(workflow_id, "Plan execution cancelled by user")

            # Check workflow timeout
            if timeout_ms and timeout_ms > 0:
                elapsed_ms = calculate_duration_ms(start_ts)
                if elapsed_ms > timeout_ms:
                    state.overall_status = ExecutionStatus.FAILED
                    raise WorkflowTimeout(workflow_id, timeout_ms)

            # Find matching executor
            executor = self.find_executor(task)
            if not executor:
                state.failed_tasks.append(task.task_id)
                state.overall_status = ExecutionStatus.FAILED
                raise UnsupportedTask(task.task_id, task.task_type.value if hasattr(task.task_type, "value") else str(task.task_type))

            # Update State & Timeline
            state.current_task = task.task_id
            state.running_tasks.append(task.task_id)
            task_start_ts = current_utc_timestamp()

            rec = AgentExecutionRecord(
                agent_name=task.required_agents[0] if task.required_agents else "UnknownAgent",
                start_time=task_start_ts,
                input_summary=f"Executing task '{task.task_name}' ({task.task_id})",
            )
            context.timeline.append(rec)

            try:
                # Dispatch execution to adapter
                vote, artifacts = executor.execute(task, context, blackboard)

                task_end_ts = current_utc_timestamp()
                dur_ms = calculate_duration_ms(task_start_ts, task_end_ts)
                durations.append(dur_ms)

                rec.complete(
                    status=AgentStatus.SUCCESS,
                    confidence=vote.confidence,
                    output_summary=vote.reason,
                    warnings=vote.warnings,
                )

                # Store vote and artifacts on blackboard
                collected_votes.append(vote)
                blackboard.put(f"vote_{vote.agent_name}", vote.to_dict())
                for k, v in artifacts.items():
                    blackboard.put(k, v)

                # Update State
                state.running_tasks.remove(task.task_id)
                state.completed_tasks.append(task.task_id)
                state.update_progress(total_tasks)

            except Exception as task_err:
                task_end_ts = current_utc_timestamp()
                dur_ms = calculate_duration_ms(task_start_ts, task_end_ts)
                durations.append(dur_ms)

                rec.complete(
                    status=AgentStatus.FAILURE,
                    confidence=0.0,
                    output_summary=f"Task error: {str(task_err)}",
                    errors=[str(task_err)],
                )

                state.running_tasks.remove(task.task_id)
                state.failed_tasks.append(task.task_id)
                metrics.tasks_failed += 1
                state.update_progress(total_tasks)

                if plan.policy.strict_order:
                    state.overall_status = ExecutionStatus.FAILED
                    raise TaskExecutionFailed(task.task_id, rec.agent_name, str(task_err))

        # 3. Complete Workflow Execution
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
        """Returns statistics on registered executors (thread-safe)."""
        with self._lock:
            return {
                "registered_executors_count": len(self._executors),
                "executor_names": [getattr(ex, "agent_name", ex.__class__.__name__) for ex in self._executors],
            }
