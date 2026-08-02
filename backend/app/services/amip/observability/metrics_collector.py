"""
AMIP Telemetry Metrics Collector.
Collects and computes operational telemetry: workflow and agent latencies, retries, failure/success counts, and active workflows.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, List, Optional
from app.services.amip.interfaces.observability_interfaces import IMetricsCollector


class MetricsCollector(IMetricsCollector):
    """
    Thread-safe operational telemetry metrics aggregator.
    """

    def __init__(self):
        self._workflow_durations: List[float] = []
        self._agent_durations: List[float] = []
        self._active_workflows: int = 0
        self._completed_workflows: int = 0
        self._failed_workflows: int = 0
        self._total_retries: int = 0
        self._lock: threading.RLock = threading.RLock()

    def record_workflow_start(self) -> None:
        """Increments active workflows counter (thread-safe)."""
        with self._lock:
            self._active_workflows += 1

    def record_workflow_execution(self, workflow_id: str, duration_ms: float, success: bool, retries: int = 0) -> None:
        """Records workflow completion telemetry (thread-safe)."""
        with self._lock:
            if self._active_workflows > 0:
                self._active_workflows -= 1
            if success:
                self._completed_workflows += 1
            else:
                self._failed_workflows += 1

            self._total_retries += max(0, retries)
            self._workflow_durations.append(float(duration_ms))

    def record_agent_execution(self, agent_name: str, duration_ms: float, success: bool) -> None:
        """Records individual agent execution latency (thread-safe)."""
        with self._lock:
            self._agent_durations.append(float(duration_ms))

    def get_summary(self) -> Dict[str, Any]:
        """Calculates statistical summary of collected telemetry metrics (thread-safe)."""
        with self._lock:
            wf_count = len(self._workflow_durations)
            avg_wf_dur = round(sum(self._workflow_durations) / wf_count, 2) if wf_count > 0 else 0.0
            max_wf_dur = round(max(self._workflow_durations), 2) if wf_count > 0 else 0.0
            min_wf_dur = round(min(self._workflow_durations), 2) if wf_count > 0 else 0.0

            ag_count = len(self._agent_durations)
            avg_ag_dur = round(sum(self._agent_durations) / ag_count, 2) if ag_count > 0 else 0.0

            total_runs = self._completed_workflows + self._failed_workflows
            succ_rate = round((self._completed_workflows / total_runs) * 100.0, 2) if total_runs > 0 else 100.0

            return {
                "active_workflows": self._active_workflows,
                "completed_workflows": self._completed_workflows,
                "failed_workflows": self._failed_workflows,
                "total_retries": self._total_retries,
                "success_rate": succ_rate,
                "average_workflow_duration_ms": avg_wf_dur,
                "max_workflow_duration_ms": max_wf_dur,
                "min_workflow_duration_ms": min_wf_dur,
                "average_agent_duration_ms": avg_ag_dur,
            }
