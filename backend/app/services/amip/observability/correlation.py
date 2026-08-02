"""
AMIP Correlation Context.
Thread-local storage propagating trace_id, workflow_id, request_id, and span_id across execution threads.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional


class CorrelationContext:
    """
    Thread-local storage for managing execution correlation metadata.
    """
    _thread_local = threading.local()

    @classmethod
    def set_context(
        cls,
        trace_id: str = "",
        workflow_id: str = "",
        request_id: str = "",
        span_id: str = "",
    ) -> None:
        """Sets thread-local correlation metadata."""
        cls._thread_local.trace_id = trace_id
        cls._thread_local.workflow_id = workflow_id
        cls._thread_local.request_id = request_id
        cls._thread_local.span_id = span_id

    @classmethod
    def get_context(cls) -> Dict[str, str]:
        """Gets thread-local correlation metadata dict."""
        return {
            "trace_id": getattr(cls._thread_local, "trace_id", ""),
            "workflow_id": getattr(cls._thread_local, "workflow_id", ""),
            "request_id": getattr(cls._thread_local, "request_id", ""),
            "span_id": getattr(cls._thread_local, "span_id", ""),
        }

    @classmethod
    def clear_context(cls) -> None:
        """Clears thread-local correlation metadata."""
        cls._thread_local.trace_id = ""
        cls._thread_local.workflow_id = ""
        cls._thread_local.request_id = ""
        cls._thread_local.span_id = ""

    @classmethod
    def bind_context(cls, execution_context: Any) -> None:
        """Binds trace_id, workflow_id, and request_id from ExecutionContext onto thread-local context."""
        if execution_context:
            trace_id = getattr(execution_context, "trace_id", "")
            workflow_id = getattr(execution_context, "workflow_id", "")
            request_id = getattr(execution_context, "request_id", "")
            cls.set_context(trace_id=trace_id, workflow_id=workflow_id, request_id=request_id)
