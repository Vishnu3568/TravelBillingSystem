"""
AMIP Trace Manager.
Generates unique trace, correlation, workflow, and execution IDs, maintaining span hierarchies.
"""
from __future__ import annotations
import uuid
import threading
from typing import Dict, Any, Optional, List
from app.services.amip.interfaces.observability_interfaces import ITraceManager


class TraceManager(ITraceManager):
    """
    Generates telemetry IDs and tracks parent-child span hierarchies in memory.
    """

    def __init__(self):
        self._spans: Dict[str, Dict[str, Any]] = {}
        self._lock: threading.RLock = threading.RLock()

    def generate_trace_id(self) -> str:
        """Generates a unique trace ID."""
        return f"trc-{uuid.uuid4().hex[:16]}"

    def generate_correlation_id(self) -> str:
        """Generates a unique correlation ID."""
        return f"cor-{uuid.uuid4().hex[:16]}"

    def generate_workflow_id(self) -> str:
        """Generates a unique workflow ID."""
        return f"wfk-{uuid.uuid4().hex[:12]}"

    def generate_execution_id(self) -> str:
        """Generates a unique execution ID."""
        return f"exe-{uuid.uuid4().hex[:12]}"

    def register_span(
        self,
        span_id: str,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registers a telemetry span and tracks parent-child hierarchy (thread-safe)."""
        with self._lock:
            span_data = {
                "span_id": span_id,
                "name": name,
                "trace_id": trace_id,
                "parent_span_id": parent_span_id,
                "metadata": metadata or {},
            }
            self._spans[span_id] = span_data
            return span_data

    def get_span_hierarchy(self, trace_id: str) -> List[Dict[str, Any]]:
        """Returns all spans belonging to a trace ID (thread-safe)."""
        with self._lock:
            return [s for s in self._spans.values() if s.get("trace_id") == trace_id]
