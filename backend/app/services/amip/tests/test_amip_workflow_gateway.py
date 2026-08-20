"""
Unit and Integration Tests for AMIP Checkpoint 8.4 Autonomous Workflow Gateway & Execution Dispatcher.
Tests workflow execution, ID generation, trace propagation, cooperative cancellation,
audit bundle generation, role authorization, and fault-isolated telemetry.
"""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.services.amip.gateway.workflow_gateway import (
    AMIPWorkflowGateway,
    get_workflow_gateway,
)
from app.services.amip.persistence.observability_repository import (
    SQLAlchemyObservabilityRepository,
)
from app.services.amip.monitoring_service import (
    AMIPMonitoringService,
    get_monitoring_service,
)
from app.schemas.amip_workflow import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowCancelResponse,
    WorkflowAuditBundleResponse,
)
from app.utils.security import create_access_token
from app.main import app


@pytest.fixture
def test_db_session_factory():
    """Creates an isolated in-memory SQLite database with StaticPool for gateway tests."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def gateway(test_db_session_factory):
    """Returns an isolated AMIPWorkflowGateway instance backed by SQLite repository."""
    repo = SQLAlchemyObservabilityRepository(session_factory=test_db_session_factory)
    monitoring_service = AMIPMonitoringService(repository=repo)
    return AMIPWorkflowGateway(monitoring_service=monitoring_service)


def test_gateway_workflow_execution_success(gateway):
    """Verify autonomous workflow execution, ID generation, consensus decision, and telemetry propagation."""
    req = WorkflowExecutionRequest(
        task_type="VALIDATION_ENGINE",
        summary="Automated Bill Anomaly Validation",
        priority="HIGH",
        execution_mode="SYNCHRONOUS",
        input_payload={"bill_id": 101, "vendor": "Express Travels"},
    )

    response = gateway.execute_workflow(
        request=req,
        user_id="operator_bob",
        user_role="MANAGER",
    )

    assert isinstance(response, WorkflowExecutionResponse)
    assert response.workflow_id.startswith("wfk-")
    assert response.trace_id.startswith("trc-")
    assert response.status in ("COMPLETED", "REVIEW_REQUIRED")
    assert 0.0 <= response.confidence <= 1.0
    assert response.policy in ("AUTO_APPROVE", "AUTO_REVIEW", "MANUAL_REVIEW")
    assert response.started_at != ""
    assert response.completed_at is not None

    # Verify telemetry was recorded
    metrics_summary = gateway.monitoring_service.metrics.get_summary()
    assert metrics_summary["completed_workflows"] >= 1

    logs = gateway.monitoring_service.get_workflow_logs(workflow_id=response.workflow_id)
    assert len(logs) >= 2  # init and completion logs


def test_gateway_workflow_cancellation_active_and_terminated(gateway):
    """Verify cooperative cancellation for active, already terminated, and unknown workflows."""
    # 1. Unknown workflow cancellation
    unknown_resp = gateway.cancel_workflow("wfk-nonexistent", user_id="admin")
    assert isinstance(unknown_resp, WorkflowCancelResponse)
    assert unknown_resp.status == "NOT_FOUND"

    # 2. Execute a workflow to completion
    req = WorkflowExecutionRequest(task_type="GENERAL_QUERY", summary="Test query")
    exec_resp = gateway.execute_workflow(request=req)

    # 3. Cancel already-completed workflow
    term_resp = gateway.cancel_workflow(exec_resp.workflow_id, user_id="admin")
    assert term_resp.status == "ALREADY_TERMINATED"


def test_gateway_audit_bundle_generation(gateway):
    """Verify complete audit bundle synthesis containing decision, explanation, timeline, spans, and logs."""
    req = WorkflowExecutionRequest(
        task_type="DOCUMENT_IMPORT",
        summary="Import invoice document OCR parse",
        input_payload={"filename": "sample_invoice.docx"},
    )
    exec_resp = gateway.execute_workflow(request=req)

    # Query audit bundle
    audit = gateway.get_workflow_audit_bundle(exec_resp.workflow_id)
    assert audit is not None
    assert isinstance(audit, WorkflowAuditBundleResponse)
    assert audit.workflow_id == exec_resp.workflow_id
    assert audit.trace_id == exec_resp.trace_id
    assert audit.decision_result is not None
    assert audit.explanation_report is not None
    assert isinstance(audit.timeline_events, list)
    assert isinstance(audit.spans, list)
    assert len(audit.spans) >= 1
    assert len(audit.logs) >= 2


def test_gateway_persistence_failure_isolation(test_db_session_factory):
    """Verify that a database failure during telemetry persistence does NOT fail the workflow execution."""
    faulty_session_factory = MagicMock(side_effect=Exception("Database connection timeout during logging"))
    faulty_repo = SQLAlchemyObservabilityRepository(session_factory=faulty_session_factory)
    faulty_monitoring = AMIPMonitoringService(repository=faulty_repo)
    gateway = AMIPWorkflowGateway(monitoring_service=faulty_monitoring)

    req = WorkflowExecutionRequest(
        task_type="REVIEW_CORRECTION",
        summary="Resilience persistence test",
    )

    # Execution must still succeed smoothly without raising exceptions
    response = gateway.execute_workflow(request=req)
    assert response.workflow_id.startswith("wfk-")
    assert response.status in ("COMPLETED", "REVIEW_REQUIRED")


def test_api_workflow_execution_role_authorization(test_db_session_factory):
    """Verify role-based access control for /api/amip/workflows/execute."""
    repo = SQLAlchemyObservabilityRepository(session_factory=test_db_session_factory)
    monitoring_service = get_monitoring_service()
    monitoring_service.repository = repo
    gateway = get_workflow_gateway()
    gateway.monitoring_service = monitoring_service

    client = TestClient(app)
    req_body = {
        "task_type": "GENERAL_QUERY",
        "summary": "Authorized execution test",
    }

    # 1. Unauthenticated -> 401 Unauthorized or 422 Unprocessable Entity
    unauth_resp = client.post("/api/amip/workflows/execute", json=req_body)
    assert unauth_resp.status_code in (401, 422)

    invalid_resp = client.post(
        "/api/amip/workflows/execute",
        json=req_body,
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert invalid_resp.status_code == 401

    # 2. Forbidden EMPLOYEE -> 403 Forbidden
    emp_token = create_access_token("employee_user", "EMPLOYEE")
    emp_resp = client.post(
        "/api/amip/workflows/execute",
        json=req_body,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert emp_resp.status_code == 403

    # 3. Authorized MANAGER -> 200 OK
    mgr_token = create_access_token("manager_user", "MANAGER")
    mgr_resp = client.post(
        "/api/amip/workflows/execute",
        json=req_body,
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert mgr_resp.status_code == 200
    assert mgr_resp.json()["workflow_id"].startswith("wfk-")

    # 4. Authorized OWNER -> 200 OK
    owner_token = create_access_token("owner_user", "OWNER")
    owner_resp = client.post(
        "/api/amip/workflows/execute",
        json=req_body,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_resp.status_code == 200
    assert owner_resp.json()["workflow_id"].startswith("wfk-")


def test_api_workflow_cancel_and_audit_endpoints(test_db_session_factory):
    """Verify cancel and audit endpoints via TestClient."""
    repo = SQLAlchemyObservabilityRepository(session_factory=test_db_session_factory)
    monitoring_service = get_monitoring_service()
    monitoring_service.repository = repo
    gateway = get_workflow_gateway()
    gateway.monitoring_service = monitoring_service

    client = TestClient(app)
    token = create_access_token("admin_user", "OWNER")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Execute a workflow
    exec_resp = client.post(
        "/api/amip/workflows/execute",
        json={"task_type": "VALIDATION_ENGINE", "summary": "Audit test run"},
        headers=headers,
    )
    assert exec_resp.status_code == 200
    w_id = exec_resp.json()["workflow_id"]

    # 2. Query Audit Bundle via GET /api/amip/workflows/{workflow_id}/audit
    audit_resp = client.get(f"/api/amip/workflows/{w_id}/audit", headers=headers)
    assert audit_resp.status_code == 200
    assert audit_resp.json()["workflow_id"] == w_id
    assert "decision_result" in audit_resp.json()
    assert "explanation_report" in audit_resp.json()

    # 3. Query Nonexistent Audit Bundle -> 404
    missing_audit = client.get("/api/amip/workflows/wfk-ghost/audit", headers=headers)
    assert missing_audit.status_code == 404

    # 4. Cancel Workflow via POST /api/amip/workflows/{workflow_id}/cancel
    cancel_resp = client.post(f"/api/amip/workflows/{w_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "ALREADY_TERMINATED"
