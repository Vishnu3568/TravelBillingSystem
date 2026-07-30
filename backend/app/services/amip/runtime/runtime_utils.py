"""
AMIP Runtime Utilities.
Provides health report formatting and runtime summary diagnostic text generators.
"""
from __future__ import annotations
from typing import Dict, Any
from app.services.amip.resilience.resilience_utils import calculate_success_rate, calculate_failure_rate


def format_health_report(health_summary: Dict[str, Any]) -> str:
    """Formats an executor health dictionary into an ASCII report string."""
    if not health_summary:
        return "No health telemetry available."

    lines: list[str] = ["=== AMIP Health Status Report ==="]
    total_exec = health_summary.get("total_executors", 0)
    healthy_cnt = health_summary.get("healthy_count", 0)

    lines.append(f"Overall Status: {health_summary.get('overall_status', 'UNKNOWN')}")
    lines.append(f"Executors Registered: {total_exec} | Healthy: {healthy_cnt}")

    executors = health_summary.get("executors", {})
    if isinstance(executors, dict):
        for name, details in executors.items():
            st = details.get("status", "HEALTHY")
            hb = details.get("last_heartbeat", "N/A")
            fails = details.get("failure_count", 0)
            recs = details.get("recovery_count", 0)
            lines.append(f"  - [{name}] Status: {st} | Heartbeat: {hb} | Failures: {fails} | Recoveries: {recs}")

    return "\n".join(lines)


def build_runtime_summary(metrics_summary: Dict[str, Any]) -> str:
    """Builds a human-readable runtime diagnostics summary from telemetry metrics."""
    if not metrics_summary:
        return "No runtime metrics recorded."

    total_wf = metrics_summary.get("total_workflows", 0)
    succ_wf = metrics_summary.get("successful_workflows", 0)
    fail_wf = metrics_summary.get("failed_workflows", 0)
    succ_rate = metrics_summary.get("success_rate", 100.0)
    avg_dur = metrics_summary.get("average_execution_duration_ms", 0.0)
    retries = metrics_summary.get("retry_count", 0)
    timeouts = metrics_summary.get("timeout_count", 0)
    cancels = metrics_summary.get("cancellation_count", 0)

    return (
        f"=== AMIP Runtime Diagnostics ===\n"
        f"Workflows Processed: {total_wf} (Passed: {succ_wf}, Failed: {fail_wf})\n"
        f"Success Rate: {succ_rate:.2f}% | Avg Duration: {avg_dur:.2f}ms\n"
        f"Retries: {retries} | Timeouts: {timeouts} | Cancellations: {cancels}"
    )
