"""
Comprehensive Unit & Integration Test Suite for AMIP Checkpoint 8.6
Durability, Idempotency, Asynchronous Background Execution, and Fault-Tolerant Recovery.
"""
from __future__ import annotations
import time
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.services.amip.gateway.workflow_gateway import AMIPWorkflowGateway
from app.services.amip.persistence.observability_repository import (
    SQLAlchemyObservabilityRepository,
)
from app.services.amip.monitoring_service import AMIPMonitoringService
from app.services.amip.runtime.idempotency_manager import IdempotencyManager
from app.services.amip.runtime.async_worker import AsyncWorkflowWorker
from app.services.amip.runtime.recovery_service import RecoveryService
from app.schemas.amip_workflow import WorkflowExecutionRequest, WorkflowExecutionResponse


@pytest.fixture
def test_db_session_factory():
    """Creates an isolated in-memory SQLite database with StaticPool."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def durability_gateway(test_db_session_factory):
    """Returns an isolated AMIPWorkflowGateway instance with runtime components."""
    repo = SQLAlchemyObservabilityRepository(session_factory=test_db_session_factory)
    monitoring_service = AMIPMonitoringService(repository=repo)
    idempotency_manager = IdempotencyManager(ttl_seconds=60)
    async_worker = AsyncWorkflowWorker(max_workers=4)
    recovery_service = RecoveryService(lease_timeout_seconds=5)

    gateway = AMIPWorkflowGateway(
        monitoring_service=monitoring_service,
        idempotency_manager=idempotency_manager,
        async_worker=async_worker,
        recovery_service=recovery_service,
    )
    yield gateway
    async_worker.shutdown(wait=False)


# ============================================================================
# 1. ASYNCHRONOUS BACKGROUND EXECUTION GATE
# ============================================================================
def test_async_workflow_dispatch_is_non_blocking(durability_gateway):
    """Verify asynchronous execution returns immediately with RUNNING status and completes in background."""
    req = WorkflowExecutionRequest(
        task_type="DOCUMENT_IMPORT",
        summary="Asynchronous bill parsing",
        execution_mode="ASYNCHRONOUS",
        input_payload={"filename": "large_invoice_batch.docx"},
    )

    t0 = time.time()
    resp = durability_gateway.execute_workflow(request=req)
    t_elapsed = time.time() - t0

    # 1. Immediate return (< 200ms)
    assert t_elapsed < 0.25, f"Async execution blocked for {t_elapsed}s"
    assert isinstance(resp, WorkflowExecutionResponse)
    assert resp.status == "RUNNING"
    assert resp.policy == "ASYNC_DISPATCH"
    assert resp.workflow_id.startswith("wfk-")
    assert resp.trace_id.startswith("trc-")

    # 2. Poll until background worker completes (within 4 seconds)
    completed = False
    for _ in range(40):
        time.sleep(0.1)
        snapshot = durability_gateway.monitoring_service.get_execution_snapshot(resp.workflow_id)
        if snapshot and (
            snapshot.get("current_task") == "t_completed"
            or snapshot.get("runtime_metrics", {}).get("status") in ("COMPLETED", "REVIEW_REQUIRED")
            or snapshot.get("status") in ("COMPLETED", "REVIEW_REQUIRED")
        ):
            completed = True
            break

    assert completed, "Background asynchronous execution did not transition to COMPLETED"


# ============================================================================
# 2. IDEMPOTENCY & DEDUPLICATION GATES
# ============================================================================
def test_same_idempotency_key_returns_identical_execution(durability_gateway):
    """Verify identical idempotency key returns the cached execution without re-running."""
    req1 = WorkflowExecutionRequest(
        task_type="VALIDATION_ENGINE",
        summary="Idempotency validation run",
        execution_mode="SYNCHRONOUS",
        idempotency_key="idemp-key-abc-123",
        input_payload={"amount": 5000},
    )

    # First execution -> runs normally
    resp1 = durability_gateway.execute_workflow(request=req1)
    assert resp1.status == "COMPLETED"
    first_workflow_id = resp1.workflow_id

    # Second execution with same key -> returns cached result
    req2 = WorkflowExecutionRequest(
        task_type="VALIDATION_ENGINE",
        summary="Idempotency validation run duplicate",
        execution_mode="SYNCHRONOUS",
        idempotency_key="idemp-key-abc-123",
        input_payload={"amount": 5000},
    )
    resp2 = durability_gateway.execute_workflow(request=req2)
    assert resp2.workflow_id == first_workflow_id
    assert resp2.status == resp1.status
    assert resp2.started_at == resp1.started_at


def test_different_idempotency_keys_produce_independent_executions(durability_gateway):
    """Verify distinct idempotency keys spawn distinct workflow executions."""
    req_a = WorkflowExecutionRequest(
        task_type="COPILOT_CHAT",
        summary="Chat query A",
        idempotency_key="key-user-session-A",
    )
    req_b = WorkflowExecutionRequest(
        task_type="COPILOT_CHAT",
        summary="Chat query B",
        idempotency_key="key-user-session-B",
    )

    resp_a = durability_gateway.execute_workflow(request=req_a)
    resp_b = durability_gateway.execute_workflow(request=req_b)

    assert resp_a.workflow_id != resp_b.workflow_id


# ============================================================================
# 3. STARTUP RECONCILIATION & STALE LEASE RECOVERY GATE
# ============================================================================
def test_startup_reconciliation_cleans_stale_zombie_workflows(durability_gateway):
    """Verify RecoveryService detects and reconciles stale RUNNING workflows after simulated crash."""
    repo = durability_gateway.monitoring_service.repository

    # Insert a simulated stale workflow started 5 minutes ago
    stale_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    repo.save_workflow_execution({
        "workflow_id": "wfk-zombie-crash-1",
        "trace_id": "trc-zombie-1",
        "status": "RUNNING",
        "current_task": "t_ocr_parse",
        "started_at": stale_time,
        "metadata": {"heartbeat_at": stale_time},
    })

    # Insert a fresh workflow (started 1 second ago)
    fresh_time = datetime.now(timezone.utc).isoformat()
    repo.save_workflow_execution({
        "workflow_id": "wfk-fresh-active-2",
        "trace_id": "trc-fresh-2",
        "status": "RUNNING",
        "current_task": "t_active",
        "started_at": fresh_time,
        "metadata": {"heartbeat_at": fresh_time},
    })

    # Run startup reconciliation
    reconciled = durability_gateway.recovery_service.reconcile_stale_workflows(
        repository=repo,
        monitoring_service=durability_gateway.monitoring_service,
    )

    # Assert zombie was reconciled, fresh remains untouched
    assert "wfk-zombie-crash-1" in reconciled
    assert "wfk-fresh-active-2" not in reconciled

    # Check updated database record for zombie
    zombie_db = repo.get_workflow_execution("wfk-zombie-crash-1")
    assert zombie_db["status"] == "STALE_TERMINATED"

    # Verify audit log was recorded
    logs = durability_gateway.monitoring_service.get_workflow_logs(workflow_id="wfk-zombie-crash-1")
    assert any("Startup recovery sweep" in l["message"] for l in logs)


# ============================================================================
# 4. CONCURRENT HITL OVERRIDES (ONLY ONE WINS) GATE
# ============================================================================
def test_concurrent_hitl_overrides_atomic_resolution(durability_gateway):
    """Verify that when multiple overrides are submitted, exactly one succeeds and duplicates fail."""
    repo = durability_gateway.monitoring_service.repository
    repo.save_workflow_execution({
        "workflow_id": "wfk-hitl-race",
        "status": "REVIEW_REQUIRED",
        "current_task": "t_conflict",
    })

    # First override -> APPROVE
    resp1 = durability_gateway.submit_human_override(
        workflow_id="wfk-hitl-race",
        action="APPROVE",
        reason="Operator A approved first",
        operator="operator_alice",
    )
    assert resp1.new_status == "APPROVED"

    # Second override -> REJECT on already transitioned workflow -> must raise 400
    with pytest.raises(HTTPException) as exc_info:
        durability_gateway.submit_human_override(
            workflow_id="wfk-hitl-race",
            action="REJECT",
            reason="Operator B rejected second",
            operator="operator_bob",
        )
    assert exc_info.value.status_code == 400
    assert "Only REVIEW_REQUIRED" in exc_info.value.detail


# ============================================================================
# 5. STEP CHECKPOINTING & FAULT ISOLATION GATES
# ============================================================================
def test_workflow_initial_checkpoint_persisted(durability_gateway):
    """Verify initial execution checkpoint is persisted immediately upon starting."""
    req = WorkflowExecutionRequest(
        task_type="DOCUMENT_IMPORT",
        summary="Checkpoint persistence verification",
    )
    resp = durability_gateway.execute_workflow(request=req)

    db_rec = durability_gateway.monitoring_service.repository.get_workflow_execution(resp.workflow_id)
    assert db_rec is not None
    assert db_rec["workflow_id"] == resp.workflow_id
    assert db_rec["status"] == resp.status
    assert len(db_rec["completed_tasks"]) > 0


def test_durability_fault_isolation_on_db_error(test_db_session_factory):
    """Verify workflow executes cleanly even if persistence repository experiences failure."""
    class BrokenRepository(SQLAlchemyObservabilityRepository):
        def save_workflow_execution(self, execution_data):
            raise RuntimeError("Simulated database failure during checkpoint")

    broken_repo = BrokenRepository(session_factory=test_db_session_factory)
    monitoring_service = AMIPMonitoringService(repository=broken_repo)
    gateway = AMIPWorkflowGateway(monitoring_service=monitoring_service)

    req = WorkflowExecutionRequest(task_type="GENERAL_QUERY", summary="Fault isolation test")
    resp = gateway.execute_workflow(request=req)

    # Workflow must complete successfully despite broken database save
    assert resp.status == "COMPLETED"
    assert resp.workflow_id.startswith("wfk-")
