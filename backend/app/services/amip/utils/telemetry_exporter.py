"""
AMIP Telemetry Exporter Utility.
Provides structured formatting, JSON serialization, and CSV transformations
for exporting platform observability, trace spans, and agent execution metrics.
"""
from __future__ import annotations
import io
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class TelemetryExporter:
    """
    Utility class for exporting AMIP observability datasets to standard interchange formats.
    """

    @staticmethod
    def export_logs_to_csv(logs: List[Dict[str, Any]]) -> str:
        """Converts structured telemetry logs to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Timestamp", "Level", "Workflow ID", "Trace ID",
            "Task ID", "Agent Name", "Status", "Execution Time (ms)", "Message"
        ])

        for l in logs:
            writer.writerow([
                l.get("timestamp", ""),
                l.get("level", "INFO"),
                l.get("workflow_id", ""),
                l.get("trace_id", ""),
                l.get("task_id", ""),
                l.get("agent_name", ""),
                l.get("status", ""),
                l.get("execution_time_ms", 0.0),
                l.get("message", ""),
            ])

        return output.getvalue()

    @staticmethod
    def export_spans_to_csv(spans: List[Dict[str, Any]]) -> str:
        """Converts distributed trace spans to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Span ID", "Trace ID", "Parent Span ID",
            "Name", "Start Time", "Duration (ms)", "Status"
        ])

        for s in spans:
            writer.writerow([
                s.get("span_id", ""),
                s.get("trace_id", ""),
                s.get("parent_span_id", "") or "",
                s.get("name", ""),
                s.get("start_time", ""),
                s.get("duration_ms", 0.0),
                s.get("status", "OK"),
            ])

        return output.getvalue()

    @staticmethod
    def generate_performance_summary(
        workflows: List[Dict[str, Any]],
        logs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generates statistical runtime KPIs from workflow and log collections."""
        total_workflows = len(workflows)
        completed = sum(1 for w in workflows if w.get("status") == "COMPLETED")
        reviews = sum(1 for w in workflows if w.get("status") == "REVIEW_REQUIRED")
        failed = sum(1 for w in workflows if w.get("status") in ("FAILED", "STALE_TERMINATED"))

        durations = [float(w.get("duration_ms", 0.0)) for w in workflows if w.get("duration_ms")]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0.0

        error_logs_count = sum(1 for l in logs if l.get("level") == "ERROR")
        warn_logs_count = sum(1 for l in logs if l.get("level") == "WARNING")

        return {
            "total_executions": total_workflows,
            "completed_count": completed,
            "review_required_count": reviews,
            "failed_count": failed,
            "success_rate_percent": round((completed / total_workflows * 100), 2) if total_workflows > 0 else 100.0,
            "avg_duration_ms": round(avg_duration, 2),
            "max_duration_ms": round(max_duration, 2),
            "total_errors_logged": error_logs_count,
            "total_warnings_logged": warn_logs_count,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
