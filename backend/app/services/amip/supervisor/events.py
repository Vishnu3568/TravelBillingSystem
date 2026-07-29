"""
AMIP Supervisor Execution Events.
Defines lightweight lifecycle event objects emitted during plan execution.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
from app.services.amip.utils.time_utils import current_utc_timestamp


@dataclass
class BaseSupervisorEvent:
    """Base event class for supervisor lifecycle notifications."""
    event_type: str = "BaseSupervisorEvent"
    workflow_id: str = ""
    timestamp: str = field(default_factory=current_utc_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes event to dictionary."""
        return asdict(self)


@dataclass
class WorkflowStarted(BaseSupervisorEvent):
    """Emitted when a workflow execution plan begins processing."""
    event_type: str = "WorkflowStarted"
    total_tasks: int = 0
    request_summary: str = ""


@dataclass
class WorkflowCompleted(BaseSupervisorEvent):
    """Emitted when a workflow plan finishes execution."""
    event_type: str = "WorkflowCompleted"
    status: str = "COMPLETED"
    total_duration_ms: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0


@dataclass
class TaskStarted(BaseSupervisorEvent):
    """Emitted when an individual task starts execution."""
    event_type: str = "TaskStarted"
    task_id: str = ""
    task_name: str = ""
    agent_name: str = ""


@dataclass
class TaskCompleted(BaseSupervisorEvent):
    """Emitted when an individual task successfully completes."""
    event_type: str = "TaskCompleted"
    task_id: str = ""
    task_name: str = ""
    agent_name: str = ""
    duration_ms: float = 0.0
    confidence: float = 1.0
    output_summary: str = ""


@dataclass
class TaskFailed(BaseSupervisorEvent):
    """Emitted when an individual task execution fails."""
    event_type: str = "TaskFailed"
    task_id: str = ""
    task_name: str = ""
    agent_name: str = ""
    error_message: str = ""


@dataclass
class TaskCancelled(BaseSupervisorEvent):
    """Emitted when a task execution is cancelled."""
    event_type: str = "TaskCancelled"
    task_id: str = ""
    task_name: str = ""
    reason: str = ""
