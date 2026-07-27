"""
AMIP Agent Vote Model.
Represents an individual specialized agent's evaluation, vote, and confidence rating.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from app.services.amip.utils.time_utils import current_utc_timestamp


@dataclass
class AgentVote:
    """
    Represents one agent's vote or recommendation during decision consensus.
    """
    agent_name: str
    confidence: float
    vote: str
    reason: str = ""
    execution_time: str = field(default_factory=current_utc_timestamp)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Bound confidence between 0.0 and 1.0
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    def to_dict(self) -> Dict[str, Any]:
        """Converts the vote instance to a dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentVote:
        """Constructs an AgentVote instance from a dictionary."""
        return cls(
            agent_name=data.get("agent_name", "UnknownAgent"),
            confidence=float(data.get("confidence", 0.0)),
            vote=data.get("vote", ""),
            reason=data.get("reason", ""),
            execution_time=data.get("execution_time", current_utc_timestamp()),
            warnings=list(data.get("warnings", [])),
        )
