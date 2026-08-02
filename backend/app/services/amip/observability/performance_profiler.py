"""
AMIP Performance Profiler.
Measures latency profiles across planner, supervisor, decision matrix, adapters, and agent steps.
"""
from __future__ import annotations
import time
import threading
from typing import Dict, Any, List, Optional
from app.services.amip.interfaces.observability_interfaces import IPerformanceProfiler


class PerformanceProfiler(IPerformanceProfiler):
    """
    High-precision latency measurement profiler for AMIP components.
    """

    def __init__(self):
        self._start_times: Dict[str, float] = {}
        self._latencies: Dict[str, List[float]] = {}
        self._lock: threading.RLock = threading.RLock()

    def profile_start(self, name: str) -> None:
        """Starts timing a component execution block (thread-safe)."""
        with self._lock:
            self._start_times[name] = time.perf_counter()

    def profile_end(self, name: str) -> float:
        """Stops timing a component execution block and records latency in ms (thread-safe)."""
        with self._lock:
            start_t = self._start_times.pop(name, None)
            if start_t is None:
                return 0.0

            dur_ms = round((time.perf_counter() - start_t) * 1000, 2)
            if name not in self._latencies:
                self._latencies[name] = []
            self._latencies[name].append(dur_ms)
            return dur_ms

    def get_latency_report(self) -> Dict[str, Any]:
        """Generates latency statistics report grouped by component (thread-safe)."""
        with self._lock:
            report: Dict[str, Any] = {}
            for name, list_dur in self._latencies.items():
                if list_dur:
                    avg_d = round(sum(list_dur) / len(list_dur), 2)
                    max_d = round(max(list_dur), 2)
                    min_d = round(min(list_dur), 2)
                    report[name] = {
                        "invocations": len(list_dur),
                        "average_ms": avg_d,
                        "max_ms": max_d,
                        "min_ms": min_d,
                    }
            return report
