"""
AMIP Timeout Controller.
Thread-safe deadline tracker and timeout enforcement manager for tasks and workflows.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional
from app.services.amip.interfaces.resilience_interfaces import ITimeoutController
from app.services.amip.utils.time_utils import current_utc_timestamp, calculate_duration_ms
from app.services.amip.exceptions import ExecutionTimeout


class TimeoutController(ITimeoutController):
    """
    Tracks task and workflow deadlines, computing remaining time and signaling timeouts.
    """

    def __init__(self):
        self._timers: Dict[str, Dict[str, Any]] = {}
        self._lock: threading.RLock = threading.RLock()

    def start_timer(self, entity_id: str, timeout_ms: float) -> None:
        """Starts a deadline timer for an entity (task_id or workflow_id)."""
        if not entity_id:
            raise ValueError("entity_id cannot be empty.")
        with self._lock:
            self._timers[entity_id] = {
                "start_time": current_utc_timestamp(),
                "timeout_ms": float(timeout_ms),
                "cancelled": False,
            }

    def is_timed_out(self, entity_id: str) -> bool:
        """Returns True if the entity timer has exceeded its configured timeout."""
        with self._lock:
            info = self._timers.get(entity_id)
            if not info or info["cancelled"]:
                return False
            elapsed_ms = calculate_duration_ms(info["start_time"])
            return elapsed_ms > info["timeout_ms"]

    def remaining_time_ms(self, entity_id: str) -> float:
        """Returns remaining execution time in milliseconds. Returns 0.0 if timed out."""
        with self._lock:
            info = self._timers.get(entity_id)
            if not info or info["cancelled"]:
                return 0.0
            elapsed_ms = calculate_duration_ms(info["start_time"])
            remaining = info["timeout_ms"] - elapsed_ms
            return max(0.0, round(remaining, 2))

    def check_deadline(self, entity_id: str) -> None:
        """Checks deadline and raises ExecutionTimeout if timed out."""
        if self.is_timed_out(entity_id):
            with self._lock:
                info = self._timers.get(entity_id, {})
                timeout_ms = info.get("timeout_ms", 0.0)
            raise ExecutionTimeout(entity_id, timeout_ms)

    def cancel_task(self, entity_id: str) -> bool:
        """Cancels timer tracking for an entity."""
        with self._lock:
            if entity_id in self._timers:
                self._timers[entity_id]["cancelled"] = True
                return True
            return False
