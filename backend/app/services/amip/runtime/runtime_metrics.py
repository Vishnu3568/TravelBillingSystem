"""
Runtime metrics container tracking execution performance, latencies, and error rates.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from app.services.amip.resilience.resilience_utils import calculate_success_rate, calculate_failure_rate


@dataclass
class RuntimeMetrics:
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
    _latencies: Dict[str, List[float]] = field(default_factory=dict, repr=False)
    _errors: Dict[str, int] = field(default_factory=dict, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def record_workflow(
        self,
        status: str,
        duration_ms: float,
        retries: int = 0,
        timeouts: int = 0,
        cancels: int = 0,
    ) -> None:
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

    def record_latency(self, component: str, latency_ms: float) -> None:
        with self._lock:
            if component not in self._latencies:
                self._latencies[component] = []
            self._latencies[component].append(float(latency_ms))

    def record_error(self, component: str) -> None:
        with self._lock:
            self._errors[component] = self._errors.get(component, 0) + 1

    def calculate_stats(self) -> RuntimeMetrics:
        with self._lock:
            self.success_rate = calculate_success_rate(self.successful_workflows, self.total_workflows)
            self.failure_rate = calculate_failure_rate(self.failed_workflows, self.total_workflows)

            if self._durations:
                self.average_execution_duration_ms = round(sum(self._durations) / len(self._durations), 2)
            else:
                self.average_execution_duration_ms = 0.0

            return self

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            latencies_summary = {}
            for comp, list_d in self._latencies.items():
                latencies_summary[comp] = {
                    "count": len(list_d),
                    "average_ms": round(sum(list_d) / len(list_d), 2) if list_d else 0.0,
                }
            res = self.to_dict()
            res["latencies"] = latencies_summary
            res["error_counts"] = dict(self._errors)
            return res

    def to_dict(self) -> Dict[str, Any]:
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


class RuntimeMonitor:
    """Monitor for observing runtime metrics."""

    def __init__(self, metrics: Optional[RuntimeMetrics] = None):
        self.metrics = metrics or RuntimeMetrics()
        self.is_running: bool = False

    def start_monitoring(self) -> None:
        self.is_running = True

    def stop_monitoring(self) -> None:
        self.is_running = False
