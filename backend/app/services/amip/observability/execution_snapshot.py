"""
AMIP Execution Snapshot.
Captures complete point-in-time runtime state of a workflow execution for debugging and auditing.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from app.services.amip.utils.time_utils import current_utc_timestamp


@dataclass
class ExecutionSnapshot:
    """
    Point-in-time snapshot of workflow context, timeline state, and agent metrics.
    """
    snapshot_id: str = field(default_factory=lambda: f"snp-{uuid.uuid4().hex[:12]}")
    timestamp: str = field(default_factory=current_utc_timestamp)
    workflow_id: str = ""
    current_task: str = ""
    completed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    agent_states: Dict[str, str] = field(default_factory=dict)
    timeline_records_count: int = 0
    runtime_metrics: Dict[str, Any] = field(default_factory=dict)
    memory_stats: Dict[str, Any] = field(default_factory=dict)
    retry_counts: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def capture(
        cls,
        workflow_id: str,
        current_task: str = "",
        completed_tasks: Optional[List[str]] = None,
        pending_tasks: Optional[List[str]] = None,
        agent_states: Optional[Dict[str, str]] = None,
        timeline_records_count: int = 0,
        runtime_metrics: Optional[Dict[str, Any]] = None,
        memory_stats: Optional[Dict[str, Any]] = None,
        retry_counts: Optional[Dict[str, int]] = None,
    ) -> ExecutionSnapshot:
        """Constructs an ExecutionSnapshot instance."""
        return cls(
            workflow_id=workflow_id,
            current_task=current_task,
            completed_tasks=list(completed_tasks or []),
            pending_tasks=list(pending_tasks or []),
            agent_states=dict(agent_states or {}),
            timeline_records_count=timeline_records_count,
            runtime_metrics=dict(runtime_metrics or {}),
            memory_stats=dict(memory_stats or {"active_threads": 1}),
            retry_counts=dict(retry_counts or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes snapshot to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionSnapshot:
        """Constructs ExecutionSnapshot instance from dictionary."""
        return cls(
            snapshot_id=data.get("snapshot_id", f"snp-{uuid.uuid4().hex[:12]}"),
            timestamp=data.get("timestamp", current_utc_timestamp()),
            workflow_id=data.get("workflow_id", ""),
            current_task=data.get("current_task", ""),
            completed_tasks=list(data.get("completed_tasks", [])),
            pending_tasks=list(data.get("pending_tasks", [])),
            agent_states=dict(data.get("agent_states", {})),
            timeline_records_count=int(data.get("timeline_records_count", 0)),
            runtime_metrics=dict(data.get("runtime_metrics", {})),
            memory_stats=dict(data.get("memory_stats", {})),
            retry_counts=dict(data.get("retry_counts", {})),
        )
