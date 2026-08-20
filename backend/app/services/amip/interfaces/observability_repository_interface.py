"""
Abstract Interface for AMIP Observability Persistence.
Defines contract for saving and retrieving workflow executions, structured logs, trace spans, and retention cleanup.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IObservabilityRepository(ABC):
    """
    Abstract interface for persisting and querying AMIP observability state.
    """

    @abstractmethod
    def save_workflow_execution(self, execution_data: Dict[str, Any]) -> bool:
        """Persists or updates an autonomous workflow execution record."""
        pass

    @abstractmethod
    def save_structured_log(self, log_record: Dict[str, Any]) -> bool:
        """Persists a single structured telemetry log record."""
        pass

    @abstractmethod
    def save_trace_span(self, span_data: Dict[str, Any]) -> bool:
        """Persists a telemetry trace span."""
        pass

    @abstractmethod
    def get_workflow_executions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves paginated historical workflow execution records."""
        pass

    @abstractmethod
    def get_workflow_execution_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest execution state for a specific workflow_id."""
        pass

    @abstractmethod
    def get_logs_by_workflow_id(
        self,
        workflow_id: str,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieves structured log records for a specific workflow."""
        pass

    @abstractmethod
    def get_trace_spans_by_trace_id(self, trace_id: str) -> List[Dict[str, Any]]:
        """Retrieves all spans registered under a specific trace_id."""
        pass

    @abstractmethod
    def cleanup_old_records(
        self,
        workflow_days: int = 90,
        log_days: int = 30,
        span_days: int = 30,
    ) -> Dict[str, int]:
        """Cleans up expired historical observability records according to retention policy."""
        pass
