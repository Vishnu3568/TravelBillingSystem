"""
AMIP Explainability Utilities.
Formatting helpers for confidence scores, timelines, execution summaries, and evidence chains.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional


def format_confidence(confidence: float) -> str:
    """Formats a float confidence score (0.0 - 1.0) into a percentage string (e.g., '96.00%')."""
    bounded = max(0.0, min(1.0, float(confidence or 0.0)))
    return f"{bounded * 100.0:.2f}%"


def format_timeline(records: List[Any]) -> str:
    """Formats a list of AgentExecutionRecords into a clean ASCII/Markdown timeline text string."""
    if not records:
        return "No timeline events recorded."

    lines: List[str] = ["### Execution Timeline"]
    for i, rec in enumerate(records, start=1):
        agent_name = getattr(rec, "agent_name", "UnknownAgent")
        status = getattr(rec, "status", "UNKNOWN")
        conf = getattr(rec, "confidence", 1.0)
        dur = getattr(rec, "duration_ms", 0.0)
        out = getattr(rec, "output_summary", "")

        status_str = status.value if hasattr(status, "value") else str(status)
        conf_str = format_confidence(conf)

        lines.append(f"{i}. [{agent_name}] Status: {status_str} | Conf: {conf_str} | Duration: {dur:.1f}ms")
        if out:
            lines.append(f"   Summary: {out}")

    return "\n".join(lines)


def summarize_execution(context: Any) -> str:
    """Summarizes overall ExecutionContext status, stage, and trace ID."""
    if not context:
        return "No execution context provided."

    wf_id = getattr(context, "workflow_id", "N/A")
    status = getattr(context, "overall_status", "UNKNOWN")
    stage = getattr(context, "current_stage", "N/A")
    status_str = status.value if hasattr(status, "value") else str(status)

    return f"Workflow '{wf_id}' | Status: {status_str} | Current Stage: {stage}"


def format_evidence_summary(evidence: Any) -> str:
    """Formats an EvidenceChain or DecisionEvidence into a clean human summary string."""
    if not evidence:
        return "No evidence collected."

    sup = getattr(evidence, "supporting_evidence", []) or getattr(evidence, "supporting_agents", [])
    conf = getattr(evidence, "conflicting_evidence", []) or getattr(evidence, "conflicting_agents", [])

    sup_str = ", ".join(sup) if sup else "None"
    conf_str = ", ".join(conf) if conf else "None"

    return f"Supporting: [{sup_str}] | Conflicting: [{conf_str}]"
