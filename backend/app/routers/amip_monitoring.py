"""
AMIP Runtime Monitoring & Health API Router.
Exposes platform health, telemetry metrics, active workflow executions, logs, traces, and diagnostics.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.utils.security import RoleChecker
from app.schemas.amip_monitoring import (
    AMIPHealthResponse,
    AMIPMetricsResponse,
    ExecutionSnapshotResponse,
    ExecutionLogResponse,
    TraceResponse,
    DiagnosticsResponse,
)
from app.services.amip.monitoring_service import get_monitoring_service, AMIPMonitoringService

router = APIRouter(prefix="/api/amip", tags=["AMIP Monitoring"])

# Restrict AMIP operational monitoring endpoints to OWNER and MANAGER roles
admin_guard = RoleChecker(["OWNER", "MANAGER"])


@router.get("/health", response_model=AMIPHealthResponse, summary="Get AMIP Platform Health Summary")
def get_amip_health(
    current_user: dict = Depends(admin_guard),
    service: AMIPMonitoringService = Depends(get_monitoring_service),
):
    """
    Returns high-level platform health, active/completed/failed workflow counts, success rate, and subsystem statuses.
    """
    return service.get_platform_health()


@router.get("/metrics", response_model=AMIPMetricsResponse, summary="Get AMIP Telemetry Metrics")
def get_amip_metrics(
    current_user: dict = Depends(admin_guard),
    service: AMIPMonitoringService = Depends(get_monitoring_service),
):
    """
    Returns structured operational telemetry metrics including latency statistics, retries, and success rates.
    """
    return service.get_runtime_metrics()


@router.get("/executions", response_model=List[ExecutionSnapshotResponse], summary="Get Active Execution Snapshots")
def get_active_executions(
    current_user: dict = Depends(admin_guard),
    service: AMIPMonitoringService = Depends(get_monitoring_service),
):
    """
    Returns list of point-in-time workflow execution snapshots.
    """
    return service.get_execution_snapshots()


@router.get(
    "/executions/{workflow_id}",
    response_model=ExecutionSnapshotResponse,
    summary="Get Specific Workflow Execution Snapshot",
)
def get_execution_by_id(
    workflow_id: str,
    current_user: dict = Depends(admin_guard),
    service: AMIPMonitoringService = Depends(get_monitoring_service),
):
    """
    Returns latest available execution state snapshot for the requested workflow_id.
    """
    snapshot = service.get_execution_snapshot(workflow_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution snapshot for workflow '{workflow_id}' not found",
        )
    return snapshot


@router.get(
    "/executions/{workflow_id}/logs",
    response_model=List[ExecutionLogResponse],
    summary="Get Workflow Execution Logs",
)
def get_execution_logs(
    workflow_id: str,
    level: Optional[str] = Query(None, description="Optional log level filter (INFO, DEBUG, WARNING, ERROR, CRITICAL)"),
    current_user: dict = Depends(admin_guard),
    service: AMIPMonitoringService = Depends(get_monitoring_service),
):
    """
    Returns structured log entries emitted during execution of the requested workflow_id.
    """
    return service.get_workflow_logs(workflow_id=workflow_id, level=level)


@router.get("/traces/{trace_id}", response_model=TraceResponse, summary="Get Telemetry Trace Spans")
def get_trace_by_id(
    trace_id: str,
    current_user: dict = Depends(admin_guard),
    service: AMIPMonitoringService = Depends(get_monitoring_service),
):
    """
    Returns span hierarchy and correlation information for the specified trace_id.
    """
    trace_info = service.get_trace_info(trace_id)
    if not trace_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace ID '{trace_id}' not found",
        )
    return trace_info


@router.get("/diagnostics", response_model=DiagnosticsResponse, summary="Get Platform Diagnostics Report")
def get_platform_diagnostics(
    current_user: dict = Depends(admin_guard),
    service: AMIPMonitoringService = Depends(get_monitoring_service),
):
    """
    Returns synthesized platform diagnostics report detailing health, runtime log counts, error logs, and component performance profiles.
    """
    return service.get_diagnostics_report()
