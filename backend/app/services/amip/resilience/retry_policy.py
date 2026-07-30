"""
AMIP Retry Policy.
Configurable policy defining retry attempts, backoff strategies, and exception filtering.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from app.services.amip.interfaces.resilience_interfaces import IRetryPolicy
from app.services.amip.resilience.resilience_utils import calculate_backoff_delay


@dataclass
class RetryPolicy(IRetryPolicy):
    """
    Defines fault tolerance retry criteria for task and workflow execution attempts.
    """
    max_retries: int = 3
    retry_delay_ms: float = 100.0
    backoff_strategy: str = "EXPONENTIAL"
    retryable_exceptions: List[str] = field(default_factory=list)

    def should_retry(self, attempt: int, exc: Optional[Exception] = None) -> bool:
        """
        Determines whether execution should be retried for the given attempt count and exception.
        """
        if attempt >= self.max_retries:
            return False

        if exc and self.retryable_exceptions:
            exc_name = exc.__class__.__name__
            if exc_name not in self.retryable_exceptions and type(exc).__name__ not in self.retryable_exceptions:
                return False

        return True

    def next_delay(self, attempt: int) -> float:
        """Calculates backoff delay in milliseconds for the next retry attempt."""
        return calculate_backoff_delay(attempt, self.retry_delay_ms, self.backoff_strategy)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes RetryPolicy to dictionary."""
        return {
            "max_retries": self.max_retries,
            "retry_delay_ms": float(self.retry_delay_ms),
            "backoff_strategy": self.backoff_strategy,
            "retryable_exceptions": list(self.retryable_exceptions),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RetryPolicy:
        """Constructs RetryPolicy instance from dictionary."""
        return cls(
            max_retries=int(data.get("max_retries", 3)),
            retry_delay_ms=float(data.get("retry_delay_ms", 100.0)),
            backoff_strategy=data.get("backoff_strategy", "EXPONENTIAL"),
            retryable_exceptions=list(data.get("retryable_exceptions", [])),
        )
