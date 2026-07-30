"""
Comprehensive Unit Test Suite for AMIP Runtime & Resilience Layer (Phase 9 Checkpoint 6).
Tests RetryPolicy, CircuitBreaker, TimeoutController, WorkflowCancellationToken, HealthMonitor,
RuntimeMetrics, RuntimeMonitor, Resilience/Runtime Utils, and Exceptions.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest
import time

from app.services.amip.models.enums import CircuitState
from app.services.amip.resilience.retry_policy import RetryPolicy
from app.services.amip.resilience.circuit_breaker import CircuitBreaker
from app.services.amip.resilience.resilience_utils import (
    calculate_backoff_delay,
    calculate_success_rate,
    calculate_failure_rate,
)
from app.services.amip.runtime.timeout_controller import TimeoutController
from app.services.amip.runtime.cancellation_token import WorkflowCancellationToken
from app.services.amip.runtime.health_monitor import HealthMonitor
from app.services.amip.runtime.runtime_metrics import RuntimeMetrics
from app.services.amip.runtime.runtime_monitor import RuntimeMonitor
from app.services.amip.runtime.runtime_utils import format_health_report, build_runtime_summary
from app.services.amip.exceptions import (
    RetryLimitExceeded,
    CircuitBreakerOpen,
    WorkflowCancelled,
    ExecutionTimeout,
)


# ============================================================================
# 1. RETRY POLICY TESTS
# ============================================================================
def test_retry_policy():
    """Verify RetryPolicy should_retry rules, backoff delays, and serialization."""
    policy = RetryPolicy(max_retries=3, retry_delay_ms=100.0, backoff_strategy="EXPONENTIAL")

    assert policy.should_retry(0) is True
    assert policy.should_retry(2) is True
    assert policy.should_retry(3) is False

    # Backoff calculation (attempt 1: 100ms, attempt 2: 200ms, attempt 3: 400ms)
    assert policy.next_delay(1) == 100.0
    assert policy.next_delay(2) == 200.0
    assert policy.next_delay(3) == 400.0

    # Linear & Fixed backoff tests
    pol_lin = RetryPolicy(retry_delay_ms=100.0, backoff_strategy="LINEAR")
    assert pol_lin.next_delay(2) == 200.0

    pol_fix = RetryPolicy(retry_delay_ms=100.0, backoff_strategy="FIXED")
    assert pol_fix.next_delay(3) == 100.0

    # Serialization
    d = policy.to_dict()
    assert d["max_retries"] == 3
    restored = RetryPolicy.from_dict(d)
    assert restored.max_retries == 3


# ============================================================================
# 2. CIRCUIT BREAKER TESTS
# ============================================================================
def test_circuit_breaker_transitions():
    """Verify CircuitBreaker state transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    breaker = CircuitBreaker(circuit_name="TestAgentCircuit", failure_threshold=2, recovery_timeout_ms=50.0)

    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_execution() is True

    # 1st failure -> still CLOSED
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED

    # 2nd failure -> threshold reached -> OPEN
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN

    # Execution blocked while OPEN
    with pytest.raises(CircuitBreakerOpen):
        breaker.allow_execution()

    # Sleep to exceed recovery_timeout_ms (50ms) -> transitions to HALF_OPEN
    time.sleep(0.06)
    assert breaker.state == CircuitState.HALF_OPEN

    # Record success while HALF_OPEN -> resets to CLOSED
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_execution() is True

    # Manual reset
    breaker.record_failure()
    breaker.reset()
    assert breaker.state == CircuitState.CLOSED


# ============================================================================
# 3. TIMEOUT CONTROLLER TESTS
# ============================================================================
def test_timeout_controller():
    """Verify TimeoutController deadline tracking, remaining time, and ExecutionTimeout exception."""
    controller = TimeoutController()
    controller.start_timer("task-100", timeout_ms=50.0)

    assert controller.is_timed_out("task-100") is False
    assert controller.remaining_time_ms("task-100") > 0.0

    # Sleep past deadline (50ms)
    time.sleep(0.06)
    assert controller.is_timed_out("task-100") is True

    with pytest.raises(ExecutionTimeout):
        controller.check_deadline("task-100")

    # Cancel timer
    assert controller.cancel_task("task-100") is True
    assert controller.is_timed_out("task-100") is False


# ============================================================================
# 4. WORKFLOW CANCELLATION TOKEN TESTS
# ============================================================================
def test_cancellation_token():
    """Verify WorkflowCancellationToken signal handling and WorkflowCancelled exception."""
    token = WorkflowCancellationToken(workflow_id="wfk-cancel-test")
    assert token.is_cancelled() is False

    token.cancel("Manual user cancellation")
    assert token.is_cancelled() is True
    assert token.reason() == "Manual user cancellation"

    with pytest.raises(WorkflowCancelled):
        token.throwIfCancelled()


# ============================================================================
# 5. HEALTH MONITOR TESTS
# ============================================================================
def test_health_monitor():
    """Verify HealthMonitor heartbeat tracking, failure counting, and recovery handling."""
    monitor = HealthMonitor()
    monitor.record_heartbeat("DocIntelAgent")
    monitor.record_heartbeat("ValidationAgent")

    summ1 = monitor.summary()
    assert summ1["overall_status"] == "HEALTHY"
    assert summ1["healthy_count"] == 2

    # Record 3 failures for DocIntelAgent -> becomes UNHEALTHY
    for _ in range(3):
        monitor.record_executor_failure("DocIntelAgent")

    health_doc = monitor.get_executor_health("DocIntelAgent")
    assert health_doc["status"] == "UNHEALTHY"

    summ2 = monitor.summary()
    assert summ2["overall_status"] == "DEGRADED"

    # Recover DocIntelAgent
    monitor.record_executor_recovery("DocIntelAgent")
    assert monitor.get_executor_health("DocIntelAgent")["status"] == "HEALTHY"
    assert monitor.summary()["overall_status"] == "HEALTHY"


# ============================================================================
# 6. RUNTIME METRICS & MONITOR TESTS
# ============================================================================
def test_runtime_metrics_and_monitor():
    """Verify RuntimeMetrics aggregation, RuntimeMonitor diagnostics, and report formatting."""
    metrics = RuntimeMetrics()
    metrics.record_workflow("COMPLETED", duration_ms=100.0, retries=1)
    metrics.record_workflow("FAILED", duration_ms=200.0, timeouts=1)

    assert metrics.total_workflows == 2
    assert metrics.successful_workflows == 1
    assert metrics.failed_workflows == 1
    assert metrics.success_rate == 50.0
    assert metrics.failure_rate == 50.0
    assert metrics.average_execution_duration_ms == 150.0

    monitor = RuntimeMonitor(metrics=metrics)
    stats = monitor.collect_statistics()
    assert stats["metrics"]["total_workflows"] == 2

    health_summ = monitor.generate_health_summary()
    assert "formatted_report" in health_summ

    diag = monitor.produce_diagnostics()
    assert "AMIP Runtime Diagnostics" in diag["diagnostics_summary"]


# ============================================================================
# 7. UTILITIES & EXCEPTIONS TESTS
# ============================================================================
def test_resilience_utilities_and_exceptions():
    """Verify utility functions and exception message generation."""
    assert calculate_success_rate(8, 10) == 80.0
    assert calculate_failure_rate(2, 10) == 20.0

    report_str = format_health_report({"overall_status": "HEALTHY", "total_executors": 1, "healthy_count": 1})
    assert "AMIP Health Status Report" in report_str

    diag_str = build_runtime_summary({"total_workflows": 5, "successful_workflows": 5, "success_rate": 100.0})
    assert "Workflows Processed: 5" in diag_str

    exc1 = RetryLimitExceeded("task-1", 3, "Connection timeout")
    assert "task-1" in str(exc1)

    exc2 = CircuitBreakerOpen("DocIntelCircuit")
    assert "DocIntelCircuit" in str(exc2)
