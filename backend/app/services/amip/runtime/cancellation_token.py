"""
AMIP Workflow Cancellation Token.
Thread-safe cancellation token signaling cooperative workflow termination.
"""
from __future__ import annotations
import threading
from typing import Optional
from app.services.amip.exceptions import WorkflowCancelled


class WorkflowCancellationToken:
    """
    Cooperative cancellation signal token for in-flight AMIP workflows.
    """

    def __init__(self, workflow_id: str = ""):
        self.workflow_id = workflow_id
        self._is_cancelled: bool = False
        self._cancel_reason: str = ""
        self._lock: threading.RLock = threading.RLock()

    def cancel(self, reason: str = "User cancellation request") -> None:
        """Signals cancellation on the token (thread-safe)."""
        with self._lock:
            self._is_cancelled = True
            self._cancel_reason = reason

    def is_cancelled(self) -> bool:
        """Returns True if token has been cancelled (thread-safe)."""
        with self._lock:
            return self._is_cancelled

    def reason(self) -> str:
        """Returns cancellation reason string (thread-safe)."""
        with self._lock:
            return self._cancel_reason

    def throwIfCancelled(self) -> None:
        """Raises WorkflowCancelled exception if token has been cancelled."""
        if self.is_cancelled():
            raise WorkflowCancelled(self.workflow_id, self.reason())
