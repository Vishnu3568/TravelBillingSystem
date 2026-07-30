"""
AMIP Runtime Metrics Container.
Thread-safe metrics container collecting workflow telemetry, rates, retries, timeouts, and cancellations.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from app.services.amip.resilience.resilience_utils import calculate_success_rate, calculate_failure_rate


@dataclass
class RuntimeMetrics:
    """
    Telemetry metrics container tracking execution performance and error rates.
    """
    total_workflows: int = 0
    successful_workflows: int = 0
    failed_workflows: int = 0
    retry_count: int = 0
    timeout_count: int = 0
    cancellation_count: int = 0
    average_execution_duration_ms: float = 0.0
    success_rate: float = 100.0
    failure_rate: float = 0.0

    _durations: List[float] = field(default_factory=list, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def record_workflow(
        self,
        status: str,
        duration_ms: float,
        retries: int = 0,
        timeouts: int = 0,
        cancels: int = 0,
    ) -> None:
        """Records telemetry for a single workflow execution (thread-safe)."""
        with self._lock:
            self.total_workflows += 1
            if status == "COMPLETED" or status == "SUCCESS":
                self.successful_workflows += 1
            else:
                self.failed_workflows += 1

            self.retry_count += max(0, retries)
            self.timeout_count += max(0, timeouts)
            self.cancellation_count += max(0, cancels)

            self._durations.append(float(duration_ms))
            self.calculate_stats()

    def calculate_stats(self) -> RuntimeMetrics:
        """Computes average duration, success rate, and failure rate."""
        with self._lock:
            self.success_rate = calculate_success_rate(self.successful_workflows, self.total_workflows)
            self.failure_rate = calculate_failure_rate(self.failed_workflows, self.total_workflows)

            if self._durations:
                self.average_execution_duration_ms = round(sum(self._durations) / len(self._durations), 2)
            else:
                self.average_execution_duration_ms = 0.0

            return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes RuntimeMetrics to dictionary (thread-safe)."""
        with self._lock:
            return {
                "total_workflows": self.total_workflows,
                "successful_workflows": self.successful_workflows,
                "failed_workflows": self.failed_workflows,
                "retry_count": self.retry_count,
                "timeout_count": self.timeout_count,
                "cancellation_count": self.cancellation_count,
                "average_execution_duration_ms": self.average_execution_duration_ms,
                "success_rate": self.success_rate,
                "failure_rate": self.failure_rate,
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RuntimeMetrics:
        """Constructs RuntimeMetrics instance from dictionary."""
        return cls(
            total_workflows=int(data.get("total_workflows", 0)),
            successful_workflows=int(data.get("successful_workflows", 0)),
            failed_workflows=int(data.get("failed_workflows", 0)),
            retry_count=int(data.get("retry_count", 0)),
            timeout_count=int(data.get("timeout_count", 0)),
            cancellation_count=int(data.get("cancellation_count", 0)),
            average_execution_duration_ms=float(data.get("average_execution_duration_ms", 0.0)),
            success_rate=float(data.get("success_rate", 100.0)),
            failure_rate=float(data.get("failure_rate", 0.0)),
        )
