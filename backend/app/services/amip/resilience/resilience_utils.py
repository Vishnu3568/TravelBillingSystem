"""
AMIP Resilience Utilities.
Provides backoff calculators and mathematical helpers for fault tolerance.
"""
from __future__ import annotations
import math
from typing import Dict, Any


def calculate_backoff_delay(attempt: int, base_delay_ms: float = 100.0, strategy: str = "EXPONENTIAL") -> float:
    """
    Computes delay duration in milliseconds for a retry attempt.
    Strategies: EXPONENTIAL (base * 2^(attempt-1)), LINEAR (base * attempt), FIXED (base).
    """
    if attempt <= 0:
        return 0.0

    strat = (strategy or "EXPONENTIAL").upper()

    if strat == "FIXED":
        return float(base_delay_ms)
    elif strat == "LINEAR":
        return float(base_delay_ms * attempt)
    else:  # EXPONENTIAL
        multiplier = math.pow(2, max(0, attempt - 1))
        return float(base_delay_ms * multiplier)


def calculate_success_rate(successes: int, total: int) -> float:
    """Calculates success percentage (0.0 to 100.0%)."""
    if total <= 0:
        return 100.0
    succ = max(0, int(successes))
    tot = max(1, int(total))
    return round((min(succ, tot) / tot) * 100.0, 2)


def calculate_failure_rate(failures: int, total: int) -> float:
    """Calculates failure percentage (0.0 to 100.0%)."""
    if total <= 0:
        return 0.0
    fail = max(0, int(failures))
    tot = max(1, int(total))
    return round((min(fail, tot) / tot) * 100.0, 2)
