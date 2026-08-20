"""
AMIP Monitoring Service.
Thread-safe operational control and telemetry aggregation service providing health, metrics,
trace hierarchies, execution snapshots, and diagnostics to the API layer.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, List, Optional
from app.services.amip.observability import (
    MetricsCollector,
    TraceManager,
    StructuredLogger,
    PerformanceProfiler,
    DiagnosticsEngine,
    ExecutionSnapshot,
)
from app.services.amip.utils.time_utils import current_utc_timestamp

_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "secret",
    "api_key",
    "authorization",
    "auth",
    "credential",
    "credentials",
    "raw_content",
    "raw_text",
}


def _sanitize_value(val: Any) -> Any:
    """Recursively strips sensitive keys from dictionaries/lists."""
    if isinstance(val, dict):
        sanitized = {}
        for k, v in val.items():
            if k.lower() in _SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = _sanitize_value(v)
        return sanitized
    elif isinstance(val, list):
        return [_sanitize_value(item) for item in val]
    return val


class AMIPMonitoringService:
    """
    Central thread-safe AMIP platform operational monitoring service.
    Aggregates metrics, trace hierarchy, structured logs, and execution snapshots.
    """

    def __init__(
        self,
        metrics: Optional[MetricsCollector] = None,
        trace_manager: Optional[TraceManager] = None,
        logger: Optional[StructuredLogger] = None,
        profiler: Optional[PerformanceProfiler] = None,
        diagnostics: Optional[DiagnosticsEngine] = None,
    ):
        self.metrics = metrics or MetricsCollector()
        self.trace_manager = trace_manager or TraceManager()
        self.logger = logger or StructuredLogger()
        self.profiler = profiler or PerformanceProfiler()
        self.diagnostics = diagnostics or DiagnosticsEngine(
            logger=self.logger, metrics=self.metrics, profiler=self.profiler
        )
        self._snapshots: Dict[str, ExecutionSnapshot] = {}
        self._lock: threading.RLock = threading.RLock()

    def get_platform_health(self) -> Dict[str, Any]:
        """
        Returns platform health summary including active/completed/failed counts,
        success rate, and subsystem statuses (thread-safe).
        """
        with self._lock:
            metrics_summary = self.metrics.get_summary()
            succ_rate = metrics_summary.get("success_rate", 100.0)

            overall_status = "HEALTHY" if succ_rate >= 90.0 else "DEGRADED" if succ_rate >= 70.0 else "UNHEALTHY"

            subsystem_health = {
                "metrics_collector": "HEALTHY",
                "structured_logger": "HEALTHY",
                "trace_manager": "HEALTHY",
                "diagnostics_engine": "HEALTHY",
                "performance_profiler": "HEALTHY",
            }

            return {
                "overall_status": overall_status,
                "generated_at": current_utc_timestamp(),
                "active_workflows": metrics_summary.get("active_workflows", 0),
                "completed_workflows": metrics_summary.get("completed_workflows", 0),
                "failed_workflows": metrics_summary.get("failed_workflows", 0),
                "success_rate": succ_rate,
                "average_workflow_duration_ms": metrics_summary.get("average_workflow_duration_ms", 0.0),
                "total_retries": metrics_summary.get("total_retries", 0),
                "subsystem_health": subsystem_health,
            }

    def get_runtime_metrics(self) -> Dict[str, Any]:
        """
        Returns structured telemetry metrics calculated by MetricsCollector (thread-safe).
        """
        with self._lock:
            summary = self.metrics.get_summary()
            summary["agent_statistics"] = None
            return summary

    def record_snapshot(self, snapshot: ExecutionSnapshot) -> None:
        """
        Stores an execution snapshot in memory (thread-safe).
        """
        with self._lock:
            self._snapshots[snapshot.workflow_id] = snapshot

    def get_execution_snapshots(self) -> List[Dict[str, Any]]:
        """
        Returns sanitized dictionaries of all known workflow execution snapshots (thread-safe).
        """
        with self._lock:
            results = []
            for snp in self._snapshots.values():
                sn_dict = snp.to_dict()
                results.append(_sanitize_value(sn_dict))
            return results

    def get_execution_snapshot(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns sanitized snapshot dictionary for a specific workflow_id, or None if not found (thread-safe).
        """
        with self._lock:
            snp = self._snapshots.get(workflow_id)
            if not snp:
                return None
            return _sanitize_value(snp.to_dict())

    def get_workflow_logs(
        self,
        workflow_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries structured log records matching filters (thread-safe).
        """
        with self._lock:
            logs = self.logger.get_logs(trace_id=trace_id, workflow_id=workflow_id, level=level)
            return [_sanitize_value(l.to_dict()) for l in logs]

    def get_trace_info(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns span hierarchy for trace_id, or None if no spans registered for trace (thread-safe).
        """
        with self._lock:
            spans = self.trace_manager.get_span_hierarchy(trace_id)
            if not spans:
                return None
            sanitized_spans = [_sanitize_value(s) for s in spans]
            return {
                "trace_id": trace_id,
                "spans": sanitized_spans,
                "total_spans": len(sanitized_spans),
            }

    def get_diagnostics_report(self) -> Dict[str, Any]:
        """
        Returns synthesized diagnostics report containing health, runtime logs, and performance profiles (thread-safe).
        """
        with self._lock:
            health_rep = self.diagnostics.generate_platform_health_report()
            runtime_rep = self.diagnostics.generate_runtime_report()
            perf_rep = self.diagnostics.generate_performance_report()

            return {
                "health_report": _sanitize_value(health_rep),
                "runtime_report": _sanitize_value(runtime_rep),
                "performance_report": _sanitize_value(perf_rep),
                "generated_at": current_utc_timestamp(),
            }

    def reset(self) -> None:
        """
        Resets monitoring state for testing purposes (thread-safe).
        """
        with self._lock:
            self._snapshots.clear()
            self.logger.clear_logs()
            self.metrics = MetricsCollector()
            self.trace_manager = TraceManager()
            self.profiler = PerformanceProfiler()
            self.diagnostics = DiagnosticsEngine(
                logger=self.logger, metrics=self.metrics, profiler=self.profiler
            )


# Global singleton instance
_monitoring_service_instance: Optional[AMIPMonitoringService] = None
_service_lock = threading.RLock()


def get_monitoring_service() -> AMIPMonitoringService:
    """Returns the shared AMIPMonitoringService singleton instance."""
    global _monitoring_service_instance
    with _service_lock:
        if _monitoring_service_instance is None:
            _monitoring_service_instance = AMIPMonitoringService()
        return _monitoring_service_instance
