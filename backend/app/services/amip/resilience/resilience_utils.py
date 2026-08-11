"""
Resilience utilities for backoff delays, exception retry checks, and rate calculations.
"""
from __future__ import annotations
import math
from typing import Dict, Any


def calculate_backoff_delay(
    attempt: int,
    base_delay_ms: float = 100.0,
    strategy: str = "EXPONENTIAL",
    backoff_factor: float = 2.0,
) -> float:
    """Computes delay duration in milliseconds for a retry attempt."""
    if attempt <= 0:
        return 0.0

    strat = (strategy or "EXPONENTIAL").upper()

    if strat == "FIXED":
        return float(base_delay_ms)
    elif strat == "LINEAR":
        return float(base_delay_ms * attempt)
    else:
        multiplier = math.pow(backoff_factor, max(0, attempt - 1))
        return float(base_delay_ms * multiplier)


def is_retriable_exception(exc: Exception) -> bool:
    """Checks whether an exception qualifies for automatic retry."""
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    exc_name = type(exc).__name__.lower()
    return "timeout" in exc_name or "connection" in exc_name or "retry" in exc_name


def calculate_success_rate(successes: int, total: int) -> float:
    """Calculates success percentage."""
    if total <= 0:
        return 100.0
    succ = max(0, int(successes))
    tot = max(1, int(total))
    return round((min(succ, tot) / tot) * 100.0, 2)


def calculate_failure_rate(failures: int, total: int) -> float:
    """Calculates failure percentage."""
    if total <= 0:
        return 0.0
    fail = max(0, int(failures))
    tot = max(1, int(total))
    return round((min(fail, tot) / tot) * 100.0, 2)
