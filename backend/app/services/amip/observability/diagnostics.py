"""
AMIP Diagnostics Engine.
Synthesizes structured log records, trace metrics, health summaries, and latency profiles into operational reports.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional, List
from app.services.amip.interfaces.observability_interfaces import IDiagnosticsEngine
from app.services.amip.observability.execution_logger import StructuredLogger
from app.services.amip.observability.metrics_collector import MetricsCollector
from app.services.amip.observability.performance_profiler import PerformanceProfiler
from app.services.amip.utils.time_utils import current_utc_timestamp


class DiagnosticsEngine(IDiagnosticsEngine):
    """
    Central operational reporting engine synthesizing platform health, runtime, performance, and agent summaries.
    """

    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        metrics: Optional[MetricsCollector] = None,
        profiler: Optional[PerformanceProfiler] = None,
    ):
        self.logger = logger or StructuredLogger()
        self.metrics = metrics or MetricsCollector()
        self.profiler = profiler or PerformanceProfiler()
        self._lock: threading.RLock = threading.RLock()

    def generate_platform_health_report(self) -> Dict[str, Any]:
        """Generates Platform Health Report containing telemetry metrics and active status."""
        with self._lock:
            metrics_summary = self.metrics.get_summary()
            succ_rate = metrics_summary.get("success_rate", 100.0)

            status = "HEALTHY" if succ_rate >= 90.0 else "DEGRADED" if succ_rate >= 70.0 else "CRITICAL"

            return {
                "report_name": "Platform Health Report",
                "generated_at": current_utc_timestamp(),
                "overall_status": status,
                "metrics": metrics_summary,
            }

    def generate_runtime_report(self) -> Dict[str, Any]:
        """Generates Runtime Telemetry Report detailing log activity and execution counts."""
        with self._lock:
            logs = self.logger.get_logs()
            error_logs = [l.to_dict() for l in logs if l.level in ("ERROR", "CRITICAL")]

            return {
                "report_name": "Runtime Diagnostics Report",
                "generated_at": current_utc_timestamp(),
                "total_logs": len(logs),
                "error_log_count": len(error_logs),
                "recent_errors": error_logs[-5:],
            }

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generates Performance Report containing latency profiles across all components."""
        with self._lock:
            latency_data = self.profiler.get_latency_report()
            return {
                "report_name": "Performance Diagnostics Report",
                "generated_at": current_utc_timestamp(),
                "latency_profiles": latency_data,
            }

    def generate_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """Generates a detailed diagnostic summary for a specific workflow_id."""
        with self._lock:
            logs = self.logger.get_logs(workflow_id=workflow_id)
            statuses = [l.status for l in logs]
            final_status = "COMPLETED" if "COMPLETED" in statuses else "RUNNING" if "RUNNING" in statuses else "UNKNOWN"

            return {
                "workflow_id": workflow_id,
                "log_count": len(logs),
                "final_status": final_status,
                "log_trail": [l.to_dict() for l in logs],
            }

    def generate_agent_summary(self, agent_name: str) -> Dict[str, Any]:
        """Generates a performance and audit summary for a specific specialized agent."""
        with self._lock:
            all_logs = self.logger.get_logs()
            agent_logs = [l for l in all_logs if l.agent_name == agent_name]
            exec_times = [l.execution_time_ms for l in agent_logs if l.execution_time_ms > 0]

            avg_time = round(sum(exec_times) / len(exec_times), 2) if exec_times else 0.0

            return {
                "agent_name": agent_name,
                "total_invocations": len(agent_logs),
                "average_execution_time_ms": avg_time,
                "logs": [l.to_dict() for l in agent_logs],
            }
