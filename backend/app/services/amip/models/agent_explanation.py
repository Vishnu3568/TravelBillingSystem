"""
AMIP Agent Explanation Model.
Represents an individual agent's contribution, confidence, execution timing, and status in an explainability report.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from app.services.amip.models.enums import AgentStatus


@dataclass
class AgentExplanation:
    """
    Detailed explanation record for one specialized agent's step within a workflow.
    """
    agent_name: str = "UnknownAgent"
    purpose: str = "General Task Execution"
    execution_time: str = ""
    confidence: float = 1.0
    status: AgentStatus = AgentStatus.SUCCESS
    input_summary: str = ""
    output_summary: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes AgentExplanation to a dictionary."""
        return {
            "agent_name": self.agent_name,
            "purpose": self.purpose,
            "execution_time": self.execution_time,
            "confidence": float(self.confidence),
            "status": self.status.value if isinstance(self.status, AgentStatus) else str(self.status),
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentExplanation:
        """Constructs an AgentExplanation instance from a dictionary."""
        status_val = data.get("status", AgentStatus.SUCCESS)
        if isinstance(status_val, str):
            try:
                status_val = AgentStatus(status_val)
            except ValueError:
                status_val = AgentStatus.SUCCESS

        return cls(
            agent_name=data.get("agent_name", "UnknownAgent"),
            purpose=data.get("purpose", "General Task Execution"),
            execution_time=data.get("execution_time", ""),
            confidence=float(data.get("confidence", 1.0)),
            status=status_val,
            input_summary=data.get("input_summary", ""),
            output_summary=data.get("output_summary", ""),
            warnings=list(data.get("warnings", [])),
            errors=list(data.get("errors", [])),
        )
