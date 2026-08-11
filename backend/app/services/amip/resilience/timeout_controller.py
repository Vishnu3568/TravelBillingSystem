"""
Timeout controller managing execution deadline enforcement and timeout tracking.
"""
from __future__ import annotations
import time
from contextlib import contextmanager
from typing import Optional, Generator
from app.services.amip.exceptions import TimeoutException


class TimeoutController:
    """Manages execution timeouts and provides context manager tracking."""

    def __init__(self, timeout_ms: float = 5000.0):
        self.timeout_ms = float(timeout_ms)
        self._start_time: Optional[float] = None
        self._timed_out: bool = False

    def start(self) -> None:
        """Starts timing."""
        self._start_time = time.perf_counter()
        self._timed_out = False

    def is_timed_out(self) -> bool:
        """Checks if elapsed time exceeds configured timeout."""
        if self._timed_out:
            return True
        if self._start_time is None:
            return False
        elapsed_ms = (time.perf_counter() - self._start_time) * 1000.0
        if elapsed_ms > self.timeout_ms:
            self._timed_out = True
            return True
        return False

    @contextmanager
    def track_timeout(self) -> Generator[None, None, None]:
        """Context manager enforcing execution deadline."""
        self.start()
        try:
            yield
            if self.is_timed_out():
                raise TimeoutException("TimeoutController", self.timeout_ms)
        finally:
            pass


TimeoutManager = TimeoutController
