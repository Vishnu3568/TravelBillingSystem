"""
Unit and Integration Tests for AMIP Checkpoint 8.3 Persistent Observability & Audit History.
Tests SQLAlchemy models, repository operations, secret sanitization, fault isolation,
retention cleanup, duplicate handling, and dual-layer API integration.
"""
from __future__ import annotations
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.amip_observability import (
    AMIPWorkflowExecution,
    AMIPExecutionLog,
    AMIPTraceSpan,
)
from app.services.amip.persistence.observability_repository import (
    SQLAlchemyObservabilityRepository,
    sanitize_payload,
)
from app.services.amip.monitoring_service import (
    AMIPMonitoringService,
    get_monitoring_service,
)
from app.services.amip.observability import ExecutionSnapshot
from app.utils.security import create_access_token
from app.main import app

# In-memory SQLite engine for dedicated persistence unit testing
from sqlalchemy.pool import StaticPool

@pytest.fixture
def test_db_session_factory():
    """Creates an isolated in-memory SQLite database for testing AMIP persistence repository."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def repo(test_db_session_factory):
    """Returns an isolated SQLAlchemyObservabilityRepository backed by SQLite."""
    return SQLAlchemyObservabilityRepository(session_factory=test_db_session_factory)


def test_model_imports_and_instantiation():
    """Verify SQLAlchemy models can be imported and instantiated with default values."""
    wf = AMIPWorkflowExecution(
        execution_id="exe-001",
        workflow_id="wfk-001",
        status="RUNNING",
    )
    assert wf.execution_id == "exe-001"
    assert wf.status == "RUNNING"

    log = AMIPExecutionLog(
        workflow_id="wfk-001",
        level="INFO",
        message="Workflow initialized",
        status="COMPLETED",
    )
    assert log.level == "INFO"
    assert log.status == "COMPLETED"
    assert log.message == "Workflow initialized"

    span = AMIPTraceSpan(
        trace_id="trc-001",
        span_id="spn-001",
        name="ValidationSpan",
    )
    assert span.name == "ValidationSpan"


def test_sanitize_payload_recursive():
    """Verify recursive payload sanitization redacts sensitive keys."""
    raw_payload = {
        "user": "admin",
        "password": "mypassword123",
        "token": "bearer-jwt-token",
        "api_key": "gemini-secret-key",
        "secret": "confidential_value",
        "nested": {
            "auth": "basic-auth",
            "credentials": {"raw_text": "Sensitive invoice OCR document string"},
            "safe_metric": 42.5,
        },
        "items": [
            {"password_hash": "$2b$12$xyz", "name": "ItemA"},
            {"raw_content": "binary-blob", "amount": 100.0},
        ],
    }

    clean = sanitize_payload(raw_payload)

    assert clean["password"] == "[REDACTED]"
    assert clean["token"] == "[REDACTED]"
    assert clean["api_key"] == "[REDACTED]"
    assert clean["secret"] == "[REDACTED]"
    assert clean["nested"]["auth"] == "[REDACTED]"
    assert clean["nested"]["credentials"] == "[REDACTED]"
    assert clean["nested"]["safe_metric"] == 42.5
    assert clean["items"][0]["password_hash"] == "[REDACTED]"
    assert clean["items"][0]["name"] == "ItemA"
    assert clean["items"][1]["raw_content"] == "[REDACTED]"
    assert clean["items"][1]["amount"] == 100.0


def test_workflow_execution_persistence_save_and_retrieve(repo):
    """Verify saving, updating, and querying workflow execution records."""
    exec_data = {
        "execution_id": "exe-test-100",
        "workflow_id": "wfk-test-100",
        "trace_id": "trc-test-100",
        "status": "RUNNING",
        "current_task": "t_validation",
        "completed_tasks": ["t_parse"],
        "pending_tasks": ["t_decision"],
        "agent_states": {"ValidationAgent": "RUNNING"},
        "retry_counts": {"ValidationAgent": 0},
        "duration_ms": 120.0,
    }

    # 1. Save new execution
    assert repo.save_workflow_execution(exec_data) is True

    # 2. Retrieve by workflow_id
    saved = repo.get_workflow_execution_by_id("wfk-test-100")
    assert saved is not None
    assert saved["workflow_id"] == "wfk-test-100"
    assert saved["status"] == "RUNNING"
    assert saved["completed_tasks"] == ["t_parse"]
    assert saved["agent_states"] == {"ValidationAgent": "RUNNING"}

    # 3. Update existing execution status
    exec_data["status"] = "COMPLETED"
    exec_data["completed_tasks"] = ["t_parse", "t_validation", "t_decision"]
    exec_data["pending_tasks"] = []
    assert repo.save_workflow_execution(exec_data) is True

    updated = repo.get_workflow_execution_by_id("wfk-test-100")
    assert updated["status"] == "COMPLETED"
    assert len(updated["completed_tasks"]) == 3
    assert updated["completed_at"] is not None

    # 4. Query execution history with pagination
    history = repo.get_workflow_executions(limit=10, status="COMPLETED")
    assert len(history) == 1
    assert history[0]["workflow_id"] == "wfk-test-100"


def test_structured_log_persistence_and_filtering(repo):
    """Verify structured log insertion and filtering by workflow and level."""
    repo.save_structured_log({
        "workflow_id": "wfk-log-200",
        "trace_id": "trc-log-200",
        "agent_name": "ValidationAgent",
        "level": "INFO",
        "message": "Validation started",
        "metadata": {"step": 1},
    })
    repo.save_structured_log({
        "workflow_id": "wfk-log-200",
        "trace_id": "trc-log-200",
        "agent_name": "ValidationAgent",
        "level": "ERROR",
        "message": "Validation encountered anomaly",
        "metadata": {"step": 2, "password": "leak_attempt"},
    })

    # Retrieve all logs
    all_logs = repo.get_logs_by_workflow_id("wfk-log-200")
    assert len(all_logs) == 2
    assert all_logs[0]["message"] == "Validation started"
    # Verify sensitive metadata was redacted
    assert all_logs[1]["metadata"]["password"] == "[REDACTED]"

    # Retrieve filtered logs by level ERROR
    err_logs = repo.get_logs_by_workflow_id("wfk-log-200", level="ERROR")
    assert len(err_logs) == 1
    assert err_logs[0]["level"] == "ERROR"


def test_trace_span_persistence_and_duplicate_protection(repo):
    """Verify trace span hierarchy persistence and duplicate span_id handling."""
    span1 = {
        "trace_id": "trc-span-300",
        "span_id": "spn-root",
        "name": "RootWorkflowSpan",
        "metadata": {"op": "root"},
    }
    span2 = {
        "trace_id": "trc-span-300",
        "span_id": "spn-child-1",
        "parent_span_id": "spn-root",
        "name": "AgentChildSpan",
        "metadata": {"token": "secret-token"},
    }

    assert repo.save_trace_span(span1) is True
    assert repo.save_trace_span(span2) is True

    # Duplicate span update should not fail
    span1_update = {
        "trace_id": "trc-span-300",
        "span_id": "spn-root",
        "name": "UpdatedRootSpan",
        "metadata": {"op": "root_updated"},
    }
    assert repo.save_trace_span(span1_update) is True

    # Retrieve spans
    spans = repo.get_trace_spans_by_trace_id("trc-span-300")
    assert len(spans) == 2
    root_span = next(s for s in spans if s["span_id"] == "spn-root")
    assert root_span["name"] == "UpdatedRootSpan"

    child_span = next(s for s in spans if s["span_id"] == "spn-child-1")
    assert child_span["metadata"]["token"] == "[REDACTED]"


def test_retention_cleanup(repo, test_db_session_factory):
    """Verify retention cleanup deletes records older than cutoff periods."""
    db = test_db_session_factory()
    try:
        # Create an expired workflow (100 days old)
        old_time_100d = datetime.utcnow() - timedelta(days=100)
        old_wf = AMIPWorkflowExecution(
            execution_id="exe-old-100d",
            workflow_id="wfk-old-100d",
            status="COMPLETED",
            started_at=old_time_100d,
        )
        db.add(old_wf)

        # Create an active workflow (10 days old)
        active_time_10d = datetime.utcnow() - timedelta(days=10)
        active_wf = AMIPWorkflowExecution(
            execution_id="exe-active-10d",
            workflow_id="wfk-active-10d",
            status="COMPLETED",
            started_at=active_time_10d,
        )
        db.add(active_wf)

        # Create an expired log (40 days old)
        old_log = AMIPExecutionLog(
            workflow_id="wfk-old-log",
            level="INFO",
            message="Old log",
            timestamp=datetime.utcnow() - timedelta(days=40),
        )
        db.add(old_log)

        # Create a fresh log (2 days old)
        fresh_log = AMIPExecutionLog(
            workflow_id="wfk-fresh-log",
            level="INFO",
            message="Fresh log",
            timestamp=datetime.utcnow() - timedelta(days=2),
        )
        db.add(fresh_log)

        db.commit()
    finally:
        db.close()

    # Execute cleanup (90 days for wf, 30 days for logs/spans)
    counts = repo.cleanup_old_records(workflow_days=90, log_days=30, span_days=30)
    assert counts["deleted_workflows"] == 1
    assert counts["deleted_logs"] == 1

    # Verify active workflow and fresh log remain
    assert repo.get_workflow_execution_by_id("wfk-active-10d") is not None
    assert repo.get_workflow_execution_by_id("wfk-old-100d") is None
    assert len(repo.get_logs_by_workflow_id("wfk-fresh-log")) == 1
    assert len(repo.get_logs_by_workflow_id("wfk-old-log")) == 0


def test_fault_isolation_on_database_failure():
    """Verify database exceptions are safely swallowed and do NOT raise into the application."""
    faulty_session_factory = MagicMock(side_effect=Exception("Simulated MySQL Database Outage / Connection Failure"))
    faulty_repo = SQLAlchemyObservabilityRepository(session_factory=faulty_session_factory)

    # All persistence methods must return False / None / empty list without raising
    assert faulty_repo.save_workflow_execution({"workflow_id": "wfk-fail"}) is False
    assert faulty_repo.save_structured_log({"workflow_id": "wfk-fail"}) is False
    assert faulty_repo.save_trace_span({"span_id": "spn-fail"}) is False
    assert faulty_repo.get_workflow_executions() == []
    assert faulty_repo.get_workflow_execution_by_id("wfk-fail") is None
    assert faulty_repo.get_logs_by_workflow_id("wfk-fail") == []
    assert faulty_repo.get_trace_spans_by_trace_id("trc-fail") == []
    assert faulty_repo.cleanup_old_records() == {"deleted_workflows": 0, "deleted_logs": 0, "deleted_spans": 0}


def test_monitoring_service_dual_layer_integration(repo):
    """Verify AMIPMonitoringService seamlessly bridges live in-memory telemetry with persistent repository."""
    service = AMIPMonitoringService(repository=repo)

    # 1. Record snapshot in service
    snapshot = ExecutionSnapshot.capture(
        workflow_id="wfk-dual-500",
        current_task="t_audit",
        completed_tasks=["t_step1"],
        agent_states={"AuditAgent": "COMPLETED"},
        runtime_metrics={"duration_ms": 95.0},
    )
    service.record_snapshot(snapshot)

    # Retrieve live from memory
    live_snap = service.get_execution_snapshot("wfk-dual-500")
    assert live_snap is not None
    assert live_snap["workflow_id"] == "wfk-dual-500"

    # Reset in-memory cache to simulate server reboot
    service._snapshots.clear()

    # Retrieve again — should fall back to repository
    recovered_snap = service.get_execution_snapshot("wfk-dual-500")
    assert recovered_snap is not None
    assert recovered_snap["workflow_id"] == "wfk-dual-500"
    assert recovered_snap["completed_tasks"] == ["t_step1"]


def test_checkpoint_8_2_api_compatibility_with_persistence(repo):
    """Verify Checkpoint 8.2 REST API endpoints continue to function with persistence fallback."""
    # Wire the global monitoring service with our repo for testing
    monitoring_service = get_monitoring_service()
    monitoring_service.repository = repo
    monitoring_service.reset()

    # Pre-populate a historical execution in repository only (simulate past run)
    repo.save_workflow_execution({
        "execution_id": "exe-hist-900",
        "workflow_id": "wfk-hist-900",
        "trace_id": "trc-hist-900",
        "status": "COMPLETED",
        "current_task": "t_done",
        "completed_tasks": ["t_start", "t_done"],
        "agent_states": {"Supervisor": "COMPLETED"},
    })

    client = TestClient(app)
    token = create_access_token("admin_user", "OWNER")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test GET /api/amip/health
    h_resp = client.get("/api/amip/health", headers=headers)
    assert h_resp.status_code == 200
    assert h_resp.json()["overall_status"] == "HEALTHY"
    assert "persistence_repository" in h_resp.json()["subsystem_health"]

    # 2. Test GET /api/amip/executions (retrieves historical execution from DB)
    ex_resp = client.get("/api/amip/executions", headers=headers)
    assert ex_resp.status_code == 200
    wfk_ids = [e["workflow_id"] for e in ex_resp.json()]
    assert "wfk-hist-900" in wfk_ids

    # 3. Test GET /api/amip/executions/{workflow_id} (fallback query)
    single_resp = client.get("/api/amip/executions/wfk-hist-900", headers=headers)
    assert single_resp.status_code == 200
    assert single_resp.json()["workflow_id"] == "wfk-hist-900"
    assert single_resp.json()["current_task"] == "t_done"
    assert single_resp.json()["agent_states"]["Supervisor"] == "COMPLETED"
