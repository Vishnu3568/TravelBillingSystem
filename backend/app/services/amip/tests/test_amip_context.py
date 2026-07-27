"""
Comprehensive Unit Test Suite for AMIP Shared Context Layer (Phase 9 Checkpoint 1).
Tests ExecutionContext, EvidenceContext, AgentExecutionRecord, ExecutionTimeline,
ExecutionBlackboard, ContextManager, Utilities, Exceptions, Serialization, and Thread Safety.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest
import threading
import time
from datetime import datetime, timezone

from app.services.amip.models.enums import (
    ExecutionStatus,
    TaskType,
    Priority,
    ExecutionMode,
    AgentStatus,
)
from app.services.amip.models.agent_record import AgentExecutionRecord
from app.services.amip.models.execution_timeline import ExecutionTimeline
from app.services.amip.models.evidence_context import EvidenceContext
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.context.blackboard import ExecutionBlackboard
from app.services.amip.context.context_manager import ContextManager
from app.services.amip.exceptions import (
    AmipBaseException,
    ContextNotFound,
    ContextAlreadyExists,
    ContextCorrupted,
)
from app.services.amip.utils import (
    generate_trace_id,
    generate_request_id,
    generate_workflow_id,
    current_utc_timestamp,
    calculate_duration_ms,
    parse_iso_timestamp,
)


# ============================================================================
# 1. ID & TIME UTILITY TESTS
# ============================================================================
def test_id_generators_uniqueness():
    """Verify unique ID generation for trace_id, request_id, and workflow_id."""
    trace_ids = {generate_trace_id() for _ in range(100)}
    request_ids = {generate_request_id() for _ in range(100)}
    workflow_ids = {generate_workflow_id() for _ in range(100)}

    assert len(trace_ids) == 100
    assert len(request_ids) == 100
    assert len(workflow_ids) == 100

    assert next(iter(trace_ids)).startswith("trc-")
    assert next(iter(request_ids)).startswith("req-")
    assert next(iter(workflow_ids)).startswith("wfk-")


def test_time_utilities():
    """Verify ISO timestamp generation, parsing, and duration calculations."""
    ts_now = current_utc_timestamp()
    parsed_dt = parse_iso_timestamp(ts_now)
    assert parsed_dt is not None
    assert parsed_dt.tzinfo == timezone.utc

    assert parse_iso_timestamp("") is None
    assert parse_iso_timestamp("invalid-date") is None

    # Calculate duration
    start_ts = "2026-07-27T10:00:00+00:00"
    end_ts = "2026-07-27T10:00:02.500000+00:00"
    duration = calculate_duration_ms(start_ts, end_ts)
    assert duration == 2500.0

    # Invalid timestamp fallback
    assert calculate_duration_ms("invalid", end_ts) == 0.0


# ============================================================================
# 2. ENUM & EXCEPTION TESTS
# ============================================================================
def test_amip_exceptions():
    """Verify custom exception messaging and hierarchy."""
    exc1 = ContextNotFound("req-123")
    assert "req-123" in str(exc1)
    assert isinstance(exc1, AmipBaseException)

    exc2 = ContextAlreadyExists("req-456")
    assert "req-456" in str(exc2)

    exc3 = ContextCorrupted("req-789", "Data missing")
    assert "req-789" in str(exc3)
    assert "Data missing" in str(exc3)


# ============================================================================
# 3. AGENT EXECUTION RECORD & TIMELINE TESTS
# ============================================================================
def test_agent_execution_record():
    """Verify AgentExecutionRecord lifecycle, completion, and serialization."""
    rec = AgentExecutionRecord(
        agent_name="FieldLabelerAgent",
        input_summary="Document tokenized into 45 cells",
    )
    assert rec.status == AgentStatus.EXECUTING
    assert rec.duration_ms == 0.0

    time.sleep(0.01)
    rec.complete(
        status=AgentStatus.SUCCESS,
        confidence=0.96,
        output_summary="Labeled 12 fields",
        warnings=["Non-standard bata label found"],
    )

    assert rec.status == AgentStatus.SUCCESS
    assert rec.confidence == 0.96
    assert rec.duration_ms > 0.0
    assert len(rec.warnings) == 1

    # Serialization test
    d = rec.to_dict()
    assert d["agent_name"] == "FieldLabelerAgent"
    assert d["status"] == "SUCCESS"

    restored = AgentExecutionRecord.from_dict(d)
    assert restored.agent_name == rec.agent_name
    assert restored.status == AgentStatus.SUCCESS


def test_execution_timeline():
    """Verify ExecutionTimeline records appending, latest retrieval, and summary."""
    timeline = ExecutionTimeline()
    assert timeline.latest() is None
    assert timeline.duration() == 0.0

    rec1 = AgentExecutionRecord(agent_name="DocIntelAgent", duration_ms=120.0, status=AgentStatus.SUCCESS)
    rec2 = AgentExecutionRecord(agent_name="ValidatorAgent", duration_ms=80.0, status=AgentStatus.WARNING)

    timeline.append(rec1)
    timeline.append(rec2)

    assert timeline.latest().agent_name == "ValidatorAgent"
    assert timeline.duration() == 200.0

    summary = timeline.summary()
    assert summary["total_agents_executed"] == 2
    assert summary["total_duration_ms"] == 200.0
    assert summary["latest_agent"] == "ValidatorAgent"

    # Serialization test
    t_list = timeline.to_list()
    restored_timeline = ExecutionTimeline.from_list(t_list)
    assert len(restored_timeline.records) == 2
    assert restored_timeline.latest().agent_name == "ValidatorAgent"


# ============================================================================
# 4. EVIDENCE CONTEXT TESTS
# ============================================================================
def test_evidence_context():
    """Verify EvidenceContext creation, binary bytes handling, and dictionary conversion."""
    ev = EvidenceContext(
        raw_document=b"dummy binary document data",
        ocr_text="SRI TULJA BHAVANI TRAVELS...",
        uploaded_filename="invoice_101.docx",
        document_metadata={"pages": 1},
        bill_metadata={"grand_total": 1500.0},
        knowledge_context=["Company uses layout A"],
    )

    dict_repr = ev.to_dict(include_raw_bytes=False)
    assert dict_repr["uploaded_filename"] == "invoice_101.docx"
    assert dict_repr["raw_document"] == "<26 bytes>"

    dict_repr_bytes = ev.to_dict(include_raw_bytes=True)
    assert dict_repr_bytes["raw_document"] == b"dummy binary document data"

    restored = EvidenceContext.from_dict(dict_repr)
    assert restored.uploaded_filename == "invoice_101.docx"
    assert restored.raw_document is None


# ============================================================================
# 5. EXECUTION CONTEXT TESTS
# ============================================================================
def test_execution_context():
    """Verify ExecutionContext initialization, stage updates, and serialization."""
    ctx = ExecutionContext(
        task_type=TaskType.DOCUMENT_IMPORT,
        user_id="owner2",
        user_role="OWNER",
        session_id="session_test_99",
        priority=Priority.HIGH,
    )

    assert ctx.current_stage == "INITIALIZED"
    assert ctx.overall_status == ExecutionStatus.PENDING
    assert ctx.priority == Priority.HIGH

    ctx.update_stage("FIELDS_LABELED", ExecutionStatus.RUNNING)
    assert ctx.current_stage == "FIELDS_LABELED"
    assert ctx.overall_status == ExecutionStatus.RUNNING

    # Add evidence & timeline
    ctx.evidence.uploaded_filename = "test_doc.docx"
    rec = AgentExecutionRecord(agent_name="TestAgent", status=AgentStatus.SUCCESS)
    ctx.timeline.append(rec)

    serialized = ctx.to_dict(include_raw_bytes=False)
    assert serialized["user_id"] == "owner2"
    assert serialized["task_type"] == "DOCUMENT_IMPORT"
    assert serialized["evidence"]["uploaded_filename"] == "test_doc.docx"
    assert len(serialized["timeline"]) == 1

    deserialized = ExecutionContext.from_dict(serialized)
    assert deserialized.request_id == ctx.request_id
    assert deserialized.task_type == TaskType.DOCUMENT_IMPORT
    assert deserialized.overall_status == ExecutionStatus.RUNNING


# ============================================================================
# 6. EXECUTION BLACKBOARD & THREAD SAFETY TESTS
# ============================================================================
def test_execution_blackboard_basic_operations():
    """Verify ExecutionBlackboard put, get, exists, remove, clear, keys, and snapshot."""
    bb = ExecutionBlackboard()
    assert not bb.exists("key1")

    bb.put("key1", "value1")
    bb.put("key2", 42)
    bb.put("key3", {"nested": "data"})

    assert bb.exists("key1")
    assert bb.get("key1") == "value1"
    assert bb.get("key2") == 42
    assert bb.get("nonexistent", "default") == "default"

    assert set(bb.keys()) == {"key1", "key2", "key3"}

    snap = bb.snapshot()
    assert snap["key2"] == 42

    assert bb.remove("key1") is True
    assert bb.remove("key1") is False
    assert not bb.exists("key1")

    bb.clear()
    assert len(bb.keys()) == 0

    with pytest.raises(ValueError):
        bb.put("", "invalid")


def test_blackboard_thread_safety():
    """Verify concurrent thread-safe reads and writes on ExecutionBlackboard."""
    bb = ExecutionBlackboard()
    errors = []

    def worker(thread_idx: int):
        try:
            for i in range(100):
                bb.put(f"t_{thread_idx}_{i}", i)
                val = bb.get(f"t_{thread_idx}_{i}")
                if val != i:
                    errors.append(f"Mismatch: thread {thread_idx}, i={i}, val={val}")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(bb.keys()) == 1000


# ============================================================================
# 7. CONTEXT MANAGER TESTS
# ============================================================================
def test_context_manager_lifecycle():
    """Verify ContextManager creation, retrieval, updates, saving, and destruction."""
    cm = ContextManager()
    assert len(cm.list_contexts()) == 0

    ctx = cm.create_context(
        task_type=TaskType.COPILOT_CHAT,
        user_id="user_john",
        user_role="MANAGER",
        session_id="session_123",
    )

    req_id = ctx.request_id
    assert len(cm.list_contexts()) == 1
    assert cm.get_context(req_id).user_id == "user_john"

    # Blackboard retrieval
    bb = cm.get_blackboard(req_id)
    bb.put("copilot_query", "Explain bill #101")
    assert cm.get_blackboard(req_id).get("copilot_query") == "Explain bill #101"

    # Update context
    ctx.update_stage("EXPLAINED", ExecutionStatus.COMPLETED)
    cm.update_context(ctx)
    assert cm.get_context(req_id).current_stage == "EXPLAINED"

    # Save / Upsert context
    new_ctx = ExecutionContext(request_id="custom_req_007", user_id="agent_007")
    cm.save_context(new_ctx)
    assert cm.get_context("custom_req_007").user_id == "agent_007"

    # Destroy context
    assert cm.destroy_context(req_id) is True
    assert cm.destroy_context(req_id) is False

    with pytest.raises(ContextNotFound):
        cm.get_context(req_id)

    with pytest.raises(ContextNotFound):
        cm.get_blackboard(req_id)

    # Exception checks
    with pytest.raises(ContextAlreadyExists):
        cm.create_context(request_id="custom_req_007")

    with pytest.raises(ContextNotFound):
        cm.update_context(ExecutionContext(request_id="nonexistent_id"))

    with pytest.raises(ContextCorrupted):
        cm.update_context(None)

    cm.clear_all()
    assert len(cm.list_contexts()) == 0


def test_context_manager_thread_safety():
    """Verify concurrent thread-safe context creation and management."""
    cm = ContextManager()
    created_ids = []
    lock = threading.Lock()
    errors = []

    def worker(thread_idx: int):
        try:
            for i in range(20):
                ctx = cm.create_context(
                    task_type=TaskType.DOCUMENT_IMPORT,
                    user_id=f"user_{thread_idx}_{i}",
                )
                with lock:
                    created_ids.append(ctx.request_id)
                bb = cm.get_blackboard(ctx.request_id)
                bb.put("worker_id", thread_idx)
        except Exception as e:
            with lock:
                errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(created_ids) == 100
    assert len(cm.list_contexts()) == 100

    cm.clear_all()
    assert len(cm.list_contexts()) == 0
