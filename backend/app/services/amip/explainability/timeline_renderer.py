"""
AMIP Timeline Renderer.
Renders execution timeline data structures into chronological audit maps, durations, and critical path traces.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from app.services.amip.interfaces.explainability_interfaces import ITimelineRenderer
from app.services.amip.explainability.explainability_utils import format_timeline
from app.services.amip.utils.time_utils import calculate_duration_ms
from app.services.amip.exceptions import TimelineGenerationError


class TimelineRenderer(ITimelineRenderer):
    """
    Renders ExecutionTimeline records into structured metrics, critical paths, and idle timing.
    """

    def render_timeline(self, timeline: Any) -> Dict[str, Any]:
        """
        Renders an ExecutionTimeline instance.
        Returns Dict with keys: events, task_start_times, task_finish_times, task_durations,
        total_duration_ms, idle_time_ms, critical_path, formatted_str.
        """
        if not timeline:
            return {
                "events": [],
                "task_start_times": {},
                "task_finish_times": {},
                "task_durations": {},
                "total_duration_ms": 0.0,
                "idle_time_ms": 0.0,
                "critical_path": [],
                "formatted_str": "No timeline provided.",
            }

        try:
            records = getattr(timeline, "records", []) if hasattr(timeline, "records") else list(timeline)
            events: List[Dict[str, Any]] = []
            task_start_times: Dict[str, str] = {}
            task_finish_times: Dict[str, str] = {}
            task_durations: Dict[str, float] = {}
            critical_path: List[str] = []

            last_end_ts: Optional[str] = None
            total_idle_ms: float = 0.0

            for rec in records:
                agent_name = getattr(rec, "agent_name", "UnknownAgent")
                start_ts = getattr(rec, "start_time", "")
                end_ts = getattr(rec, "end_time", "")
                dur = getattr(rec, "duration_ms", 0.0)

                task_start_times[agent_name] = start_ts
                task_finish_times[agent_name] = end_ts
                task_durations[agent_name] = float(dur)
                critical_path.append(agent_name)

                # Calculate idle gap if consecutive
                if last_end_ts and start_ts:
                    gap_ms = calculate_duration_ms(last_end_ts, start_ts)
                    if gap_ms > 0:
                        total_idle_ms += gap_ms
                if end_ts:
                    last_end_ts = end_ts

                events.append({
                    "agent_name": agent_name,
                    "start_time": start_ts,
                    "end_time": end_ts,
                    "duration_ms": float(dur),
                    "status": getattr(rec, "status", "UNKNOWN"),
                    "confidence": float(getattr(rec, "confidence", 1.0)),
                })

            total_dur = sum(task_durations.values()) + total_idle_ms
            formatted_str = format_timeline(records)

            return {
                "events": events,
                "task_start_times": task_start_times,
                "task_finish_times": task_finish_times,
                "task_durations": task_durations,
                "total_duration_ms": round(total_dur, 2),
                "idle_time_ms": round(total_idle_ms, 2),
                "critical_path": critical_path,
                "formatted_str": formatted_str,
            }

        except Exception as err:
            wf_id = getattr(timeline, "workflow_id", "unknown_wf") if hasattr(timeline, "workflow_id") else "unknown_wf"
            raise TimelineGenerationError(wf_id, str(err))
