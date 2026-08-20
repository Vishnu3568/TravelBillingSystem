"""
Pydantic Schemas for AMIP Human-in-the-Loop (HITL) Review Queue and Operator Overrides.
Defines typed request and response contracts for operator approval, rejection, and escalation.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HITLReviewItemResponse(BaseModel):
    """Represents a workflow execution currently requiring human operator review."""
    workflow_id: str
    trace_id: str = ""
    task_type: str = "GENERAL_QUERY"
    current_task: str = ""
    status: str = "REVIEW_REQUIRED"
    confidence: float = 0.0
    reason: str = ""
    duration_ms: float = 0.0
    completed_tasks: List[str] = Field(default_factory=list)
    pending_tasks: List[str] = Field(default_factory=list)
    agent_states: Dict[str, str] = Field(default_factory=dict)
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    created_at: str = ""


class HITLOverrideRequest(BaseModel):
    """Payload submitted by a human operator to override or resolve a workflow in review."""
    action: str = Field(..., description="Action to take: APPROVE, REJECT, or ESCALATE")
    reason: str = Field(..., description="Operator justification reason for the decision")
    notes: Optional[str] = Field(default=None, description="Optional extra operator notes")


class HITLOverrideResponse(BaseModel):
    """Outcome of a human operator decision override."""
    workflow_id: str
    previous_status: str
    new_status: str
    action: str
    operator: str
    reason: str
    updated_at: str
    message: str
