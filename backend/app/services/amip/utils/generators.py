"""
AMIP Identifier Generators.
Provides UUID-based unique trace, request, and workflow ID generation.
"""
from __future__ import annotations
import uuid


def generate_trace_id() -> str:
    """Generates a globally unique distributed trace identifier."""
    return f"trc-{uuid.uuid4().hex[:16]}"


def generate_request_id() -> str:
    """Generates a unique request identifier for an execution task."""
    return f"req-{uuid.uuid4().hex[:12]}"


def generate_workflow_id() -> str:
    """Generates a unique workflow execution identifier."""
    return f"wfk-{uuid.uuid4().hex[:12]}"
