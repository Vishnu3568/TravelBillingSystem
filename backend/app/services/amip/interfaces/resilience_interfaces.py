"""
AMIP Resilience and Runtime Abstract Interfaces.
Defines contracts for RetryPolicy, CircuitBreaker, TimeoutController, HealthMonitor, and RuntimeMonitor components.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple


class IRetryPolicy(ABC):
    """Abstract interface contract for RetryPolicy."""

    @abstractmethod
    def should_retry(self, attempt: int, exc: Optional[Exception] = None) -> bool:
        pass

    @abstractmethod
    def next_delay(self, attempt: int) -> float:
        pass


class ICircuitBreaker(ABC):
    """Abstract interface contract for CircuitBreaker."""

    @abstractmethod
    def record_success(self) -> None:
        pass

    @abstractmethod
    def record_failure(self, exc: Optional[Exception] = None) -> None:
        pass

    @abstractmethod
    def allow_execution(self) -> bool:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class ITimeoutController(ABC):
    """Abstract interface contract for TimeoutController."""

    @abstractmethod
    def start_timer(self, entity_id: str, timeout_ms: float) -> None:
        pass

    @abstractmethod
    def is_timed_out(self, entity_id: str) -> bool:
        pass

    @abstractmethod
    def remaining_time_ms(self, entity_id: str) -> float:
        pass


class IHealthMonitor(ABC):
    """Abstract interface contract for HealthMonitor."""

    @abstractmethod
    def record_heartbeat(self, executor_name: str) -> None:
        pass

    @abstractmethod
    def record_executor_failure(self, executor_name: str) -> None:
        pass

    @abstractmethod
    def record_executor_recovery(self, executor_name: str) -> None:
        pass

    @abstractmethod
    def summary(self) -> Dict[str, Any]:
        pass


class IRuntimeMonitor(ABC):
    """Abstract interface contract for RuntimeMonitor."""

    @abstractmethod
    def collect_statistics(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_health_summary(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def produce_diagnostics(self) -> Dict[str, Any]:
        pass
