"""
Cancellation token supporting execution cancellation requests.
"""
from __future__ import annotations
import threading
from typing import Optional
from app.services.amip.exceptions import OperationCancelled


class CancellationToken:
    """Thread-safe token for signalling and checking cancellation status."""

    def __init__(self):
        self._cancelled: bool = False
        self._reason: str = ""
        self._lock: threading.RLock = threading.RLock()

    def cancel(self, reason: str = "Operation cancelled") -> None:
        """Signals cancellation with reason."""
        with self._lock:
            self._cancelled = True
            self._reason = reason

    def is_cancelled(self) -> bool:
        """Returns True if cancellation was requested."""
        with self._lock:
            return self._cancelled

    @property
    def cancellation_reason(self) -> str:
        """Returns cancellation reason."""
        with self._lock:
            return self._reason

    def check_cancellation(self) -> None:
        """Raises OperationCancelled if token is in cancelled state."""
        with self._lock:
            if self._cancelled:
                raise OperationCancelled("CancellationToken", self._reason)
