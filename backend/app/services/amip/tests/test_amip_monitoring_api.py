"""
Unit and Integration Tests for AMIP Checkpoint 8.2 Runtime Monitoring & Health APIs.
Tests health summary, telemetry metrics, execution snapshots, log querying, trace hierarchies,
diagnostics reports, security authorization, and sensitive data sanitization.
"""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.security import create_access_token
from app.services.amip.monitoring_service import get_monitoring_service
from app.services.amip.observability import ExecutionSnapshot

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_monitoring_state():
    """Resets monitoring service state before each test."""
    service = get_monitoring_service()
    service.reset()
    yield
    service.reset()


def get_auth_header(role: str = "OWNER", username: str = "test_admin") -> dict:
    """Generates Bearer token header for the given role."""
    token = create_access_token(username=username, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint_unauthenticated():
    """Verify health endpoint rejects unauthenticated requests with 401 or 422."""
    # Missing Authorization header -> FastAPI Header(...) validation returns 422
    response = client.get("/api/amip/health")
    assert response.status_code in (401, 422)

    # Invalid Authorization token -> security dependency returns 401
    invalid_resp = client.get("/api/amip/health", headers={"Authorization": "Bearer invalid_token"})
    assert invalid_resp.status_code == 401


def test_health_endpoint_forbidden_role():
    """Verify health endpoint rejects EMPLOYEE role with 403."""
    headers = get_auth_header(role="EMPLOYEE")
    response = client.get("/api/amip/health", headers=headers)
    assert response.status_code == 403
    assert "insufficient permissions" in response.json()["detail"]


def test_health_endpoint_success():
    """Verify health endpoint returns 200 with correct schema for OWNER / MANAGER."""
    headers = get_auth_header(role="OWNER")
    response = client.get("/api/amip/health", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "HEALTHY"
    assert "generated_at" in data
    assert data["active_workflows"] == 0
    assert data["completed_workflows"] == 0
    assert data["failed_workflows"] == 0
    assert data["success_rate"] == 100.0
    assert "subsystem_health" in data
    assert data["subsystem_health"]["metrics_collector"] == "HEALTHY"


def test_metrics_endpoint_collection():
    """Verify metrics endpoint returns aggregated telemetry data matching collector state."""
    service = get_monitoring_service()
    service.metrics.record_workflow_start()
    service.metrics.record_workflow_execution("wfk-101", duration_ms=150.0, success=True, retries=1)
    service.metrics.record_agent_execution("ValidationAgent", duration_ms=45.0, success=True)

    headers = get_auth_header(role="MANAGER")
    response = client.get("/api/amip/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["completed_workflows"] == 1
    assert data["total_retries"] == 1
    assert data["average_workflow_duration_ms"] == 150.0
    assert data["average_agent_duration_ms"] == 45.0
    assert data["success_rate"] == 100.0


def test_execution_snapshots_list_and_get():
    """Verify execution snapshots listing and single workflow retrieval."""
    service = get_monitoring_service()

    snapshot = ExecutionSnapshot.capture(
        workflow_id="wfk-snap-200",
        current_task="t_validate",
        completed_tasks=["t_parse"],
        pending_tasks=["t_save"],
        agent_states={"ValidationAgent": "RUNNING"},
        timeline_records_count=2,
        runtime_metrics={"duration_ms": 80.0},
        retry_counts={"t_parse": 0},
    )
    service.record_snapshot(snapshot)

    headers = get_auth_header(role="OWNER")

    # List all executions
    list_resp = client.get("/api/amip/executions", headers=headers)
    assert list_resp.status_code == 200
    snaps = list_resp.json()
    assert len(snaps) == 1
    assert snaps[0]["workflow_id"] == "wfk-snap-200"
    assert snaps[0]["current_task"] == "t_validate"

    # Get single execution by ID
    get_resp = client.get("/api/amip/executions/wfk-snap-200", headers=headers)
    assert get_resp.status_code == 200
    single_snap = get_resp.json()
    assert single_snap["workflow_id"] == "wfk-snap-200"

    # Missing execution returns 404
    missing_resp = client.get("/api/amip/executions/wfk-nonexistent", headers=headers)
    assert missing_resp.status_code == 404
    assert "not found" in missing_resp.json()["detail"]


def test_workflow_logs_query_and_filter():
    """Verify workflow log entries endpoint with level filtering."""
    service = get_monitoring_service()
    service.logger.info("Task t1 started", workflow_id="wfk-logs-300", agent_name="AgentA")
    service.logger.error("Task t2 failed", workflow_id="wfk-logs-300", agent_name="AgentB")

    headers = get_auth_header(role="MANAGER")

    # Query all logs for workflow
    all_logs_resp = client.get("/api/amip/executions/wfk-logs-300/logs", headers=headers)
    assert all_logs_resp.status_code == 200
    logs = all_logs_resp.json()
    assert len(logs) == 2

    # Query filtered by level ERROR
    err_logs_resp = client.get("/api/amip/executions/wfk-logs-300/logs?level=ERROR", headers=headers)
    assert err_logs_resp.status_code == 200
    err_logs = err_logs_resp.json()
    assert len(err_logs) == 1
    assert err_logs[0]["level"] == "ERROR"
    assert err_logs[0]["message"] == "Task t2 failed"

    # Unknown workflow returns empty list
    empty_resp = client.get("/api/amip/executions/wfk-unknown/logs", headers=headers)
    assert empty_resp.status_code == 200
    assert empty_resp.json() == []


def test_trace_spans_endpoint():
    """Verify trace span hierarchy endpoint."""
    service = get_monitoring_service()
    trc_id = service.trace_manager.generate_trace_id()
    service.trace_manager.register_span(span_id="spn-1", name="RootWorkflow", trace_id=trc_id)
    service.trace_manager.register_span(span_id="spn-2", name="AgentStep", trace_id=trc_id, parent_span_id="spn-1")

    headers = get_auth_header(role="OWNER")

    # Trace found
    trace_resp = client.get(f"/api/amip/traces/{trc_id}", headers=headers)
    assert trace_resp.status_code == 200
    data = trace_resp.json()
    assert data["trace_id"] == trc_id
    assert data["total_spans"] == 2
    assert len(data["spans"]) == 2

    # Non-existent trace returns 404
    missing_resp = client.get("/api/amip/traces/trc-missing-999", headers=headers)
    assert missing_resp.status_code == 404
    assert "not found" in missing_resp.json()["detail"]


def test_platform_diagnostics_report():
    """Verify diagnostics report synthesis endpoint."""
    service = get_monitoring_service()
    service.logger.info("Initializing workflow", workflow_id="wfk-diag-400")

    headers = get_auth_header(role="OWNER")
    resp = client.get("/api/amip/diagnostics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "health_report" in data
    assert "runtime_report" in data
    assert "performance_report" in data
    assert "generated_at" in data
    assert data["health_report"]["overall_status"] == "HEALTHY"


def test_sensitive_data_sanitization():
    """Verify sensitive content like passwords, tokens, and raw_text are redacted."""
    service = get_monitoring_service()

    snapshot = ExecutionSnapshot.capture(
        workflow_id="wfk-secret-500",
        current_task="t_secret",
        memory_stats={"password": "supersecretpassword123", "active_threads": 4},
        runtime_metrics={"raw_text": "Sensitive doc payload", "metric_ok": 10},
    )
    service.record_snapshot(snapshot)

    headers = get_auth_header(role="OWNER")
    resp = client.get("/api/amip/executions/wfk-secret-500", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["memory_stats"]["password"] == "[REDACTED]"
    assert data["memory_stats"]["active_threads"] == 4
    assert data["runtime_metrics"]["raw_text"] == "[REDACTED]"
    assert data["runtime_metrics"]["metric_ok"] == 10
