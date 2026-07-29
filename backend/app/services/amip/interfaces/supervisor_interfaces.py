"""
AMIP Supervisor Abstract Interfaces.
Defines contracts for TaskExecutor adapters, ExecutionEngine, and AMIPSupervisor components.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from app.services.amip.models.enums import AgentStatus


class ITaskExecutor(ABC):
    """Abstract interface contract for specialized agent task executors."""

    @abstractmethod
    def execute(self, task: Any, context: Any, blackboard: Any) -> Tuple[Any, Dict[str, Any]]:
        """
        Executes a task.
        Returns Tuple[AgentVote, output_artifacts_dict].
        """
        pass

    @abstractmethod
    def cancel(self, task_id: str) -> bool:
        """Cancels an in-flight task execution."""
        pass

    @abstractmethod
    def status(self, task_id: str) -> AgentStatus:
        """Retrieves status of task execution."""
        pass

    @abstractmethod
    def supports(self, task: Any) -> bool:
        """Returns True if this executor supports the given task type or agent."""
        pass


class IExecutionEngine(ABC):
    """Abstract interface contract for ExecutionEngine."""

    @abstractmethod
    def execute_plan(self, plan: Any, context: Any, blackboard: Any) -> Dict[str, Any]:
        """Executes plan tasks using registered executors."""
        pass

    @abstractmethod
    def cancel(self, workflow_id: str) -> bool:
        """Cancels plan execution."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Returns execution stats."""
        pass


class ISupervisor(ABC):
    """Abstract interface contract for AMIPSupervisor."""

    @abstractmethod
    def orchestrate(
        self,
        context: Any,
        plan: Optional[Any] = None,
    ) -> Tuple[Any, Any]:
        """
        Orchestrates full workflow lifecycle.
        Returns Tuple[DecisionResult, ExecutionContext].
        """
        pass

    @abstractmethod
    def get_state(self) -> Any:
        """Returns current supervisor state."""
        pass

    @abstractmethod
    def get_metrics(self) -> Any:
        """Returns supervisor metrics."""
        pass
