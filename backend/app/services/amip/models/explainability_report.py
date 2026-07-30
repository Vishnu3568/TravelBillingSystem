"""
AMIP Explainability Report DTO.
Comprehensive audit container synthesizing execution state, timeline rendering, agent explanations, evidence chain, and human narrative.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.services.amip.models.enums import ExecutionStatus
from app.services.amip.models.agent_explanation import AgentExplanation
from app.services.amip.models.evidence_chain import EvidenceChain
from app.services.amip.models.decision_explanation import DecisionExplanation
from app.services.amip.utils.time_utils import current_utc_timestamp
import uuid


def generate_report_id() -> str:
    """Generates a unique explainability report identifier."""
    return f"rep-{uuid.uuid4().hex[:12]}"


@dataclass
class ExplainabilityReport:
    """
    Comprehensive explainability report DTO for enterprise auditing and user transparency.
    """
    report_id: str = field(default_factory=generate_report_id)
    trace_id: str = ""
    workflow_id: str = ""
    generated_at: str = field(default_factory=current_utc_timestamp)
    overall_status: ExecutionStatus = ExecutionStatus.COMPLETED
    overall_confidence: float = 1.0
    execution_duration_ms: float = 0.0
    decision_summary: str = "Workflow completed successfully."
    recommendation: str = "AUTO_APPROVE"
    agent_explanations: List[AgentExplanation] = field(default_factory=list)
    evidence_chain: EvidenceChain = field(default_factory=EvidenceChain)
    decision_explanation: DecisionExplanation = field(default_factory=DecisionExplanation)
    timeline_summary: Dict[str, Any] = field(default_factory=dict)
    narrative_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ExplainabilityReport to dictionary."""
        return {
            "report_id": self.report_id,
            "trace_id": self.trace_id,
            "workflow_id": self.workflow_id,
            "generated_at": self.generated_at,
            "overall_status": self.overall_status.value if isinstance(self.overall_status, ExecutionStatus) else str(self.overall_status),
            "overall_confidence": float(self.overall_confidence),
            "execution_duration_ms": float(self.execution_duration_ms),
            "decision_summary": self.decision_summary,
            "recommendation": self.recommendation,
            "agent_explanations": [a.to_dict() for a in self.agent_explanations],
            "evidence_chain": self.evidence_chain.to_dict(),
            "decision_explanation": self.decision_explanation.to_dict(),
            "timeline_summary": dict(self.timeline_summary),
            "narrative_summary": self.narrative_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExplainabilityReport:
        """Constructs ExplainabilityReport from dictionary."""
        status_val = data.get("overall_status", ExecutionStatus.COMPLETED)
        if isinstance(status_val, str):
            try:
                status_val = ExecutionStatus(status_val)
            except ValueError:
                status_val = ExecutionStatus.COMPLETED

        agents_raw = data.get("agent_explanations", [])
        agent_exps = [AgentExplanation.from_dict(a) for a in agents_raw] if isinstance(agents_raw, list) else []

        ev_raw = data.get("evidence_chain", {})
        ev_obj = EvidenceChain.from_dict(ev_raw) if isinstance(ev_raw, dict) else EvidenceChain()

        dec_raw = data.get("decision_explanation", {})
        dec_obj = DecisionExplanation.from_dict(dec_raw) if isinstance(dec_raw, dict) else DecisionExplanation()

        return cls(
            report_id=data.get("report_id", generate_report_id()),
            trace_id=data.get("trace_id", ""),
            workflow_id=data.get("workflow_id", ""),
            generated_at=data.get("generated_at", current_utc_timestamp()),
            overall_status=status_val,
            overall_confidence=float(data.get("overall_confidence", 1.0)),
            execution_duration_ms=float(data.get("execution_duration_ms", 0.0)),
            decision_summary=data.get("decision_summary", "Workflow completed successfully."),
            recommendation=data.get("recommendation", "AUTO_APPROVE"),
            agent_explanations=agent_exps,
            evidence_chain=ev_obj,
            decision_explanation=dec_obj,
            timeline_summary=dict(data.get("timeline_summary", {})),
            narrative_summary=data.get("narrative_summary", ""),
        )
