"""
Unit and Integration Tests for AMIP Checkpoint 8.5 Human-in-the-Loop (HITL) Review & Overrides.
Tests pending review retrieval, APPROVE / REJECT / ESCALATE overrides, state validation,
audit log generation, and role authorization.
"""
from __future__ import annotations
import pytest
from fastapi import HTTPException
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
from app.services.amip.observability import ExecutionSnapshot
from app.schemas.amip_hitl import (
    HITLReviewItemResponse,
    HITLOverrideRequest,
    HITLOverrideResponse,
)
from app.utils.security import create_access_token
from app.main import app


@pytest.fixture
def test_db_session_factory():
    """Creates an isolated in-memory SQLite database with StaticPool."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def hitl_gateway(test_db_session_factory):
    """Returns an isolated AMIPWorkflowGateway instance backed by SQLite repository."""
    repo = SQLAlchemyObservabilityRepository(session_factory=test_db_session_factory)
    monitoring_service = AMIPMonitoringService(repository=repo)
    return AMIPWorkflowGateway(monitoring_service=monitoring_service)


def test_hitl_pending_reviews_retrieval(hitl_gateway):
    """Verify retrieval of pending reviews for workflows in REVIEW_REQUIRED status."""
    # 1. Add a REVIEW_REQUIRED workflow
    snap_review = ExecutionSnapshot.capture(
        workflow_id="wfk-review-1",
        current_task="t_validate",
        completed_tasks=["t_parse"],
        pending_tasks=["t_decision"],
        agent_states={"ValidationAgent": "REVIEW_REQUIRED"},
    )
    hitl_gateway.monitoring_service.record_snapshot(snap_review)
    # Update status in snapshot dict
    hitl_gateway.monitoring_service._snapshots["wfk-review-1"].current_task = "t_validate"

    # Also save to repository with REVIEW_REQUIRED
    hitl_gateway.monitoring_service.repository.save_workflow_execution({
        "workflow_id": "wfk-review-1",
        "status": "REVIEW_REQUIRED",
        "current_task": "t_validate",
        "completed_tasks": ["t_parse"],
        "pending_tasks": ["t_decision"],
        "agent_states": {"ValidationAgent": "REVIEW_REQUIRED"},
    })

    # Add a COMPLETED workflow (should not appear in pending reviews)
    hitl_gateway.monitoring_service.repository.save_workflow_execution({
        "workflow_id": "wfk-completed-2",
        "status": "COMPLETED",
    })

    # Retrieve pending reviews
    pending = hitl_gateway.get_pending_reviews()
    assert len(pending) == 1
    assert pending[0].workflow_id == "wfk-review-1"
    assert pending[0].status == "REVIEW_REQUIRED"


def test_hitl_override_approve_action(hitl_gateway):
    """Verify human operator APPROVE override updates status and writes auditable log."""
    hitl_gateway.monitoring_service.repository.save_workflow_execution({
        "workflow_id": "wfk-override-approve",
        "status": "REVIEW_REQUIRED",
        "current_task": "t_conflict",
    })

    resp = hitl_gateway.submit_human_override(
        workflow_id="wfk-override-approve",
        action="APPROVE",
        reason="Manual verification of fuel receipt confirmed valid",
        operator="manager_alice",
    )

    assert isinstance(resp, HITLOverrideResponse)
    assert resp.workflow_id == "wfk-override-approve"
    assert resp.previous_status == "REVIEW_REQUIRED"
    assert resp.new_status == "APPROVED"
    assert resp.operator == "manager_alice"

    # Verify audit log was recorded
    logs = hitl_gateway.monitoring_service.get_workflow_logs(workflow_id="wfk-override-approve")
    assert any("Manual verification" in l["message"] for l in logs)


def test_hitl_override_reject_and_escalate(hitl_gateway):
    """Verify REJECT and ESCALATE override actions."""
    # REJECT test
    hitl_gateway.monitoring_service.repository.save_workflow_execution({
        "workflow_id": "wfk-reject-1",
        "status": "REVIEW_REQUIRED",
    })
    rej_resp = hitl_gateway.submit_human_override(
        workflow_id="wfk-reject-1",
        action="REJECT",
        reason="Duplicate invoice detected upon visual review",
        operator="manager_bob",
    )
    assert rej_resp.new_status == "REJECTED"

    # ESCALATE test
    hitl_gateway.monitoring_service.repository.save_workflow_execution({
        "workflow_id": "wfk-escalate-1",
        "status": "REVIEW_REQUIRED",
    })
    esc_resp = hitl_gateway.submit_human_override(
        workflow_id="wfk-escalate-1",
        action="ESCALATE",
        reason="Requires legal compliance audit",
        operator="manager_bob",
    )
    assert esc_resp.new_status == "ESCALATED"


def test_hitl_override_invalid_state_and_action(hitl_gateway):
    """Verify error handling for invalid actions and invalid workflow states."""
    # 1. Invalid Action
    hitl_gateway.monitoring_service.repository.save_workflow_execution({
        "workflow_id": "wfk-err-1",
        "status": "REVIEW_REQUIRED",
    })
    with pytest.raises(HTTPException) as exc_info:
        hitl_gateway.submit_human_override(
            workflow_id="wfk-err-1",
            action="INVALID_ACTION",
            reason="testing",
        )
    assert exc_info.value.status_code == 400
    assert "Invalid action" in exc_info.value.detail

    # 2. Overriding workflow that is already COMPLETED
    hitl_gateway.monitoring_service.repository.save_workflow_execution({
        "workflow_id": "wfk-completed-1",
        "status": "COMPLETED",
    })
    with pytest.raises(HTTPException) as exc_info2:
        hitl_gateway.submit_human_override(
            workflow_id="wfk-completed-1",
            action="APPROVE",
            reason="testing",
        )
    assert exc_info2.value.status_code == 400
    assert "Only REVIEW_REQUIRED" in exc_info2.value.detail

    # 3. Nonexistent workflow
    with pytest.raises(HTTPException) as exc_info3:
        hitl_gateway.submit_human_override(
            workflow_id="wfk-ghost-999",
            action="APPROVE",
            reason="testing",
        )
    assert exc_info3.value.status_code == 404


def test_api_hitl_endpoints_role_authorization(test_db_session_factory):
    """Verify API endpoints for pending reviews and operator overrides via TestClient."""
    repo = SQLAlchemyObservabilityRepository(session_factory=test_db_session_factory)
    monitoring_service = get_monitoring_service()
    monitoring_service.repository = repo
    gateway = get_workflow_gateway()
    gateway.monitoring_service = monitoring_service

    # Create a pending review in DB
    repo.save_workflow_execution({
        "workflow_id": "wfk-api-review",
        "status": "REVIEW_REQUIRED",
        "current_task": "t_validate",
    })

    client = TestClient(app)

    # 1. Unauthenticated -> 401 or 422
    unauth_resp = client.get("/api/amip/reviews/pending")
    assert unauth_resp.status_code in (401, 422)

    # 2. Forbidden EMPLOYEE -> 403
    emp_token = create_access_token("emp_user", "EMPLOYEE")
    emp_resp = client.get("/api/amip/reviews/pending", headers={"Authorization": f"Bearer {emp_token}"})
    assert emp_resp.status_code == 403

    # 3. Authorized MANAGER -> 200 OK
    mgr_token = create_access_token("mgr_user", "MANAGER")
    mgr_resp = client.get("/api/amip/reviews/pending", headers={"Authorization": f"Bearer {mgr_token}"})
    assert mgr_resp.status_code == 200
    assert any(r["workflow_id"] == "wfk-api-review" for r in mgr_resp.json())

    # 4. Submit Override via POST /api/amip/workflows/{id}/override
    override_body = {
        "action": "APPROVE",
        "reason": "Approved via administrative review",
        "notes": "Verified by manager",
    }
    ov_resp = client.post(
        "/api/amip/workflows/wfk-api-review/override",
        json=override_body,
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert ov_resp.status_code == 200
    assert ov_resp.json()["new_status"] == "APPROVED"
    assert ov_resp.json()["operator"] == "mgr_user"
