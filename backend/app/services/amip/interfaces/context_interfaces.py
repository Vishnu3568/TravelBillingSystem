"""
AMIP Context Abstract Interfaces.
Defines contracts for ExecutionContext, Blackboard, and ContextManager components.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.services.amip.models.enums import ExecutionStatus, TaskType, Priority, ExecutionMode


class IExecutionContext(ABC):
    """Abstract interface contract for ExecutionContext."""

    @property
    @abstractmethod
    def request_id(self) -> str:
        pass

    @property
    @abstractmethod
    def trace_id(self) -> str:
        pass

    @property
    @abstractmethod
    def overall_status(self) -> ExecutionStatus:
        pass

    @abstractmethod
    def update_stage(self, stage_name: str, status: Optional[ExecutionStatus] = None) -> None:
        pass

    @abstractmethod
    def to_dict(self, include_raw_bytes: bool = False) -> Dict[str, Any]:
        pass


class IBlackboard(ABC):
    """Abstract interface contract for thread-safe ExecutionBlackboard."""

    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        pass

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        pass


class IContextManager(ABC):
    """Abstract interface contract for ContextManager."""

    @abstractmethod
    def create_context(
        self,
        task_type: TaskType = TaskType.GENERAL_QUERY,
        user_id: str = "system",
        user_role: str = "EMPLOYEE",
        session_id: str = "default_session",
        execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS,
        priority: Priority = Priority.NORMAL,
    ) -> Any:
        pass

    @abstractmethod
    def get_context(self, request_id: str) -> Any:
        pass

    @abstractmethod
    def get_blackboard(self, request_id: str) -> IBlackboard:
        pass

    @abstractmethod
    def update_context(self, context: Any) -> None:
        pass

    @abstractmethod
    def save_context(self, context: Any) -> None:
        pass

    @abstractmethod
    def destroy_context(self, request_id: str) -> bool:
        pass
