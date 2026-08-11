"""
Supervisor service orchestrating context management, plan execution, and decision resolution.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, List, Optional, Tuple
from app.services.amip.interfaces.supervisor_interfaces import ISupervisor, IExecutionEngine
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.models.execution_plan import ExecutionPlan
from app.services.amip.models.decision_result import DecisionResult
from app.services.amip.models.decision_evidence import DecisionEvidence
from app.services.amip.models.agent_vote import AgentVote
from app.services.amip.models.enums import (
    ExecutionStatus,
    DecisionStatus,
    DecisionPolicy,
    TaskType,
    Priority,
    ExecutionMode,
)
from app.services.amip.context.context_manager import ContextManager
from app.services.amip.planner.execution_planner import ExecutionPlanner
from app.services.amip.decision.decision_matrix import DecisionMatrix
from app.services.amip.supervisor.execution_engine import ExecutionEngine
from app.services.amip.supervisor.supervisor_state import SupervisorState, SupervisorMetrics
from app.services.amip.utils.generators import generate_trace_id


class AMIPSupervisor(ISupervisor):
    """Orchestrates workflow execution across context, planning, execution, and decision matrix."""

    def __init__(
        self,
        context_manager: Optional[ContextManager] = None,
        planner: Optional[ExecutionPlanner] = None,
        engine: Optional[ExecutionEngine] = None,
    ):
        self.context_manager = context_manager or ContextManager()
        self.planner = planner or ExecutionPlanner()
        self.engine = engine or ExecutionEngine()
        self._last_state: Optional[SupervisorState] = None
        self._last_metrics: Optional[SupervisorMetrics] = None
        self._lock: threading.RLock = threading.RLock()

    def orchestrate(
        self,
        context: Optional[ExecutionContext] = None,
        plan: Optional[ExecutionPlan] = None,
        task_type: TaskType = TaskType.GENERAL_QUERY,
        user_id: str = "system",
        user_role: str = "EMPLOYEE",
        session_id: str = "default_session",
        timeout_ms: Optional[float] = None,
    ) -> Tuple[DecisionResult, ExecutionContext]:
        """Runs full orchestration workflow and returns final decision result with updated context."""
        with self._lock:
            if context is None:
                context = self.context_manager.create_context(
                    task_type=task_type,
                    user_id=user_id,
                    user_role=user_role,
                    session_id=session_id,
                )
            else:
                self.context_manager.save_context(context)

            blackboard = self.context_manager.get_blackboard(context.request_id)
            context.update_stage("ORCHESTRATION_STARTED", ExecutionStatus.RUNNING)

            if plan is None:
                plan = self.planner.create_plan(
                    request_summary=f"Orchestration workflow for task type '{task_type.value}'",
                    workflow_id=context.workflow_id,
                    execution_mode=context.execution_mode,
                    priority=context.priority,
                )

            self.planner.validate_plan(plan)
            context.update_stage("PLAN_VALIDATED")

            votes, state, metrics = self.engine.execute_plan(
                plan=plan,
                context=context,
                blackboard=blackboard,
                timeout_ms=timeout_ms,
            )

            self._last_state = state
            self._last_metrics = metrics

            matrix = DecisionMatrix(votes)
            overall_conf = matrix.calculate_confidence()
            maj_vote = matrix.majority_vote() or "APPROVED"
            conflicts = matrix.conflicts()

            if conflicts:
                policy_enum = DecisionPolicy.AUTO_REVIEW
                status_enum = DecisionStatus.REVIEW_REQUIRED
                rec_action = "FLAG_FOR_REVIEW"
                reason_str = f"Resolved with {len(conflicts)} conflicting votes. Review required."
            elif overall_conf >= 0.85:
                policy_enum = DecisionPolicy.AUTO_APPROVE
                status_enum = DecisionStatus.COMPLETED
                rec_action = "AUTO_APPROVE_WORKFLOW"
                reason_str = f"High confidence consensus reached ({overall_conf:.2f})."
            else:
                policy_enum = DecisionPolicy.MANUAL_REVIEW
                status_enum = DecisionStatus.REVIEW_REQUIRED
                rec_action = "REQUIRE_MANUAL_INTERVENTION"
                reason_str = f"Medium/low confidence score ({overall_conf:.2f})."

            evidence_dto = DecisionEvidence(
                supporting_agents=[v.agent_name for v in votes if v.vote == maj_vote],
                conflicting_agents=[v.agent_name for v in votes if v.vote != maj_vote],
                confidence_breakdown={v.agent_name: v.confidence for v in votes},
                validation_summary=blackboard.get("validation_report", {}),
                graph_summary=blackboard.get("graph_summary", {}),
                learning_summary=blackboard.get("learned_context", {}),
                predictive_summary=blackboard.get("predictive_summary", {}),
            )

            result = DecisionResult(
                trace_id=context.trace_id,
                workflow_id=context.workflow_id,
                status=status_enum,
                confidence=round(overall_conf, 4),
                reason=reason_str,
                summary=plan.request_summary,
                recommended_action=rec_action,
                policy=policy_enum,
                evidence=evidence_dto,
            )

            context.update_stage(
                "ORCHESTRATION_COMPLETED",
                ExecutionStatus.COMPLETED if status_enum == DecisionStatus.COMPLETED else ExecutionStatus.DEGRADED
            )
            self.context_manager.update_context(context)

            return result, context

    def get_state(self) -> Optional[SupervisorState]:
        """Returns current supervisor state."""
        with self._lock:
            return self._last_state

    def get_metrics(self) -> Optional[SupervisorMetrics]:
        """Returns current supervisor metrics."""
        with self._lock:
            return self._last_metrics
