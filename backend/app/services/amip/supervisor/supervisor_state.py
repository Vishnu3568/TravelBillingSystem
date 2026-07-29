"""
AMIP Supervisor State and Metrics Models.
Provides progress tracking and execution metrics telemetry.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from app.services.amip.models.enums import ExecutionStatus


@dataclass
class SupervisorState:
    """
    Mutable state tracker for active supervisor workflow execution.
    """
    workflow_id: str = ""
    current_task: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    running_tasks: List[str] = field(default_factory=list)
    execution_progress: float = 0.0
    overall_status: ExecutionStatus = ExecutionStatus.PENDING

    def update_progress(self, total_tasks: int) -> float:
        """Calculates and updates percentage progress (0.0 to 100.0%)."""
        if total_tasks <= 0:
            self.execution_progress = 100.0
        else:
            done_count = len(self.completed_tasks) + len(self.failed_tasks)
            self.execution_progress = min(100.0, round((done_count / total_tasks) * 100.0, 2))
        return self.execution_progress

    def to_dict(self) -> Dict[str, Any]:
        """Serializes SupervisorState to dictionary."""
        d = asdict(self)
        d["overall_status"] = self.overall_status.value if isinstance(self.overall_status, ExecutionStatus) else str(self.overall_status)
        return d


@dataclass
class SupervisorMetrics:
    """
    Execution performance metrics collected during supervisor execution.
    """
    workflow_id: str = ""
    total_execution_time_ms: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_task_duration_ms: float = 0.0
    success_rate: float = 0.0

    def calculate_metrics(self, durations: List[float], total_tasks: int) -> SupervisorMetrics:
        """Computes summary metrics from duration list and task counts."""
        self.tasks_completed = len(durations) - self.tasks_failed if self.tasks_failed <= len(durations) else 0
        if total_tasks > 0:
            self.success_rate = round((self.tasks_completed / total_tasks) * 100.0, 2)
        else:
            self.success_rate = 100.0

        if durations:
            self.average_task_duration_ms = round(sum(durations) / len(durations), 2)
        else:
            self.average_task_duration_ms = 0.0

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes metrics to dictionary."""
        return asdict(self)
