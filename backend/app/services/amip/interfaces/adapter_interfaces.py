"""
AMIP Adapter and AdapterRegistry Abstract Interfaces.
Defines contracts for domain service adapters and adapter resolution registries.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.execution_context import ExecutionContext


class IAdapter(ABC):
    """Abstract interface for AMIP orchestrator domain adapters."""

    @abstractmethod
    def execute(self, task: ExecutionTask, context: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Executes domain task via underlying orchestrator, returning standardized result dictionary."""
        pass

    @abstractmethod
    def get_agent_name(self) -> str:
        """Returns the registered agent name for this adapter."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Returns health status of the adapter and underlying service."""
        pass


class IAdapterRegistry(ABC):
    """Abstract interface for AMIP Adapter Registry."""

    @abstractmethod
    def register_adapter(self, key: str, adapter: IAdapter) -> None:
        """Registers an adapter under a task type or agent name key."""
        pass

    @abstractmethod
    def resolve(self, key: str) -> Optional[IAdapter]:
        """Resolves adapter by task type or agent name key."""
        pass

    @abstractmethod
    def list_adapters(self) -> Dict[str, IAdapter]:
        """Returns all registered adapters."""
        pass
