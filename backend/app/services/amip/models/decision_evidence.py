"""
AMIP Decision Evidence Model.
Stores cross-engine facts, supporting/conflicting agent records, and summary telemetry.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class DecisionEvidence:
    """
    Consolidates consensus voting evidence and cross-engine telemetry summaries.
    """
    supporting_agents: List[str] = field(default_factory=list)
    conflicting_agents: List[str] = field(default_factory=list)
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    validation_summary: Dict[str, Any] = field(default_factory=dict)
    graph_summary: Dict[str, Any] = field(default_factory=dict)
    learning_summary: Dict[str, Any] = field(default_factory=dict)
    predictive_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts evidence data to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DecisionEvidence:
        """Constructs a DecisionEvidence instance from a dictionary."""
        return cls(
            supporting_agents=list(data.get("supporting_agents", [])),
            conflicting_agents=list(data.get("conflicting_agents", [])),
            confidence_breakdown=dict(data.get("confidence_breakdown", {})),
            validation_summary=dict(data.get("validation_summary", {})),
            graph_summary=dict(data.get("graph_summary", {})),
            learning_summary=dict(data.get("learning_summary", {})),
            predictive_summary=dict(data.get("predictive_summary", {})),
        )
