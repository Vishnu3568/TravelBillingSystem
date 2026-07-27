"""
AMIP Platform Exception Definitions.
Defines core exceptions for AMIP context operations and decision calculations.
"""
from __future__ import annotations


class AmipBaseException(Exception):
    """Base exception for all AMIP platform errors."""
    pass


class ContextNotFound(AmipBaseException):
    """Raised when a requested execution context ID is not found in storage."""
    def __init__(self, context_id: str):
        self.context_id = context_id
        super().__init__(f"AMIP Execution Context '{context_id}' was not found.")


class ContextAlreadyExists(AmipBaseException):
    """Raised when attempting to create a context that already exists."""
    def __init__(self, context_id: str):
        self.context_id = context_id
        super().__init__(f"AMIP Execution Context '{context_id}' already exists.")


class ContextCorrupted(AmipBaseException):
    """Raised when a context object or blackboard state fails integrity validation."""
    def __init__(self, context_id: str, reason: str):
        self.context_id = context_id
        self.reason = reason
        super().__init__(f"AMIP Execution Context '{context_id}' is corrupted: {reason}")


class DecisionConflict(AmipBaseException):
    """Raised when agent votes conflict below confidence resolution threshold."""
    def __init__(self, decision_id: str, details: str):
        self.decision_id = decision_id
        self.details = details
        super().__init__(f"AMIP Decision '{decision_id}' failed due to unresolvable conflict: {details}")


class DecisionFailed(AmipBaseException):
    """Raised when decision evaluation algorithm encounters a fatal processing error."""
    def __init__(self, decision_id: str, reason: str):
        self.decision_id = decision_id
        self.reason = reason
        super().__init__(f"AMIP Decision '{decision_id}' evaluation failed: {reason}")


class DecisionTimeout(AmipBaseException):
    """Raised when decision evaluation exceeds deadline threshold."""
    def __init__(self, decision_id: str, timeout_ms: float):
        self.decision_id = decision_id
        self.timeout_ms = timeout_ms
        super().__init__(f"AMIP Decision '{decision_id}' timed out after {timeout_ms:.2f}ms.")
