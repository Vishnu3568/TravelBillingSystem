"""
AMIP Execution Task Model.
Represents a single step or work unit within an ExecutionPlan.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from app.services.amip.models.enums import TaskType, Priority, AgentStatus
import uuid


def generate_task_id() -> str:
    """Generates a unique execution task identifier."""
    return f"tsk-{uuid.uuid4().hex[:12]}"


@dataclass
class ExecutionTask:
    """
    Represents an atomic task unit scheduled within an AMIP execution plan.
    """
    task_id: str = field(default_factory=generate_task_id)
    task_name: str = "Unassigned Task"
    task_type: TaskType = TaskType.GENERAL_QUERY
    priority: Priority = Priority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    estimated_duration_ms: float = 100.0
    required_agents: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ExecutionTask to a dictionary."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else str(self.task_type),
            "priority": self.priority.value if isinstance(self.priority, Priority) else str(self.priority),
            "dependencies": list(self.dependencies),
            "estimated_duration_ms": float(self.estimated_duration_ms),
            "required_agents": list(self.required_agents),
            "status": self.status.value if isinstance(self.status, AgentStatus) else str(self.status),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionTask:
        """Constructs an ExecutionTask instance from a dictionary."""
        def parse_enum(enum_cls, val, default_val):
            if isinstance(val, str):
                try:
                    return enum_cls(val)
                except ValueError:
                    return default_val
            return val or default_val

        task_type_val = parse_enum(TaskType, data.get("task_type"), TaskType.GENERAL_QUERY)
        priority_val = parse_enum(Priority, data.get("priority"), Priority.NORMAL)
        status_val = parse_enum(AgentStatus, data.get("status"), AgentStatus.IDLE)

        return cls(
            task_id=data.get("task_id", generate_task_id()),
            task_name=data.get("task_name", "Unassigned Task"),
            task_type=task_type_val,
            priority=priority_val,
            dependencies=list(data.get("dependencies", [])),
            estimated_duration_ms=float(data.get("estimated_duration_ms", 100.0)),
            required_agents=list(data.get("required_agents", [])),
            status=status_val,
            metadata=dict(data.get("metadata", {})),
        )
