"""
AMIP Decision Explanation Model.
Provides detailed justification for consensus decisions, alternative evaluation options, and policy application.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.services.amip.models.enums import DecisionPolicy


@dataclass
class DecisionExplanation:
    """
    Detailed audit explanation of why a specific decision outcome was selected by the Decision Engine.
    """
    why_decision_was_taken: str = "High confidence consensus among executing agents."
    alternative_decisions: List[str] = field(default_factory=list)
    rejected_alternatives: List[str] = field(default_factory=list)
    confidence_reasoning: str = "Weighted average confidence exceeded threshold."
    decision_policy_used: DecisionPolicy = DecisionPolicy.AUTO_APPROVE

    def to_dict(self) -> Dict[str, Any]:
        """Serializes DecisionExplanation to dictionary."""
        return {
            "why_decision_was_taken": self.why_decision_was_taken,
            "alternative_decisions": list(self.alternative_decisions),
            "rejected_alternatives": list(self.rejected_alternatives),
            "confidence_reasoning": self.confidence_reasoning,
            "decision_policy_used": self.decision_policy_used.value if isinstance(self.decision_policy_used, DecisionPolicy) else str(self.decision_policy_used),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DecisionExplanation:
        """Constructs DecisionExplanation instance from dictionary."""
        policy_val = data.get("decision_policy_used", DecisionPolicy.AUTO_APPROVE)
        if isinstance(policy_val, str):
            try:
                policy_val = DecisionPolicy(policy_val)
            except ValueError:
                policy_val = DecisionPolicy.AUTO_APPROVE

        return cls(
            why_decision_was_taken=data.get("why_decision_was_taken", "High confidence consensus among executing agents."),
            alternative_decisions=list(data.get("alternative_decisions", [])),
            rejected_alternatives=list(data.get("rejected_alternatives", [])),
            confidence_reasoning=data.get("confidence_reasoning", "Weighted average confidence exceeded threshold."),
            decision_policy_used=policy_val,
        )
