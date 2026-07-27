"""
AMIP Execution Context Model.
Strongly typed execution context representing task state, trace metadata, evidence, and timeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from app.services.amip.models.enums import ExecutionStatus, TaskType, Priority, ExecutionMode
from app.services.amip.models.evidence_context import EvidenceContext
from app.services.amip.models.execution_timeline import ExecutionTimeline
from app.services.amip.utils.generators import generate_request_id, generate_trace_id, generate_workflow_id
from app.services.amip.utils.time_utils import current_utc_timestamp


@dataclass
class ExecutionContext:
    """
    Core strongly-typed execution context object for AMIP workflows.
    """
    request_id: str = field(default_factory=generate_request_id)
    trace_id: str = field(default_factory=generate_trace_id)
    session_id: str = "default_session"
    workflow_id: str = field(default_factory=generate_workflow_id)
    task_type: TaskType = TaskType.GENERAL_QUERY
    user_id: str = "system"
    user_role: str = "EMPLOYEE"
    request_timestamp: str = field(default_factory=current_utc_timestamp)
    current_stage: str = "INITIALIZED"
    overall_status: ExecutionStatus = ExecutionStatus.PENDING
    execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS
    priority: Priority = Priority.NORMAL
    evidence: EvidenceContext = field(default_factory=EvidenceContext)
    timeline: ExecutionTimeline = field(default_factory=ExecutionTimeline)

    def update_stage(self, stage_name: str, status: Optional[ExecutionStatus] = None) -> None:
        """Updates the current stage and optionally the overall status."""
        self.current_stage = stage_name
        if status:
            self.overall_status = status

    def to_dict(self, include_raw_bytes: bool = False) -> Dict[str, Any]:
        """Serializes the ExecutionContext into a dictionary representation."""
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else str(self.task_type),
            "user_id": self.user_id,
            "user_role": self.user_role,
            "request_timestamp": self.request_timestamp,
            "current_stage": self.current_stage,
            "overall_status": self.overall_status.value if isinstance(self.overall_status, ExecutionStatus) else str(self.overall_status),
            "execution_mode": self.execution_mode.value if isinstance(self.execution_mode, ExecutionMode) else str(self.execution_mode),
            "priority": self.priority.value if isinstance(self.priority, Priority) else str(self.priority),
            "evidence": self.evidence.to_dict(include_raw_bytes=include_raw_bytes),
            "timeline": self.timeline.to_list(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionContext:
        """Constructs an ExecutionContext instance from a dictionary."""
        def parse_enum(enum_cls, val, default_val):
            if isinstance(val, str):
                try:
                    return enum_cls(val)
                except ValueError:
                    return default_val
            return val or default_val

        task_type = parse_enum(TaskType, data.get("task_type"), TaskType.GENERAL_QUERY)
        status = parse_enum(ExecutionStatus, data.get("overall_status"), ExecutionStatus.PENDING)
        mode = parse_enum(ExecutionMode, data.get("execution_mode"), ExecutionMode.SYNCHRONOUS)
        priority = parse_enum(Priority, data.get("priority"), Priority.NORMAL)

        evidence_data = data.get("evidence", {})
        evidence_obj = EvidenceContext.from_dict(evidence_data) if isinstance(evidence_data, dict) else EvidenceContext()

        timeline_data = data.get("timeline", [])
        timeline_obj = ExecutionTimeline.from_list(timeline_data) if isinstance(timeline_data, list) else ExecutionTimeline()

        return cls(
            request_id=data.get("request_id", generate_request_id()),
            trace_id=data.get("trace_id", generate_trace_id()),
            session_id=data.get("session_id", "default_session"),
            workflow_id=data.get("workflow_id", generate_workflow_id()),
            task_type=task_type,
            user_id=data.get("user_id", "system"),
            user_role=data.get("user_role", "EMPLOYEE"),
            request_timestamp=data.get("request_timestamp", current_utc_timestamp()),
            current_stage=data.get("current_stage", "INITIALIZED"),
            overall_status=status,
            execution_mode=mode,
            priority=priority,
            evidence=evidence_obj,
            timeline=timeline_obj,
        )
