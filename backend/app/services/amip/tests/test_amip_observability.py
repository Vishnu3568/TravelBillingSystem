"""
Comprehensive Unit Test Suite for AMIP Observability Foundation (Phase 9 Checkpoint 8.1).
Tests TraceManager, StructuredLogRecord, StructuredLogger, CorrelationContext,
ExecutionSnapshot, MetricsCollector, PerformanceProfiler, DiagnosticsEngine, and Concurrency.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest
import threading
import time

from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.observability.structured_log import StructuredLogRecord
from app.services.amip.observability.execution_logger import StructuredLogger
from app.services.amip.observability.trace_manager import TraceManager
from app.services.amip.observability.correlation import CorrelationContext
from app.services.amip.observability.execution_snapshot import ExecutionSnapshot
from app.services.amip.observability.metrics_collector import MetricsCollector
from app.services.amip.observability.performance_profiler import PerformanceProfiler
from app.services.amip.observability.diagnostics import DiagnosticsEngine


# ============================================================================
# 1. TRACE MANAGER TESTS
# ============================================================================
def test_trace_manager_id_generation_and_spans():
    """Verify TraceManager ID generation uniqueness and span hierarchy tracking."""
    tm = TraceManager()
    trc_id = tm.generate_trace_id()
    cor_id = tm.generate_correlation_id()
    wfk_id = tm.generate_workflow_id()
    exe_id = tm.generate_execution_id()

    assert trc_id.startswith("trc-")
    assert cor_id.startswith("cor-")
    assert wfk_id.startswith("wfk-")
    assert exe_id.startswith("exe-")

    span1 = tm.register_span("spn-1", "PlannerSpan", trc_id)
    span2 = tm.register_span("spn-2", "ValidationSpan", trc_id, parent_span_id="spn-1")

    hierarchy = tm.get_span_hierarchy(trc_id)
    assert len(hierarchy) == 2
    assert hierarchy[1]["parent_span_id"] == "spn-1"


# ============================================================================
# 2. STRUCTURED LOG RECORD & LOGGER TESTS
# ============================================================================
def test_structured_log_record_serialization():
    """Verify StructuredLogRecord to_dict, to_json, and from_dict serialization."""
    rec = StructuredLogRecord(
        message="Task completed successfully",
        level="INFO",
        trace_id="trc-100",
        workflow_id="wfk-200",
        task_id="t-1",
        agent_name="ValidationAgent",
        execution_time_ms=45.2,
        status="COMPLETED",
        metadata={"issues_count": 0},
    )

    d = rec.to_dict()
    assert d["message"] == "Task completed successfully"
    assert d["agent_name"] == "ValidationAgent"

    json_str = rec.to_json()
    assert "ValidationAgent" in json_str

    restored = StructuredLogRecord.from_dict(d)
    assert restored.trace_id == "trc-100"
    assert restored.execution_time_ms == 45.2


def test_structured_logger_levels_and_querying():
    """Verify StructuredLogger level methods (info, debug, warning, error, critical) and queries."""
    logger = StructuredLogger()
    logger.info("Info log", trace_id="trc-1", workflow_id="wfk-1")
    logger.debug("Debug log", trace_id="trc-1", workflow_id="wfk-1")
    logger.warning("Warning log", trace_id="trc-1", workflow_id="wfk-1")
    logger.error("Error log", trace_id="trc-2", workflow_id="wfk-2")
    logger.critical("Critical log", trace_id="trc-2", workflow_id="wfk-2")

    logs_trc1 = logger.get_logs(trace_id="trc-1")
    assert len(logs_trc1) == 3

    error_logs = logger.get_logs(level="ERROR")
    assert len(error_logs) == 1
    assert error_logs[0].workflow_id == "wfk-2"

    logger.clear_logs()
    assert len(logger.get_logs()) == 0


# ============================================================================
# 3. CORRELATION CONTEXT TESTS
# ============================================================================
def test_correlation_context_propagation():
    """Verify thread-local CorrelationContext setting, getting, clearing, and context binding."""
    CorrelationContext.set_context(
        trace_id="trc-999",
        workflow_id="wfk-888",
        request_id="req-777",
        span_id="spn-666",
    )

    ctx_dict = CorrelationContext.get_context()
    assert ctx_dict["trace_id"] == "trc-999"
    assert ctx_dict["workflow_id"] == "wfk-888"

    # Bind from ExecutionContext
    exec_ctx = ExecutionContext(workflow_id="wfk-bound", trace_id="trc-bound")
    CorrelationContext.bind_context(exec_ctx)

    bound_dict = CorrelationContext.get_context()
    assert bound_dict["workflow_id"] == "wfk-bound"
    assert bound_dict["trace_id"] == "trc-bound"

    CorrelationContext.clear_context()
    assert CorrelationContext.get_context()["trace_id"] == ""


# ============================================================================
# 4. EXECUTION SNAPSHOT TESTS
# ============================================================================
def test_execution_snapshot_capture():
    """Verify ExecutionSnapshot capture and dictionary roundtrip."""
    snapshot = ExecutionSnapshot.capture(
        workflow_id="wfk-snap-1",
        current_task="t-val",
        completed_tasks=["t-import"],
        pending_tasks=["t-pred"],
        agent_states={"ValidationAgent": "EXECUTING"},
        timeline_records_count=1,
        retry_counts={"ValidationAgent": 0},
    )

    assert snapshot.workflow_id == "wfk-snap-1"
    assert len(snapshot.completed_tasks) == 1

    d = snapshot.to_dict()
    assert d["current_task"] == "t-val"

    restored = ExecutionSnapshot.from_dict(d)
    assert restored.workflow_id == "wfk-snap-1"
    assert restored.agent_states["ValidationAgent"] == "EXECUTING"


# ============================================================================
# 5. METRICS COLLECTOR TESTS
# ============================================================================
def test_metrics_collector():
    """Verify MetricsCollector telemetry tracking, latencies, and success rate computations."""
    mc = MetricsCollector()
    mc.record_workflow_start()
    mc.record_workflow_execution("wfk-1", duration_ms=100.0, success=True, retries=0)

    mc.record_workflow_start()
    mc.record_workflow_execution("wfk-2", duration_ms=300.0, success=False, retries=2)

    mc.record_agent_execution("ValidationAgent", duration_ms=50.0, success=True)
    mc.record_agent_execution("ValidationAgent", duration_ms=150.0, success=True)

    summary = mc.get_summary()
    assert summary["completed_workflows"] == 1
    assert summary["failed_workflows"] == 1
    assert summary["total_retries"] == 2
    assert summary["success_rate"] == 50.0
    assert summary["average_workflow_duration_ms"] == 200.0
    assert summary["average_agent_duration_ms"] == 100.0


# ============================================================================
# 6. PERFORMANCE PROFILER TESTS
# ============================================================================
def test_performance_profiler():
    """Verify PerformanceProfiler profile_start, profile_end, and latency report generation."""
    profiler = PerformanceProfiler()
    profiler.profile_start("PlannerEngine")
    time.sleep(0.02)
    dur = profiler.profile_end("PlannerEngine")
    assert dur >= 15.0

    report = profiler.get_latency_report()
    assert "PlannerEngine" in report
    assert report["PlannerEngine"]["invocations"] == 1
    assert report["PlannerEngine"]["average_ms"] >= 15.0


# ============================================================================
# 7. DIAGNOSTICS ENGINE TESTS
# ============================================================================
def test_diagnostics_engine_reports():
    """Verify DiagnosticsEngine health, runtime, performance, workflow, and agent summaries."""
    logger = StructuredLogger()
    metrics = MetricsCollector()
    profiler = PerformanceProfiler()

    logger.info("Executing task t1", workflow_id="wfk-diag-1", agent_name="ValidationAgent")
    metrics.record_workflow_execution("wfk-diag-1", duration_ms=80.0, success=True)
    profiler.profile_start("ValidationAgent")
    profiler.profile_end("ValidationAgent")

    engine = DiagnosticsEngine(logger=logger, metrics=metrics, profiler=profiler)

    health_rep = engine.generate_platform_health_report()
    assert health_rep["overall_status"] == "HEALTHY"

    runtime_rep = engine.generate_runtime_report()
    assert runtime_rep["total_logs"] == 1

    perf_rep = engine.generate_performance_report()
    assert "ValidationAgent" in perf_rep["latency_profiles"]

    wfk_sum = engine.generate_workflow_summary("wfk-diag-1")
    assert wfk_sum["log_count"] == 1

    agent_sum = engine.generate_agent_summary("ValidationAgent")
    assert agent_sum["total_invocations"] == 1


# ============================================================================
# 8. CONCURRENCY & THREAD SAFETY TESTS
# ============================================================================
def test_observability_thread_safety():
    """Verify thread-safe logging, metrics recording, and trace generation under concurrent workloads."""
    logger = StructuredLogger()
    metrics = MetricsCollector()
    tm = TraceManager()

    def worker(worker_id: int):
        trc = tm.generate_trace_id()
        wfk = tm.generate_workflow_id()
        for i in range(10):
            logger.info(f"Worker {worker_id} msg {i}", trace_id=trc, workflow_id=wfk)
            metrics.record_workflow_execution(wfk, duration_ms=10.0, success=True)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(logger.get_logs()) == 50
    assert metrics.get_summary()["completed_workflows"] == 50
