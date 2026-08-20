"""
AMIP Autonomous Workflow Gateway & Execution Dispatcher.
Unified facade coordinating request ingress, context initialization, planning,
supervisor orchestration, cooperative cancellation, explainability reporting, and audit bundling.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, List, Optional, Tuple
from app.services.amip.models.enums import (
    TaskType,
    Priority,
    ExecutionMode,
    ExecutionStatus,
    DecisionStatus,
    DecisionPolicy,
)
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.context.context_manager import ContextManager
from app.services.amip.planner.execution_planner import ExecutionPlanner
from app.services.amip.supervisor.amip_supervisor import AMIPSupervisor
from app.services.amip.explainability.explainability_engine import ExplainabilityEngine
from app.services.amip.resilience.cancellation_token import CancellationToken
from app.services.amip.monitoring_service import (
    AMIPMonitoringService,
    get_monitoring_service,
)
from app.services.amip.observability import ExecutionSnapshot
from app.services.amip.utils.generators import generate_trace_id, generate_workflow_id
from app.services.amip.utils.time_utils import current_utc_timestamp
from app.schemas.amip_workflow import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowCancelResponse,
    WorkflowAuditBundleResponse,
)


class AMIPWorkflowGateway:
    """
    Central operational gateway and execution facade for the AMIP multi-agent platform.
    Coordinates workflow lifecycle, cooperative cancellation, and comprehensive audit aggregation.
    """

    def __init__(
        self,
        supervisor: Optional[AMIPSupervisor] = None,
        context_manager: Optional[ContextManager] = None,
        planner: Optional[ExecutionPlanner] = None,
        explainability: Optional[ExplainabilityEngine] = None,
        monitoring_service: Optional[AMIPMonitoringService] = None,
    ):
        self.context_manager = context_manager or ContextManager()
        self.planner = planner or ExecutionPlanner()
        self.supervisor = supervisor or AMIPSupervisor(
            context_manager=self.context_manager,
            planner=self.planner,
        )
        self.explainability = explainability or ExplainabilityEngine()
        self.monitoring_service = monitoring_service or get_monitoring_service()
        self._active_tokens: Dict[str, CancellationToken] = {}
        self._lock: threading.RLock = threading.RLock()

    @staticmethod
    def _synthesize_tasks_for_type(task_type: TaskType) -> List[ExecutionTask]:
        """Synthesizes appropriate execution tasks and dependencies for a given task type."""
        if task_type == TaskType.DOCUMENT_IMPORT:
            return [
                ExecutionTask(task_id="t1_parse", task_name="Parse OCR & Structure", task_type=task_type, required_agents=["DocIntelAgent"]),
                ExecutionTask(task_id="t2_label", task_name="Adaptive Learning & Labeling", task_type=task_type, dependencies=["t1_parse"], required_agents=["LearningAgent"]),
                ExecutionTask(task_id="t3_validate", task_name="Cross-Field Validation", task_type=task_type, dependencies=["t2_label"], required_agents=["ValidationAgent"]),
            ]
        elif task_type == TaskType.VALIDATION_ENGINE:
            return [
                ExecutionTask(task_id="t1_validate", task_name="Formula & Amount Validation", task_type=task_type, required_agents=["ValidationAgent"]),
                ExecutionTask(task_id="t2_graph", task_name="Graph Entity Consistency Check", task_type=task_type, dependencies=["t1_validate"], required_agents=["GraphAgent"]),
            ]
        elif task_type == TaskType.REVIEW_CORRECTION:
            return [
                ExecutionTask(task_id="t1_learn", task_name="Extract Correction Patterns", task_type=task_type, required_agents=["LearningAgent"]),
                ExecutionTask(task_id="t2_verify", task_name="Verify Correction Validity", task_type=task_type, dependencies=["t1_learn"], required_agents=["ValidationAgent"]),
            ]
        elif task_type == TaskType.COPILOT_CHAT:
            return [
                ExecutionTask(task_id="t1_copilot", task_name="Copilot Advisory Query", task_type=task_type, required_agents=["CopilotAgent"]),
            ]
        elif task_type == TaskType.PREDICTIVE_FORECAST:
            return [
                ExecutionTask(task_id="t1_predict", task_name="Predictive Risk Forecasting", task_type=task_type, required_agents=["PredictiveAgent"]),
            ]
        elif task_type == TaskType.GRAPH_QUERY:
            return [
                ExecutionTask(task_id="t1_graph", task_name="Knowledge Graph Topology Query", task_type=task_type, required_agents=["GraphAgent"]),
            ]
        else:  # GENERAL_QUERY
            return [
                ExecutionTask(task_id="t1_intel", task_name="Intelligence Extraction", task_type=task_type, required_agents=["DocIntelAgent"]),
                ExecutionTask(task_id="t2_validate", task_name="Consensus Verification", task_type=task_type, dependencies=["t1_intel"], required_agents=["ValidationAgent"]),
            ]

    def execute_workflow(
        self,
        request: WorkflowExecutionRequest,
        user_id: str = "system",
        user_role: str = "EMPLOYEE",
        session_id: str = "default_session",
    ) -> WorkflowExecutionResponse:
        """
        Triggers and orchestrates an autonomous multi-agent workflow end-to-end.
        """
        # 1. Parse Enums safely
        task_type_str = (request.task_type or "GENERAL_QUERY").upper()
        try:
            task_type = TaskType(task_type_str)
        except Exception:
            task_type = TaskType.GENERAL_QUERY

        priority_str = (request.priority or "NORMAL").upper()
        try:
            priority = Priority(priority_str)
        except Exception:
            priority = Priority.NORMAL

        exec_mode_str = (request.execution_mode or "SYNCHRONOUS").upper()
        try:
            exec_mode = ExecutionMode(exec_mode_str)
        except Exception:
            exec_mode = ExecutionMode.SYNCHRONOUS

        # 2. Generate Identifiers & Register Root Span
        workflow_id = generate_workflow_id()
        trace_id = generate_trace_id()
        started_at = current_utc_timestamp()

        self.monitoring_service.record_trace_span(
            span_id=f"span-root-{workflow_id}",
            name=f"WorkflowExecution_{task_type.value}",
            trace_id=trace_id,
            metadata={"summary": request.summary, "task_type": task_type.value},
        )

        self.monitoring_service.record_log(
            level="INFO",
            message=f"Initializing autonomous AMIP workflow for task '{task_type.value}'",
            trace_id=trace_id,
            workflow_id=workflow_id,
            task_id="t_init",
            agent_name="AMIPWorkflowGateway",
        )

        # 3. Create Execution Context & Cancellation Token
        cancel_token = CancellationToken()
        with self._lock:
            self._active_tokens[workflow_id] = cancel_token

        context = self.context_manager.create_context(
            task_type=task_type,
            user_id=user_id,
            user_role=user_role,
            session_id=session_id,
            priority=priority,
            execution_mode=exec_mode,
            workflow_id=workflow_id,
            trace_id=trace_id,
        )

        # Prepopulate blackboard with input payload
        blackboard = self.context_manager.get_blackboard(context.request_id)
        if request.input_payload:
            for k, v in request.input_payload.items():
                blackboard.put(str(k), v)

        # 4. Synthesize Tasks & Generate Execution Plan
        tasks = self._synthesize_tasks_for_type(task_type)
        plan = self.planner.create_plan(
            request_summary=request.summary,
            tasks=tasks,
            workflow_id=workflow_id,
            execution_mode=exec_mode,
            priority=priority,
        )

        # Record Initial Snapshot
        self.monitoring_service.record_snapshot(
            ExecutionSnapshot.capture(
                workflow_id=workflow_id,
                current_task=plan.tasks[0].task_id if plan.tasks else "t_init",
                completed_tasks=[],
                pending_tasks=[t.task_id for t in plan.tasks],
                agent_states={"AMIPWorkflowGateway": "RUNNING"},
            )
        )

        try:
            # 5. Orchestrate via AMIPSupervisor
            decision_result, updated_context = self.supervisor.orchestrate(
                context=context,
                plan=plan,
                task_type=task_type,
                user_id=user_id,
                user_role=user_role,
                session_id=session_id,
                timeout_ms=request.timeout_ms,
            )

            # Check if cancellation was triggered
            if cancel_token.is_cancelled():
                updated_context.update_stage("WORKFLOW_CANCELLED", ExecutionStatus.CANCELLED)
                decision_result.status = DecisionStatus.REJECTED
                decision_result.reason = f"Workflow was cancelled: {cancel_token.cancellation_reason or 'Requested by operator'}"
                decision_result.recommended_action = "ABORT_EXECUTION"

            # 6. Generate Narrative Explainability Report
            explanation_rep = self.explainability.generate_report(
                context=updated_context,
                plan=plan,
                state=self.supervisor.get_state(),
                decision=decision_result,
            )

            completed_at = current_utc_timestamp()
            duration_ms = explanation_rep.execution_duration_ms

            # 7. Record Metrics & Final Snapshot
            success = decision_result.status in (DecisionStatus.COMPLETED, DecisionStatus.REVIEW_REQUIRED)
            self.monitoring_service.metrics.record_workflow_execution(
                workflow_id=workflow_id,
                duration_ms=duration_ms,
                success=success,
                retries=0,
            )

            supporting = decision_result.evidence.supporting_agents if decision_result.evidence else []
            conflicting = decision_result.evidence.conflicting_agents if decision_result.evidence else []
            breakdown = decision_result.evidence.confidence_breakdown if decision_result.evidence else {}

            agent_states = {name: "COMPLETED" for name in supporting}
            for c in conflicting:
                agent_states[c] = "CONFLICT"

            self.monitoring_service.record_snapshot(
                ExecutionSnapshot.capture(
                    workflow_id=workflow_id,
                    current_task="t_completed",
                    completed_tasks=[t.task_id for t in plan.tasks],
                    pending_tasks=[],
                    agent_states=agent_states,
                    runtime_metrics={"duration_ms": duration_ms, "trace_id": trace_id},
                )
            )

            self.monitoring_service.record_log(
                level="INFO" if success else "WARNING",
                message=f"Autonomous workflow '{workflow_id}' completed with status '{decision_result.status.value}'",
                trace_id=trace_id,
                workflow_id=workflow_id,
                task_id="t_completed",
                agent_name="AMIPWorkflowGateway",
                execution_time_ms=duration_ms,
                status=decision_result.status.value,
                metadata={"confidence": decision_result.confidence, "policy": decision_result.policy.value},
            )

            return WorkflowExecutionResponse(
                workflow_id=workflow_id,
                trace_id=trace_id,
                status=decision_result.status.value,
                confidence=decision_result.confidence,
                recommended_action=decision_result.recommended_action,
                reason=decision_result.reason,
                summary=decision_result.summary,
                policy=decision_result.policy.value,
                execution_duration_ms=duration_ms,
                supporting_agents=supporting,
                conflicting_agents=conflicting,
                confidence_breakdown=breakdown,
                started_at=started_at,
                completed_at=completed_at,
            )

        finally:
            with self._lock:
                self._active_tokens.pop(workflow_id, None)

    def cancel_workflow(self, workflow_id: str, user_id: str = "system") -> WorkflowCancelResponse:
        """
        Cooperatively requests cancellation of an active autonomous workflow.
        """
        cancelled_at = current_utc_timestamp()
        with self._lock:
            token = self._active_tokens.get(workflow_id)

        if token:
            token.cancel(reason=f"Cancellation requested by operator '{user_id}'")
            self.monitoring_service.record_log(
                level="WARNING",
                message=f"Cancellation signal dispatched to active workflow '{workflow_id}' by '{user_id}'",
                workflow_id=workflow_id,
                agent_name="AMIPWorkflowGateway",
            )
            return WorkflowCancelResponse(
                workflow_id=workflow_id,
                status="CANCELLING",
                message=f"Cooperative cancellation signal dispatched to workflow '{workflow_id}'",
                cancelled_at=cancelled_at,
            )

        # Check if already completed or unknown
        snapshot = self.monitoring_service.get_execution_snapshot(workflow_id)
        if snapshot:
            return WorkflowCancelResponse(
                workflow_id=workflow_id,
                status="ALREADY_TERMINATED",
                message=f"Workflow '{workflow_id}' has already completed or terminated",
                cancelled_at=cancelled_at,
            )

        return WorkflowCancelResponse(
            workflow_id=workflow_id,
            status="NOT_FOUND",
            message=f"Workflow '{workflow_id}' not found or already purged",
            cancelled_at=cancelled_at,
        )

    def get_workflow_audit_bundle(self, workflow_id: str) -> Optional[WorkflowAuditBundleResponse]:
        """
        Synthesizes a complete execution audit bundle for a workflow.
        """
        snapshot = self.monitoring_service.get_execution_snapshot(workflow_id)
        if not snapshot:
            return None

        # Resolve trace_id from snapshot, context, or logs
        trace_id = snapshot.get("trace_id") or snapshot.get("runtime_metrics", {}).get("trace_id", "")
        if not trace_id:
            ctx = self.context_manager.get_context(workflow_id)
            if ctx and ctx.trace_id:
                trace_id = ctx.trace_id

        logs = self.monitoring_service.get_workflow_logs(workflow_id=workflow_id)
        if not trace_id and logs:
            trace_id = logs[0].get("trace_id", "")

        trace_info = self.monitoring_service.get_trace_info(trace_id) if trace_id else None
        spans = trace_info.get("spans", []) if trace_info else []

        # Reconstruct timeline events
        timeline_events = []
        for l in logs:
            timeline_events.append({
                "timestamp": l.get("timestamp", ""),
                "agent_name": l.get("agent_name", ""),
                "level": l.get("level", ""),
                "message": l.get("message", ""),
                "status": l.get("status", ""),
            })

        decision_result = {
            "workflow_id": workflow_id,
            "status": snapshot.get("status", "COMPLETED"),
            "duration_ms": snapshot.get("duration_ms", 0.0),
            "completed_tasks": snapshot.get("completed_tasks", []),
            "agent_states": snapshot.get("agent_states", {}),
            "retry_counts": snapshot.get("retry_counts", {}),
        }

        explanation_report = {
            "narrative": f"Autonomous execution completed with {len(snapshot.get('completed_tasks', []))} tasks.",
            "agent_states": snapshot.get("agent_states", {}),
            "timeline_records_count": snapshot.get("timeline_records_count", 0),
        }

        return WorkflowAuditBundleResponse(
            workflow_id=workflow_id,
            trace_id=trace_id or "",
            status=snapshot.get("status", "COMPLETED"),
            decision_result=decision_result,
            explanation_report=explanation_report,
            timeline_events=timeline_events,
            spans=spans,
            logs=logs,
            runtime_metrics=snapshot.get("runtime_metrics", {}),
            generated_at=current_utc_timestamp(),
        )


# Global singleton instance
_gateway_instance: Optional[AMIPWorkflowGateway] = None
_gateway_lock = threading.RLock()


def get_workflow_gateway() -> AMIPWorkflowGateway:
    """Returns the shared AMIPWorkflowGateway singleton instance."""
    global _gateway_instance
    with _gateway_lock:
        if _gateway_instance is None:
            _gateway_instance = AMIPWorkflowGateway()
        return _gateway_instance
