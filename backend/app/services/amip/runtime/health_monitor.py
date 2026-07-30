"""
AMIP Health Monitor.
Thread-safe health monitoring tracking heartbeat telemetry, failure rates, and executor availability.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional
from app.services.amip.interfaces.resilience_interfaces import IHealthMonitor
from app.services.amip.utils.time_utils import current_utc_timestamp
from app.services.amip.runtime.runtime_utils import format_health_report


class HealthMonitor(IHealthMonitor):
    """
    Tracks telemetry heartbeat, availability status, failures, and recoveries across registered executors.
    """

    def __init__(self):
        self._executors: Dict[str, Dict[str, Any]] = {}
        self._lock: threading.RLock = threading.RLock()

    def record_heartbeat(self, executor_name: str) -> None:
        """Records a heartbeat ping from a specific executor (thread-safe)."""
        with self._lock:
            if executor_name not in self._executors:
                self._executors[executor_name] = {
                    "status": "HEALTHY",
                    "last_heartbeat": current_utc_timestamp(),
                    "failure_count": 0,
                    "recovery_count": 0,
                }
            else:
                self._executors[executor_name]["last_heartbeat"] = current_utc_timestamp()
                if self._executors[executor_name]["status"] == "UNHEALTHY":
                    self._executors[executor_name]["status"] = "HEALTHY"

    def record_executor_failure(self, executor_name: str) -> None:
        """Records an execution failure for an executor (thread-safe)."""
        with self._lock:
            if executor_name not in self._executors:
                self.record_heartbeat(executor_name)

            record = self._executors[executor_name]
            record["failure_count"] += 1
            if record["failure_count"] >= 3:
                record["status"] = "UNHEALTHY"

    def record_executor_recovery(self, executor_name: str) -> None:
        """Records a recovery event for an executor (thread-safe)."""
        with self._lock:
            if executor_name not in self._executors:
                self.record_heartbeat(executor_name)

            record = self._executors[executor_name]
            record["recovery_count"] += 1
            record["status"] = "HEALTHY"

    def get_executor_health(self, executor_name: str) -> Dict[str, Any]:
        """Retrieves health record dict for an executor."""
        with self._lock:
            return dict(self._executors.get(executor_name, {
                "status": "UNKNOWN",
                "last_heartbeat": "N/A",
                "failure_count": 0,
                "recovery_count": 0,
            }))

    def summary(self) -> Dict[str, Any]:
        """Generates structured health summary dictionary (thread-safe)."""
        with self._lock:
            total_exec = len(self._executors)
            healthy_cnt = sum(1 for e in self._executors.values() if e["status"] == "HEALTHY")

            if total_exec == 0:
                overall = "UNKNOWN"
            elif healthy_cnt == total_exec:
                overall = "HEALTHY"
            elif healthy_cnt > 0:
                overall = "DEGRADED"
            else:
                overall = "UNHEALTHY"

            exec_copy = {k: dict(v) for k, v in self._executors.items()}

            return {
                "overall_status": overall,
                "total_executors": total_exec,
                "healthy_count": healthy_cnt,
                "executors": exec_copy,
            }
