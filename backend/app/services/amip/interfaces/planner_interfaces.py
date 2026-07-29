"""
AMIP Planner Abstract Interfaces.
Defines contracts for TaskGraph, ExecutionPlan, and ExecutionPlanner components.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from app.services.amip.models.enums import PlanningStrategy, Priority, ExecutionMode


class ITaskGraph(ABC):
    """Abstract interface contract for TaskDependencyGraph."""

    @abstractmethod
    def add_node(self, task: Any) -> None:
        pass

    @abstractmethod
    def add_dependency(self, task_id: str, depends_on_task_id: str) -> None:
        pass

    @abstractmethod
    def remove_dependency(self, task_id: str, depends_on_task_id: str) -> bool:
        pass

    @abstractmethod
    def topological_sort(self) -> List[Any]:
        pass

    @abstractmethod
    def detect_cycles(self) -> bool:
        pass

    @abstractmethod
    def independent_tasks(self) -> List[Any]:
        pass


class IExecutionPlan(ABC):
    """Abstract interface contract for ExecutionPlan."""

    @abstractmethod
    def add_task(self, task: Any) -> None:
        pass

    @abstractmethod
    def remove_task(self, task_id: str) -> bool:
        pass

    @abstractmethod
    def find_task(self, task_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    def ordered_tasks(self) -> List[Any]:
        pass

    @abstractmethod
    def validate_dependencies(self) -> bool:
        pass

    @abstractmethod
    def summary(self) -> Dict[str, Any]:
        pass


class IExecutionPlanner(ABC):
    """Abstract interface contract for ExecutionPlanner."""

    @abstractmethod
    def create_plan(
        self,
        request_summary: str = "Execution Plan",
        tasks: Optional[List[Any]] = None,
        strategy: PlanningStrategy = PlanningStrategy.SEQUENTIAL,
        policy: Optional[Any] = None,
        execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS,
        priority: Priority = Priority.NORMAL,
        workflow_id: Optional[str] = None,
    ) -> Any:
        pass

    @abstractmethod
    def validate_plan(self, plan: Any) -> bool:
        pass

    @abstractmethod
    def estimate_duration(self, plan: Any) -> float:
        pass

    @abstractmethod
    def build_dependency_graph(self, plan: Any) -> ITaskGraph:
        pass
