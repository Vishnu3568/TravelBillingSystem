"""
Verification script for Checkpoint 8.1 - Observability Foundation.
Verifies metrics collection, unique trace IDs, correlation propagation,
diagnostics report generation, execution snapshot, and workflow summary.
"""
from __future__ import annotations
import json
from app.services.amip.observability import (
    TraceManager,
    StructuredLogger,
    CorrelationContext,
    MetricsCollector,
    PerformanceProfiler,
    ExecutionSnapshot,
    DiagnosticsEngine,
)


def verify_checkpoint_8_1():
    print("=== CHECKPOINT 8.1 VERIFICATION SCRIPT ===")

    # 1. Metrics & Trace Verification
    tm = TraceManager()
    trc1 = tm.generate_trace_id()
    trc2 = tm.generate_trace_id()
    assert trc1 != trc2, "Trace IDs must be unique!"
    print(f"[OK] Unique Trace IDs Verified: {trc1}, {trc2}")

    # 2. Correlation Context Verification
    CorrelationContext.set_context(trace_id=trc1, workflow_id="wfk-sample-100", request_id="req-555")
    ctx = CorrelationContext.get_context()
    assert ctx["trace_id"] == trc1 and ctx["workflow_id"] == "wfk-sample-100"
    print(f"[OK] Correlation Context Propagation Verified: {ctx}")

    # 3. Metrics Collector Verification
    mc = MetricsCollector()
    mc.record_workflow_start()
    mc.record_workflow_execution("wfk-sample-100", duration_ms=120.5, success=True, retries=1)
    summary = mc.get_summary()
    assert summary["completed_workflows"] == 1 and summary["total_retries"] == 1
    print(f"[OK] Metrics Collection Verified: {summary}")

    # 4. Logger & Performance Profiler
    logger = StructuredLogger()
    logger.info("Executed task t1 successfully", trace_id=trc1, workflow_id="wfk-sample-100", agent_name="ValidationAgent", execution_time_ms=45.0)

    profiler = PerformanceProfiler()
    profiler.profile_start("ValidationAgent")
    profiler.profile_end("ValidationAgent")

    # 5. Diagnostics Engine Samples
    diag = DiagnosticsEngine(logger=logger, metrics=mc, profiler=profiler)

    health_rep = diag.generate_platform_health_report()
    print("\n--- SAMPLE DIAGNOSTICS REPORT ---")
    print(json.dumps(health_rep, indent=2))

    # 6. Sample Execution Snapshot
    snapshot = ExecutionSnapshot.capture(
        workflow_id="wfk-sample-100",
        current_task="t2",
        completed_tasks=["t1"],
        pending_tasks=["t3"],
        agent_states={"ValidationAgent": "COMPLETED", "PredictiveAgent": "RUNNING"},
        timeline_records_count=1,
        runtime_metrics=summary,
        retry_counts={"ValidationAgent": 0},
    )
    print("\n--- SAMPLE EXECUTION SNAPSHOT ---")
    print(json.dumps(snapshot.to_dict(), indent=2))

    # 7. Sample Workflow Summary
    wf_summary = diag.generate_workflow_summary("wfk-sample-100")
    print("\n--- SAMPLE WORKFLOW SUMMARY ---")
    print(json.dumps(wf_summary, indent=2))

    print("\n[OK] ALL CHECKPOINT 8.1 VERIFICATIONS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    verify_checkpoint_8_1()
