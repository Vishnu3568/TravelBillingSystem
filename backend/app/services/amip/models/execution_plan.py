"""
AMIP Execution Plan Model.
Represents a structured execution plan containing scheduled tasks, ordering, strategy, and duration estimates.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.services.amip.models.enums import Priority, ExecutionMode, PlanningStrategy
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.planning_policy import PlanningPolicy
from app.services.amip.utils.generators import generate_workflow_id
from app.services.amip.utils.time_utils import current_utc_timestamp
import uuid


def generate_plan_id() -> str:
    """Generates a unique execution plan identifier."""
    return f"pln-{uuid.uuid4().hex[:12]}"


@dataclass
class ExecutionPlan:
    """
    Complete execution plan containing scheduled tasks, dependencies, and execution policies.
    """
    plan_id: str = field(default_factory=generate_plan_id)
    workflow_id: str = field(default_factory=generate_workflow_id)
    created_at: str = field(default_factory=current_utc_timestamp)
    request_summary: str = "Unspecified Request"
    execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS
    planning_strategy: PlanningStrategy = PlanningStrategy.SEQUENTIAL
    policy: PlanningPolicy = field(default_factory=PlanningPolicy)
    tasks: List[ExecutionTask] = field(default_factory=list)
    overall_priority: Priority = Priority.NORMAL
    estimated_total_duration: float = 0.0

    def add_task(self, task: ExecutionTask) -> None:
        """Adds a task to the execution plan and recalculates estimated duration."""
        if not task:
            raise ValueError("Cannot add null task to ExecutionPlan.")
        self.tasks.append(task)
        self.recalculate_estimated_duration()

    def remove_task(self, task_id: str) -> bool:
        """Removes a task by task_id from the plan. Returns True if task was removed."""
        idx = next((i for i, t in enumerate(self.tasks) if t.task_id == task_id), None)
        if idx is not None:
            self.tasks.pop(idx)
            self.recalculate_estimated_duration()
            return True
        return False

    def find_task(self, task_id: str) -> Optional[ExecutionTask]:
        """Finds a task by task_id."""
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def ordered_tasks(self) -> List[ExecutionTask]:
        """
        Returns tasks sorted in topological dependency order.
        Uses TaskDependencyGraph to resolve ordering.
        """
        from app.services.amip.planner.dependency_graph import TaskDependencyGraph
        graph = TaskDependencyGraph(self.tasks)
        return graph.topological_sort()

    def validate_dependencies(self) -> bool:
        """
        Validates that all task dependencies exist in the plan and no cycles exist.
        Returns True if dependencies are valid, False otherwise.
        """
        from app.services.amip.planner.dependency_graph import TaskDependencyGraph
        try:
            graph = TaskDependencyGraph(self.tasks)
            if graph.detect_cycles():
                return False
            graph.topological_sort()
            return True
        except Exception:
            return False

    def recalculate_estimated_duration(self) -> float:
        """Calculates total estimated duration based on strategy and task estimates."""
        from app.services.amip.planner.planner_utils import estimate_plan_duration
        self.estimated_total_duration = estimate_plan_duration(self.tasks, self.planning_strategy)
        return self.estimated_total_duration

    def summary(self) -> Dict[str, Any]:
        """Generates a structured summary report of the execution plan."""
        return {
            "plan_id": self.plan_id,
            "workflow_id": self.workflow_id,
            "request_summary": self.request_summary,
            "planning_strategy": self.planning_strategy.value,
            "total_tasks": len(self.tasks),
            "overall_priority": self.overall_priority.value,
            "estimated_total_duration_ms": self.estimated_total_duration,
            "is_valid": self.validate_dependencies(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ExecutionPlan to a dictionary."""
        return {
            "plan_id": self.plan_id,
            "workflow_id": self.workflow_id,
            "created_at": self.created_at,
            "request_summary": self.request_summary,
            "execution_mode": self.execution_mode.value if isinstance(self.execution_mode, ExecutionMode) else str(self.execution_mode),
            "planning_strategy": self.planning_strategy.value if isinstance(self.planning_strategy, PlanningStrategy) else str(self.planning_strategy),
            "policy": self.policy.to_dict(),
            "tasks": [t.to_dict() for t in self.tasks],
            "overall_priority": self.overall_priority.value if isinstance(self.overall_priority, Priority) else str(self.overall_priority),
            "estimated_total_duration": float(self.estimated_total_duration),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionPlan:
        """Constructs ExecutionPlan from a dictionary."""
        def parse_enum(enum_cls, val, default_val):
            if isinstance(val, str):
                try:
                    return enum_cls(val)
                except ValueError:
                    return default_val
            return val or default_val

        mode_val = parse_enum(ExecutionMode, data.get("execution_mode"), ExecutionMode.SYNCHRONOUS)
        strategy_val = parse_enum(PlanningStrategy, data.get("planning_strategy"), PlanningStrategy.SEQUENTIAL)
        priority_val = parse_enum(Priority, data.get("overall_priority"), Priority.NORMAL)

        policy_data = data.get("policy", {})
        policy_obj = PlanningPolicy.from_dict(policy_data) if isinstance(policy_data, dict) else PlanningPolicy()

        task_list = data.get("tasks", [])
        tasks_obj = [ExecutionTask.from_dict(t) for t in task_list] if isinstance(task_list, list) else []

        plan = cls(
            plan_id=data.get("plan_id", generate_plan_id()),
            workflow_id=data.get("workflow_id", generate_workflow_id()),
            created_at=data.get("created_at", current_utc_timestamp()),
            request_summary=data.get("request_summary", "Unspecified Request"),
            execution_mode=mode_val,
            planning_strategy=strategy_val,
            policy=policy_obj,
            tasks=tasks_obj,
            overall_priority=priority_val,
            estimated_total_duration=float(data.get("estimated_total_duration", 0.0)),
        )
        plan.recalculate_estimated_duration()
        return plan
