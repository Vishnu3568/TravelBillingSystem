"""
AMIP Platform Exception Definitions.
Defines core exceptions for AMIP context operations.
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
