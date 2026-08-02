"""
AMIP Observability Abstract Interfaces.
Defines contracts for StructuredLogger, TraceManager, MetricsCollector, PerformanceProfiler, and DiagnosticsEngine.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IStructuredLogger(ABC):
    """Abstract interface contract for AMIP StructuredLogger."""

    @abstractmethod
    def log(
        self,
        level: str,
        message: str,
        trace_id: str = "",
        workflow_id: str = "",
        task_id: str = "",
        agent_name: str = "",
        execution_time_ms: float = 0.0,
        status: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        pass


class ITraceManager(ABC):
    """Abstract interface contract for AMIP TraceManager."""

    @abstractmethod
    def generate_trace_id(self) -> str:
        pass

    @abstractmethod
    def generate_correlation_id(self) -> str:
        pass

    @abstractmethod
    def generate_workflow_id(self) -> str:
        pass


class IMetricsCollector(ABC):
    """Abstract interface contract for AMIP MetricsCollector."""

    @abstractmethod
    def record_workflow_execution(self, workflow_id: str, duration_ms: float, success: bool, retries: int = 0) -> None:
        pass

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        pass


class IPerformanceProfiler(ABC):
    """Abstract interface contract for AMIP PerformanceProfiler."""

    @abstractmethod
    def profile_start(self, name: str) -> None:
        pass

    @abstractmethod
    def profile_end(self, name: str) -> float:
        pass

    @abstractmethod
    def get_latency_report(self) -> Dict[str, Any]:
        pass


class IDiagnosticsEngine(ABC):
    """Abstract interface contract for AMIP DiagnosticsEngine."""

    @abstractmethod
    def generate_platform_health_report(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_performance_report(self) -> Dict[str, Any]:
        pass
