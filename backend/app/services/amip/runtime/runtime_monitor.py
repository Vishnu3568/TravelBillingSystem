"""
AMIP Runtime Monitor.
Central runtime telemetry aggregator coordinating HealthMonitor and RuntimeMetrics.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional
from app.services.amip.interfaces.resilience_interfaces import IRuntimeMonitor
from app.services.amip.runtime.health_monitor import HealthMonitor
from app.services.amip.runtime.runtime_metrics import RuntimeMetrics
from app.services.amip.runtime.runtime_utils import format_health_report, build_runtime_summary


class RuntimeMonitor(IRuntimeMonitor):
    """
    Monitors active runtime environment, combining telemetry metrics, health state, and diagnostics.
    """

    def __init__(
        self,
        health_monitor: Optional[HealthMonitor] = None,
        metrics: Optional[RuntimeMetrics] = None,
    ):
        self.health_monitor = health_monitor or HealthMonitor()
        self.metrics = metrics or RuntimeMetrics()
        self._lock: threading.RLock = threading.RLock()

    def collect_statistics(self) -> Dict[str, Any]:
        """Returns consolidated dictionary of runtime metrics and health state (thread-safe)."""
        with self._lock:
            return {
                "metrics": self.metrics.to_dict(),
                "health": self.health_monitor.summary(),
            }

    def generate_health_summary(self) -> Dict[str, Any]:
        """Generates health summary dictionary and formatted report string."""
        with self._lock:
            summary = self.health_monitor.summary()
            summary["formatted_report"] = format_health_report(summary)
            return summary

    def produce_diagnostics(self) -> Dict[str, Any]:
        """Produces runtime diagnostic summary dictionary and report text."""
        with self._lock:
            stats = self.collect_statistics()
            metrics_dict = stats["metrics"]
            summary_text = build_runtime_summary(metrics_dict)

            return {
                "diagnostics_summary": summary_text,
                "statistics": stats,
            }
