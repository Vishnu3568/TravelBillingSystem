"""
AMIP Decision Result Model.
Represents the final outcome, recommendation, and provenance of an AMIP decision process.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from app.services.amip.models.enums import DecisionStatus, DecisionPolicy
from app.services.amip.models.decision_evidence import DecisionEvidence
from app.services.amip.utils.generators import generate_trace_id, generate_workflow_id
from app.services.amip.utils.time_utils import current_utc_timestamp
import uuid


def generate_decision_id() -> str:
    """Generates a unique decision identifier."""
    return f"dec-{uuid.uuid4().hex[:12]}"


@dataclass
class DecisionResult:
    """
    Final decision evaluation DTO returned by decision engines.
    """
    decision_id: str = field(default_factory=generate_decision_id)
    trace_id: str = field(default_factory=generate_trace_id)
    workflow_id: str = field(default_factory=generate_workflow_id)
    status: DecisionStatus = DecisionStatus.PENDING
    confidence: float = 0.0
    reason: str = ""
    summary: str = ""
    recommended_action: str = ""
    policy: DecisionPolicy = DecisionPolicy.AUTO_REVIEW
    evidence: DecisionEvidence = field(default_factory=DecisionEvidence)
    created_at: str = field(default_factory=current_utc_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes DecisionResult to a dictionary."""
        return {
            "decision_id": self.decision_id,
            "trace_id": self.trace_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value if isinstance(self.status, DecisionStatus) else str(self.status),
            "confidence": float(self.confidence),
            "reason": self.reason,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
            "policy": self.policy.value if isinstance(self.policy, DecisionPolicy) else str(self.policy),
            "evidence": self.evidence.to_dict(),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DecisionResult:
        """Constructs DecisionResult from a dictionary."""
        def parse_enum(enum_cls, val, default_val):
            if isinstance(val, str):
                try:
                    return enum_cls(val)
                except ValueError:
                    return default_val
            return val or default_val

        status_val = parse_enum(DecisionStatus, data.get("status"), DecisionStatus.PENDING)
        policy_val = parse_enum(DecisionPolicy, data.get("policy"), DecisionPolicy.AUTO_REVIEW)

        evidence_data = data.get("evidence", {})
        evidence_obj = DecisionEvidence.from_dict(evidence_data) if isinstance(evidence_data, dict) else DecisionEvidence()

        return cls(
            decision_id=data.get("decision_id", generate_decision_id()),
            trace_id=data.get("trace_id", generate_trace_id()),
            workflow_id=data.get("workflow_id", generate_workflow_id()),
            status=status_val,
            confidence=float(data.get("confidence", 0.0)),
            reason=data.get("reason", ""),
            summary=data.get("summary", ""),
            recommended_action=data.get("recommended_action", ""),
            policy=policy_val,
            evidence=evidence_obj,
            created_at=data.get("created_at", current_utc_timestamp()),
        )
