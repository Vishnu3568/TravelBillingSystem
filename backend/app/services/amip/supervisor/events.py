"""
Lifecycle event objects emitted during supervisor plan execution.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
from app.services.amip.utils.time_utils import current_utc_timestamp


@dataclass
class BaseSupervisorEvent:
    event_type: str = "BaseSupervisorEvent"
    workflow_id: str = ""
    timestamp: str = field(default_factory=current_utc_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseSupervisorEvent:
        evt_type = data.get("event_type", "BaseSupervisorEvent")
        event_cls_map = {
            "WorkflowStarted": WorkflowStarted,
            "WorkflowCompleted": WorkflowCompleted,
            "TaskStarted": TaskStarted,
            "TaskCompleted": TaskCompleted,
            "TaskFailed": TaskFailed,
            "TaskCancelled": TaskCancelled,
        }
        target_cls = event_cls_map.get(evt_type, BaseSupervisorEvent)
        kwargs = {}
        for f in target_cls.__dataclass_fields__:
            if f in data:
                kwargs[f] = data[f]
        return target_cls(**kwargs)


@dataclass
class WorkflowStarted(BaseSupervisorEvent):
    event_type: str = "WorkflowStarted"
    total_tasks: int = 0
    request_summary: str = ""


@dataclass
class WorkflowCompleted(BaseSupervisorEvent):
    event_type: str = "WorkflowCompleted"
    status: str = "COMPLETED"
    total_duration_ms: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0


@dataclass
class TaskStarted(BaseSupervisorEvent):
    event_type: str = "TaskStarted"
    task_id: str = ""
    task_name: str = ""
    agent_name: str = ""


@dataclass
class TaskCompleted(BaseSupervisorEvent):
    event_type: str = "TaskCompleted"
    task_id: str = ""
    task_name: str = ""
    agent_name: str = ""
    duration_ms: float = 0.0
    confidence: float = 1.0
    output_summary: str = ""


@dataclass
class TaskFailed(BaseSupervisorEvent):
    event_type: str = "TaskFailed"
    task_id: str = ""
    task_name: str = ""
    agent_name: str = ""
    error_message: str = ""


@dataclass
class TaskCancelled(BaseSupervisorEvent):
    event_type: str = "TaskCancelled"
    task_id: str = ""
    task_name: str = ""
    reason: str = ""


AMIPEvent = BaseSupervisorEvent
