"""
Pydantic Schemas for AMIP Autonomous Workflow Gateway & Execution Dispatcher.
Defines typed request and response contracts for workflow execution, cancellation, and audit bundles.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class WorkflowExecutionRequest(BaseModel):
    """Request payload to trigger an autonomous AMIP workflow."""
    task_type: str = Field(default="GENERAL_QUERY", description="Task type (e.g., DOCUMENT_IMPORT, VALIDATION_ENGINE, GENERAL_QUERY)")
    summary: str = Field(default="Autonomous AMIP workflow execution", description="High-level summary or description of the requested task")
    priority: str = Field(default="NORMAL", description="Priority level (LOW, NORMAL, HIGH, CRITICAL)")
    execution_mode: str = Field(default="SYNCHRONOUS", description="Execution mode (SYNCHRONOUS, ASYNCHRONOUS, BATCH, DEGRADED)")
    timeout_ms: Optional[float] = Field(default=None, description="Optional execution timeout in milliseconds")
    input_payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary task context or payload data")


class WorkflowExecutionResponse(BaseModel):
    """Response payload returning the outcome of an autonomous workflow execution."""
    workflow_id: str
    trace_id: str
    status: str
    confidence: float
    recommended_action: str
    reason: str
    summary: str
    policy: str
    execution_duration_ms: float
    supporting_agents: List[str] = Field(default_factory=list)
    conflicting_agents: List[str] = Field(default_factory=list)
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    started_at: str
    completed_at: Optional[str] = None


class WorkflowCancelResponse(BaseModel):
    """Response payload returning the cancellation outcome of a workflow."""
    workflow_id: str
    status: str
    message: str
    cancelled_at: str


class WorkflowAuditBundleResponse(BaseModel):
    """Comprehensive synthesized audit bundle containing decision, explanation, timeline, trace, and logs."""
    workflow_id: str
    trace_id: str
    status: str
    decision_result: Optional[Dict[str, Any]] = None
    explanation_report: Optional[Dict[str, Any]] = None
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list)
    spans: List[Dict[str, Any]] = Field(default_factory=list)
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    runtime_metrics: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str
