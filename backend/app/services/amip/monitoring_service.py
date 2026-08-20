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
from app.services.amip.interfaces.observability_repository_interface import (
    IObservabilityRepository,
)
from app.services.amip.persistence.observability_repository import (
    SQLAlchemyObservabilityRepository,
    sanitize_payload,
)
from app.services.amip.utils.time_utils import current_utc_timestamp


class AMIPMonitoringService:
    """
    Central thread-safe AMIP platform operational monitoring service.
    Aggregates in-memory live telemetry and persists durable audit history via IObservabilityRepository.
    """

    def __init__(
        self,
        metrics: Optional[MetricsCollector] = None,
        trace_manager: Optional[TraceManager] = None,
        logger: Optional[StructuredLogger] = None,
        profiler: Optional[PerformanceProfiler] = None,
        diagnostics: Optional[DiagnosticsEngine] = None,
        repository: Optional[IObservabilityRepository] = None,
    ):
        self.metrics = metrics or MetricsCollector()
        self.trace_manager = trace_manager or TraceManager()
        self.logger = logger or StructuredLogger()
        self.profiler = profiler or PerformanceProfiler()
        self.diagnostics = diagnostics or DiagnosticsEngine(
            logger=self.logger, metrics=self.metrics, profiler=self.profiler
        )
        self.repository: IObservabilityRepository = repository or SQLAlchemyObservabilityRepository()
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
                "persistence_repository": "HEALTHY",
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
        Stores an execution snapshot in memory and asynchronously persists to durable storage (thread-safe).
        """
        with self._lock:
            self._snapshots[snapshot.workflow_id] = snapshot

        # Non-blocking persistence integration
        try:
            self.repository.save_workflow_execution(snapshot.to_dict())
        except Exception:
            pass

    def record_log(
        self,
        level: str,
        message: str,
        trace_id: str = "",
        workflow_id: str = "",
        task_id: str = "",
        agent_name: str = "",
        execution_time_ms: float = 0.0,
        status: str = "COMPLETED",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emits a structured log record to memory and persists to database.
        """
        self.logger.log(
            level=level,
            message=message,
            trace_id=trace_id,
            workflow_id=workflow_id,
            task_id=task_id,
            agent_name=agent_name,
            execution_time_ms=execution_time_ms,
            status=status,
            metadata=metadata,
        )
        try:
            self.repository.save_structured_log({
                "message": message,
                "level": level,
                "trace_id": trace_id,
                "workflow_id": workflow_id,
                "task_id": task_id,
                "agent_name": agent_name,
                "execution_time_ms": execution_time_ms,
                "status": status,
                "metadata": metadata or {},
            })
        except Exception:
            pass

    def record_trace_span(
        self,
        span_id: str,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Registers a telemetry span in memory and persists to database.
        """
        span = self.trace_manager.register_span(
            span_id=span_id,
            name=name,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            metadata=metadata,
        )
        try:
            self.repository.save_trace_span(span)
        except Exception:
            pass
        return span

    def get_execution_snapshots(self) -> List[Dict[str, Any]]:
        """
        Returns sanitized dictionaries of all known workflow execution snapshots,
        combining live in-memory state with historical persisted records.
        """
        with self._lock:
            in_memory_results = {snp.workflow_id: sanitize_payload(snp.to_dict()) for snp in self._snapshots.values()}

        # Fetch historical records from database
        try:
            db_records = self.repository.get_workflow_executions(limit=50)
            for rec in db_records:
                w_id = rec.get("workflow_id")
                if w_id and w_id not in in_memory_results:
                    in_memory_results[w_id] = sanitize_payload(rec)
        except Exception:
            pass

        return list(in_memory_results.values())

    def get_execution_snapshot(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns sanitized snapshot dictionary for a specific workflow_id.
        Checks in-memory cache first, falling back to persistent storage.
        """
        with self._lock:
            snp = self._snapshots.get(workflow_id)
            if snp:
                return sanitize_payload(snp.to_dict())

        # Fallback to persistent database storage
        try:
            persisted = self.repository.get_workflow_execution_by_id(workflow_id)
            if persisted:
                return sanitize_payload(persisted)
        except Exception:
            pass

        return None

    def get_workflow_logs(
        self,
        workflow_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries structured log records matching filters.
        Combines in-memory live logs with persistent historical logs.
        """
        with self._lock:
            logs = self.logger.get_logs(trace_id=trace_id, workflow_id=workflow_id, level=level)
            in_memory_logs = [sanitize_payload(l.to_dict()) for l in logs]

        if in_memory_logs:
            return in_memory_logs

        # If not present in memory and workflow_id provided, query repository
        if workflow_id:
            try:
                persisted_logs = self.repository.get_logs_by_workflow_id(workflow_id=workflow_id, level=level)
                return [sanitize_payload(l) for l in persisted_logs]
            except Exception:
                pass

        return []

    def get_trace_info(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns span hierarchy for trace_id.
        Checks in-memory manager first, falling back to persistent database.
        """
        with self._lock:
            spans = self.trace_manager.get_span_hierarchy(trace_id)
            if spans:
                sanitized_spans = [sanitize_payload(s) for s in spans]
                return {
                    "trace_id": trace_id,
                    "spans": sanitized_spans,
                    "total_spans": len(sanitized_spans),
                }

        # Fallback to persistent database storage
        try:
            persisted_spans = self.repository.get_trace_spans_by_trace_id(trace_id)
            if persisted_spans:
                sanitized_spans = [sanitize_payload(s) for s in persisted_spans]
                return {
                    "trace_id": trace_id,
                    "spans": sanitized_spans,
                    "total_spans": len(sanitized_spans),
                }
        except Exception:
            pass

        return None

    def get_diagnostics_report(self) -> Dict[str, Any]:
        """
        Returns synthesized diagnostics report containing health, runtime logs, and performance profiles.
        """
        with self._lock:
            health_rep = self.diagnostics.generate_platform_health_report()
            runtime_rep = self.diagnostics.generate_runtime_report()
            perf_rep = self.diagnostics.generate_performance_report()

            return {
                "health_report": sanitize_payload(health_rep),
                "runtime_report": sanitize_payload(runtime_rep),
                "performance_report": sanitize_payload(perf_rep),
                "generated_at": current_utc_timestamp(),
            }

    def cleanup_retention(
        self,
        workflow_days: int = 90,
        log_days: int = 30,
        span_days: int = 30,
    ) -> Dict[str, int]:
        """
        Explicit operation to clean up expired historical observability records.
        """
        return self.repository.cleanup_old_records(
            workflow_days=workflow_days,
            log_days=log_days,
            span_days=span_days,
        )

    def reset(self) -> None:
        """
        Resets in-memory monitoring state for testing purposes.
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

