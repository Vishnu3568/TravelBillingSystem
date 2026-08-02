"""
AMIP Execution Structured Logger.
Thread-safe in-memory structured telemetry logging engine without external framework dependencies.
"""
from __future__ import annotations
import threading
from typing import List, Dict, Any, Optional
from app.services.amip.interfaces.observability_interfaces import IStructuredLogger
from app.services.amip.observability.structured_log import StructuredLogRecord


class StructuredLogger(IStructuredLogger):
    """
    Thread-safe structured log collector storing structured log records in memory.
    """

    def __init__(self, max_records: int = 5000):
        self.max_records = max_records
        self._records: List[StructuredLogRecord] = []
        self._lock: threading.RLock = threading.RLock()

    def log(
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
        """Appends a structured log record to memory (thread-safe)."""
        record = StructuredLogRecord(
            message=message,
            level=level.upper(),
            trace_id=trace_id,
            workflow_id=workflow_id,
            task_id=task_id,
            agent_name=agent_name,
            execution_time_ms=execution_time_ms,
            status=status,
            metadata=metadata or {},
        )
        with self._lock:
            if len(self._records) >= self.max_records:
                self._records.pop(0)
            self._records.append(record)

    def info(self, message: str, **kwargs) -> None:
        """Logs an INFO level structured record."""
        self.log("INFO", message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Logs a DEBUG level structured record."""
        self.log("DEBUG", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Logs a WARNING level structured record."""
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Logs an ERROR level structured record."""
        self.log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Logs a CRITICAL level structured record."""
        self.log("CRITICAL", message, **kwargs)

    def get_logs(
        self,
        trace_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[StructuredLogRecord]:
        """Queries in-memory structured log records with filtering (thread-safe)."""
        with self._lock:
            results = list(self._records)
            if trace_id:
                results = [r for r in results if r.trace_id == trace_id]
            if workflow_id:
                results = [r for r in results if r.workflow_id == workflow_id]
            if level:
                results = [r for r in results if r.level == level.upper()]
            return results

    def clear_logs(self) -> None:
        """Clears all stored log records (thread-safe)."""
        with self._lock:
            self._records.clear()
