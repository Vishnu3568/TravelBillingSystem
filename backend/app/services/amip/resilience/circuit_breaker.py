"""
AMIP Circuit Breaker.
Thread-safe fault protection state machine preventing cascading failures across executing agents.
States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional
from app.services.amip.models.enums import CircuitState
from app.services.amip.interfaces.resilience_interfaces import ICircuitBreaker
from app.services.amip.utils.time_utils import current_utc_timestamp, calculate_duration_ms
from app.services.amip.exceptions import CircuitBreakerOpen


class CircuitBreaker(ICircuitBreaker):
    """
    Thread-safe Circuit Breaker guarding external dependencies and agents.
    """

    def __init__(
        self,
        circuit_name: str = "DefaultCircuit",
        failure_threshold: int = 5,
        recovery_timeout_ms: float = 10000.0,
    ):
        self.circuit_name = circuit_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_ms = recovery_timeout_ms
        self._state: CircuitState = CircuitState.CLOSED
        self._consecutive_failures: int = 0
        self._last_state_change: str = current_utc_timestamp()
        self._last_failure_time: Optional[str] = None
        self._lock: threading.RLock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        """Returns current circuit state, checking recovery timeout if OPEN."""
        with self._lock:
            if self._state == CircuitState.OPEN and self._last_failure_time:
                elapsed_ms = calculate_duration_ms(self._last_failure_time)
                if elapsed_ms >= self.recovery_timeout_ms:
                    self._state = CircuitState.HALF_OPEN
                    self._last_state_change = current_utc_timestamp()
            return self._state

    def allow_execution(self) -> bool:
        """
        Returns True if execution is allowed.
        If OPEN and recovery timeout has not elapsed, raises CircuitBreakerOpen.
        """
        with self._lock:
            current_st = self.state
            if current_st == CircuitState.OPEN:
                raise CircuitBreakerOpen(self.circuit_name, current_st.value)
            return True

    def record_success(self) -> None:
        """Records a successful execution. Resets failures and closes circuit if HALF_OPEN."""
        with self._lock:
            self._consecutive_failures = 0
            if self._state != CircuitState.CLOSED:
                self._state = CircuitState.CLOSED
                self._last_state_change = current_utc_timestamp()

    def record_failure(self, exc: Optional[Exception] = None) -> None:
        """Records an execution failure. Opens circuit if threshold reached."""
        with self._lock:
            self._consecutive_failures += 1
            self._last_failure_time = current_utc_timestamp()
            if self._consecutive_failures >= self.failure_threshold or self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._last_state_change = current_utc_timestamp()

    def reset(self) -> None:
        """Resets the circuit breaker to CLOSED state with zero failures."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._last_failure_time = None
            self._last_state_change = current_utc_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes CircuitBreaker state to dictionary (thread-safe)."""
        with self._lock:
            return {
                "circuit_name": self.circuit_name,
                "state": self.state.value,
                "consecutive_failures": self._consecutive_failures,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_ms": self.recovery_timeout_ms,
                "last_state_change": self._last_state_change,
            }
