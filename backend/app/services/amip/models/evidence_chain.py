"""
AMIP Evidence Chain Model.
Aggregates supporting evidence, conflicting evidence, missing evidence, validation notes, and cross-engine references.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class EvidenceChain:
    """
    Structured container storing multi-agent evidence artifacts across domain engines.
    """
    supporting_evidence: List[str] = field(default_factory=list)
    conflicting_evidence: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    validation_notes: List[str] = field(default_factory=list)
    graph_references: Dict[str, Any] = field(default_factory=dict)
    learning_references: Dict[str, Any] = field(default_factory=dict)
    predictive_references: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes EvidenceChain to dictionary."""
        return {
            "supporting_evidence": list(self.supporting_evidence),
            "conflicting_evidence": list(self.conflicting_evidence),
            "missing_evidence": list(self.missing_evidence),
            "validation_notes": list(self.validation_notes),
            "graph_references": dict(self.graph_references),
            "learning_references": dict(self.learning_references),
            "predictive_references": dict(self.predictive_references),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceChain:
        """Constructs EvidenceChain instance from a dictionary."""
        return cls(
            supporting_evidence=list(data.get("supporting_evidence", [])),
            conflicting_evidence=list(data.get("conflicting_evidence", [])),
            missing_evidence=list(data.get("missing_evidence", [])),
            validation_notes=list(data.get("validation_notes", [])),
            graph_references=dict(data.get("graph_references", {})),
            learning_references=dict(data.get("learning_references", {})),
            predictive_references=dict(data.get("predictive_references", {})),
        )
