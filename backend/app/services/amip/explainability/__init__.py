"""
AMIP Explainability Package.
Exports ExplainabilityReport, AgentExplanation, EvidenceChain, DecisionExplanation,
TimelineRenderer, ExecutionNarrator, ExplainabilityEngine, and utility functions.
"""
from app.services.amip.models.explainability_report import ExplainabilityReport, generate_report_id
from app.services.amip.models.agent_explanation import AgentExplanation
from app.services.amip.models.evidence_chain import EvidenceChain
from app.services.amip.explainability.decision_explanation import DecisionExplanation
from app.services.amip.explainability.timeline_renderer import TimelineRenderer
from app.services.amip.explainability.execution_narrator import ExecutionNarrator
from app.services.amip.explainability.explainability_engine import ExplainabilityEngine
from app.services.amip.explainability.explainability_utils import (
    format_confidence,
    format_timeline,
    summarize_execution,
    format_evidence_summary,
)

__all__ = [
    "ExplainabilityReport",
    "generate_report_id",
    "AgentExplanation",
    "EvidenceChain",
    "DecisionExplanation",
    "TimelineRenderer",
    "ExecutionNarrator",
    "ExplainabilityEngine",
    "format_confidence",
    "format_timeline",
    "summarize_execution",
    "format_evidence_summary",
]
