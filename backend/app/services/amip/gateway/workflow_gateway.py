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
from app.services.amip.runtime.idempotency_manager import (
    IdempotencyManager,
    get_idempotency_manager,
)
from app.services.amip.runtime.async_worker import (
    AsyncWorkflowWorker,
    get_async_worker,
)
from app.services.amip.runtime.recovery_service import (
    RecoveryService,
    get_recovery_service,
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
from app.schemas.amip_hitl import (
    HITLReviewItemResponse,
    HITLOverrideResponse,
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
        idempotency_manager: Optional[IdempotencyManager] = None,
        async_worker: Optional[AsyncWorkflowWorker] = None,
        recovery_service: Optional[RecoveryService] = None,
    ):
        self.context_manager = context_manager or ContextManager()
        self.planner = planner or ExecutionPlanner()
        self.supervisor = supervisor or AMIPSupervisor(
            context_manager=self.context_manager,
            planner=self.planner,
        )
        self.explainability = explainability or ExplainabilityEngine()
        self.monitoring_service = monitoring_service or get_monitoring_service()
        self.idempotency_manager = idempotency_manager or get_idempotency_manager()
        self.async_worker = async_worker or get_async_worker()
        self.recovery_service = recovery_service or get_recovery_service()
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
        Supports idempotency deduplication and asynchronous background execution.
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

        # 3. Idempotency Check
        if request.idempotency_key:
            lease_acquired, cached_entry = self.idempotency_manager.acquire_lease(
                idempotency_key=request.idempotency_key,
                workflow_id=workflow_id,
                payload=request.input_payload,
            )
            if not lease_acquired and cached_entry:
                if cached_entry.get("result"):
                    return WorkflowExecutionResponse(**cached_entry["result"])
                # In-flight duplicate execution
                return WorkflowExecutionResponse(
                    workflow_id=cached_entry.get("workflow_id", workflow_id),
                    trace_id=trace_id,
                    status="RUNNING",
                    confidence=0.0,
                    recommended_action="WAIT_FOR_COMPLETION",
                    reason="Duplicate execution already in progress for this idempotency key",
                    summary=request.summary,
                    policy="IDEMPOTENCY_DEDUPLICATED",
                    execution_duration_ms=0.0,
                    started_at=started_at,
                )

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

        # 4. Create Execution Context & Cancellation Token
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

        # 5. Synthesize Tasks & Generate Execution Plan
        tasks = self._synthesize_tasks_for_type(task_type)
        plan = self.planner.create_plan(
            request_summary=request.summary,
            tasks=tasks,
            workflow_id=workflow_id,
            execution_mode=exec_mode,
            priority=priority,
        )

        # Record Initial Snapshot & Database Checkpoint
        initial_snapshot = ExecutionSnapshot.capture(
            workflow_id=workflow_id,
            current_task=plan.tasks[0].task_id if plan.tasks else "t_init",
            completed_tasks=[],
            pending_tasks=[t.task_id for t in plan.tasks],
            agent_states={"AMIPWorkflowGateway": "RUNNING"},
            runtime_metrics={"trace_id": trace_id, "heartbeat_at": started_at, "status": "RUNNING"},
        )
        self.monitoring_service.record_snapshot(initial_snapshot)
        try:
            self.monitoring_service.repository.save_workflow_execution({
                "workflow_id": workflow_id,
                "trace_id": trace_id,
                "status": "RUNNING",
                "current_task": plan.tasks[0].task_id if plan.tasks else "t_init",
                "completed_tasks": [],
                "pending_tasks": [t.task_id for t in plan.tasks],
                "agent_states": {"AMIPWorkflowGateway": "RUNNING"},
                "duration_ms": 0.0,
                "started_at": started_at,
                "metadata": {"heartbeat_at": started_at, "idempotency_key": request.idempotency_key or ""},
            })
        except Exception:
            pass

        # 6. Branch Execution: Asynchronous vs Synchronous
        if exec_mode == ExecutionMode.ASYNCHRONOUS:
            self.async_worker.submit_workflow(
                self._run_workflow_pipeline,
                workflow_id=workflow_id,
                trace_id=trace_id,
                task_type=task_type,
                request=request,
                context=context,
                plan=plan,
                cancel_token=cancel_token,
                started_at=started_at,
                user_id=user_id,
                user_role=user_role,
                session_id=session_id,
            )
            return WorkflowExecutionResponse(
                workflow_id=workflow_id,
                trace_id=trace_id,
                status="RUNNING",
                confidence=0.0,
                recommended_action="POLL_STATUS",
                reason="Asynchronous workflow dispatched to background worker pool",
                summary=request.summary,
                policy="ASYNC_DISPATCH",
                execution_duration_ms=0.0,
                supporting_agents=[],
                conflicting_agents=[],
                confidence_breakdown={},
                started_at=started_at,
                completed_at=None,
            )

        return self._run_workflow_pipeline(
            workflow_id=workflow_id,
            trace_id=trace_id,
            task_type=task_type,
            request=request,
            context=context,
            plan=plan,
            cancel_token=cancel_token,
            started_at=started_at,
            user_id=user_id,
            user_role=user_role,
            session_id=session_id,
        )

    def _run_workflow_pipeline(
        self,
        workflow_id: str,
        trace_id: str,
        task_type: TaskType,
        request: WorkflowExecutionRequest,
        context: ExecutionContext,
        plan: Any,
        cancel_token: CancellationToken,
        started_at: str,
        user_id: str,
        user_role: str,
        session_id: str,
    ) -> WorkflowExecutionResponse:
        """
        Executes the end-to-end multi-agent orchestration pipeline with step checkpointing.
        """
        try:
            # 1. Orchestrate via AMIPSupervisor
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

            # 2. Generate Narrative Explainability Report
            explanation_rep = self.explainability.generate_report(
                context=updated_context,
                plan=plan,
                state=self.supervisor.get_state(),
                decision=decision_result,
            )

            completed_at = current_utc_timestamp()
            duration_ms = explanation_rep.execution_duration_ms

            # 3. Record Metrics & Final Snapshot
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

            final_snapshot = ExecutionSnapshot.capture(
                workflow_id=workflow_id,
                current_task="t_completed",
                completed_tasks=[t.task_id for t in plan.tasks],
                pending_tasks=[],
                agent_states=agent_states,
                runtime_metrics={
                    "duration_ms": duration_ms,
                    "trace_id": trace_id,
                    "heartbeat_at": completed_at,
                    "status": decision_result.status.value,
                },
            )
            self.monitoring_service.record_snapshot(final_snapshot)

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

            # 4. Checkpoint Final Execution in Database
            try:
                self.monitoring_service.repository.save_workflow_execution({
                    "workflow_id": workflow_id,
                    "trace_id": trace_id,
                    "status": decision_result.status.value,
                    "current_task": "t_completed",
                    "completed_tasks": [t.task_id for t in plan.tasks],
                    "pending_tasks": [],
                    "agent_states": agent_states,
                    "duration_ms": duration_ms,
                    "started_at": started_at,
                    "metadata": {
                        "heartbeat_at": completed_at,
                        "idempotency_key": request.idempotency_key or "",
                        "confidence": decision_result.confidence,
                        "policy": decision_result.policy.value,
                    },
                })
            except Exception:
                pass

            response_dto = WorkflowExecutionResponse(
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

            # 5. Record Idempotency Completion
            if request.idempotency_key:
                result_payload = response_dto.model_dump() if hasattr(response_dto, "model_dump") else response_dto.dict()
                self.idempotency_manager.record_completion(
                    idempotency_key=request.idempotency_key,
                    workflow_id=workflow_id,
                    result=result_payload,
                )

            return response_dto

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

    def get_pending_reviews(self) -> List[HITLReviewItemResponse]:
        """
        Retrieves all workflows currently in REVIEW_REQUIRED status awaiting human operator intervention.
        """
        results: Dict[str, HITLReviewItemResponse] = {}

        # 1. Check in-memory snapshots
        for snp in self.monitoring_service.get_execution_snapshots():
            if snp.get("status") == "REVIEW_REQUIRED":
                w_id = snp.get("workflow_id", "")
                if w_id:
                    results[w_id] = HITLReviewItemResponse(
                        workflow_id=w_id,
                        trace_id=snp.get("trace_id", ""),
                        task_type=snp.get("task_type", "GENERAL_QUERY"),
                        current_task=snp.get("current_task", ""),
                        status=snp.get("status", "REVIEW_REQUIRED"),
                        confidence=float(snp.get("runtime_metrics", {}).get("confidence", 0.0)),
                        reason=snp.get("runtime_metrics", {}).get("reason", "Conflicting agent votes or low confidence."),
                        duration_ms=float(snp.get("duration_ms", 0.0)),
                        completed_tasks=snp.get("completed_tasks", []),
                        pending_tasks=snp.get("pending_tasks", []),
                        agent_states=snp.get("agent_states", {}),
                        retry_counts=snp.get("retry_counts", {}),
                        created_at=snp.get("timestamp", ""),
                    )

        # 2. Check persistent repository
        try:
            db_records = self.monitoring_service.repository.get_workflow_executions(limit=50, status="REVIEW_REQUIRED")
            for rec in db_records:
                w_id = rec.get("workflow_id", "")
                if w_id and w_id not in results:
                    results[w_id] = HITLReviewItemResponse(
                        workflow_id=w_id,
                        trace_id=rec.get("trace_id", ""),
                        task_type=rec.get("task_type", "GENERAL_QUERY"),
                        current_task=rec.get("current_task", ""),
                        status=rec.get("status", "REVIEW_REQUIRED"),
                        confidence=float(rec.get("runtime_metrics", {}).get("confidence", 0.0)),
                        reason=rec.get("runtime_metrics", {}).get("reason", "Conflicting agent votes or low confidence."),
                        duration_ms=float(rec.get("duration_ms", 0.0)),
                        completed_tasks=rec.get("completed_tasks", []),
                        pending_tasks=rec.get("pending_tasks", []),
                        agent_states=rec.get("agent_states", {}),
                        retry_counts=rec.get("retry_counts", {}),
                        created_at=rec.get("started_at", ""),
                    )
        except Exception:
            pass

        return list(results.values())

    def submit_human_override(
        self,
        workflow_id: str,
        action: str,
        reason: str,
        notes: Optional[str] = None,
        operator: str = "system",
    ) -> HITLOverrideResponse:
        """
        Submits a human operator override (APPROVE, REJECT, ESCALATE) for a workflow in review.
        """
        from fastapi import HTTPException, status as http_status

        action_norm = (action or "").strip().upper()
        if action_norm not in ("APPROVE", "REJECT", "ESCALATE"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action '{action}'. Supported actions are APPROVE, REJECT, ESCALATE.",
            )

        with self._lock:
            snapshot = self.monitoring_service.get_execution_snapshot(workflow_id)
            if not snapshot:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Workflow '{workflow_id}' not found",
                )

            current_status = snapshot.get("status", "UNKNOWN")
            if current_status != "REVIEW_REQUIRED":
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot override workflow '{workflow_id}' with status '{current_status}'. Only REVIEW_REQUIRED workflows can be overridden.",
                )

            # Map new status
            status_map = {
                "APPROVE": "APPROVED",
                "REJECT": "REJECTED",
                "ESCALATE": "ESCALATED",
            }
            new_status = status_map[action_norm]
            now_ts = current_utc_timestamp()
            trace_id = snapshot.get("trace_id") or snapshot.get("runtime_metrics", {}).get("trace_id", "")

            # 1. Update in-memory snapshot if present
            with self.monitoring_service._lock:
                mem_snp = self.monitoring_service._snapshots.get(workflow_id)
                if mem_snp:
                    mem_snp.agent_states["HumanOperator"] = new_status
                    mem_snp.current_task = f"override_{action_norm.lower()}"

        # 2. Record auditable structured log
        self.monitoring_service.record_log(
            level="INFO" if action_norm == "APPROVE" else "WARNING",
            message=f"Human operator '{operator}' submitted override '{action_norm}': {reason}",
            trace_id=trace_id,
            workflow_id=workflow_id,
            task_id="hitl_override",
            agent_name="HumanOperator",
            status=new_status,
            metadata={"operator": operator, "action": action_norm, "reason": reason, "notes": notes or ""},
        )

        # 3. Persist updated execution state
        updated_exec_data = {
            "workflow_id": workflow_id,
            "execution_id": snapshot.get("execution_id") or snapshot.get("snapshot_id"),
            "trace_id": trace_id,
            "status": new_status,
            "current_task": f"override_{action_norm.lower()}",
            "completed_tasks": snapshot.get("completed_tasks", []),
            "pending_tasks": snapshot.get("pending_tasks", []),
            "agent_states": {**snapshot.get("agent_states", {}), "HumanOperator": new_status},
            "retry_counts": snapshot.get("retry_counts", {}),
            "duration_ms": snapshot.get("duration_ms", 0.0),
        }
        try:
            self.monitoring_service.repository.save_workflow_execution(updated_exec_data)
        except Exception:
            pass

        return HITLOverrideResponse(
            workflow_id=workflow_id,
            previous_status=current_status,
            new_status=new_status,
            action=action_norm,
            operator=operator,
            reason=reason,
            updated_at=now_ts,
            message=f"Workflow '{workflow_id}' successfully updated to status '{new_status}' by operator '{operator}'",
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
