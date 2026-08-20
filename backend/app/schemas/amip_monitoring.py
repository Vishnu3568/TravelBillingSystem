"""
Pydantic Response Schemas for AMIP Runtime Monitoring & Health APIs.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AMIPHealthResponse(BaseModel):
    """
    Response model for GET /api/amip/health
    """
    overall_status: str = Field(..., description="Overall platform status (HEALTHY, DEGRADED, UNHEALTHY, CRITICAL)")
    generated_at: str = Field(..., description="ISO 8601 UTC timestamp of report generation")
    active_workflows: int = Field(0, description="Count of currently active workflow executions")
    completed_workflows: int = Field(0, description="Count of successfully completed workflows")
    failed_workflows: int = Field(0, description="Count of failed workflows")
    success_rate: float = Field(100.0, description="Overall workflow execution success percentage")
    average_workflow_duration_ms: float = Field(0.0, description="Average workflow execution latency in milliseconds")
    total_retries: int = Field(0, description="Total count of retries performed across workflows")
    subsystem_health: Dict[str, Any] = Field(default_factory=dict, description="Health status breakdown of individual subsystems")


class AMIPMetricsResponse(BaseModel):
    """
    Response model for GET /api/amip/metrics
    """
    active_workflows: int = Field(0, description="Count of active workflows")
    completed_workflows: int = Field(0, description="Count of completed workflows")
    failed_workflows: int = Field(0, description="Count of failed workflows")
    total_retries: int = Field(0, description="Total retry operations")
    success_rate: float = Field(100.0, description="Success rate percentage")
    average_workflow_duration_ms: float = Field(0.0, description="Average workflow execution duration")
    max_workflow_duration_ms: float = Field(0.0, description="Maximum recorded workflow duration")
    min_workflow_duration_ms: float = Field(0.0, description="Minimum recorded workflow duration")
    average_agent_duration_ms: float = Field(0.0, description="Average agent task execution duration")
    agent_statistics: Optional[Dict[str, Any]] = Field(default=None, description="Detailed agent-level performance breakdown")


class ExecutionSnapshotResponse(BaseModel):
    """
    Response model for GET /api/amip/executions and GET /api/amip/executions/{workflow_id}
    """
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    timestamp: str = Field(..., description="UTC timestamp of snapshot capture")
    workflow_id: str = Field(..., description="Associated workflow identifier")
    current_task: str = Field("", description="Currently executing task ID")
    completed_tasks: List[str] = Field(default_factory=list, description="List of completed task IDs")
    pending_tasks: List[str] = Field(default_factory=list, description="List of pending task IDs")
    agent_states: Dict[str, str] = Field(default_factory=dict, description="Map of agent name to execution status")
    timeline_records_count: int = Field(0, description="Count of timeline event records")
    runtime_metrics: Dict[str, Any] = Field(default_factory=dict, description="Snapshot runtime metrics")
    memory_stats: Dict[str, Any] = Field(default_factory=dict, description="Execution thread and memory statistics")
    retry_counts: Dict[str, int] = Field(default_factory=dict, description="Map of task/agent to retry count")


class ExecutionLogResponse(BaseModel):
    """
    Response model for GET /api/amip/executions/{workflow_id}/logs
    """
    message: str = Field(..., description="Log message text")
    level: str = Field("INFO", description="Log severity level")
    timestamp: str = Field(..., description="UTC timestamp of log entry")
    trace_id: str = Field("", description="Associated trace identifier")
    workflow_id: str = Field("", description="Associated workflow identifier")
    task_id: str = Field("", description="Associated task identifier")
    agent_name: str = Field("", description="Associated agent name")
    execution_time_ms: float = Field(0.0, description="Execution duration in milliseconds")
    status: str = Field("COMPLETED", description="Execution status at log emission")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured log metadata")


class SpanResponse(BaseModel):
    """
    Response model for individual telemetry span in TraceResponse
    """
    span_id: str = Field(..., description="Unique span identifier")
    name: str = Field(..., description="Span or operation name")
    trace_id: str = Field(..., description="Associated trace identifier")
    parent_span_id: Optional[str] = Field(None, description="Parent span identifier if nested")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Span metadata attributes")


class TraceResponse(BaseModel):
    """
    Response model for GET /api/amip/traces/{trace_id}
    """
    trace_id: str = Field(..., description="Unique trace identifier")
    spans: List[SpanResponse] = Field(default_factory=list, description="Hierarchical telemetry spans for trace")
    total_spans: int = Field(0, description="Total count of spans in trace")


class DiagnosticsResponse(BaseModel):
    """
    Response model for GET /api/amip/diagnostics
    """
    health_report: Dict[str, Any] = Field(default_factory=dict, description="Synthesized platform health report")
    runtime_report: Dict[str, Any] = Field(default_factory=dict, description="Runtime telemetry and error log report")
    performance_report: Dict[str, Any] = Field(default_factory=dict, description="Performance and latency profile report")
    generated_at: str = Field(..., description="UTC timestamp of report generation")
