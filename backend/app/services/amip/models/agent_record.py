"""
AMIP Agent Execution Record.
Represents an immutable record of a single agent step execution.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from app.services.amip.models.enums import AgentStatus
from app.services.amip.utils.time_utils import current_utc_timestamp, calculate_duration_ms


@dataclass
class AgentExecutionRecord:
    """
    Represents the execution metadata and outcome of a single specialized agent.
    """
    agent_name: str
    start_time: str = field(default_factory=current_utc_timestamp)
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    status: AgentStatus = AgentStatus.EXECUTING
    confidence: float = 1.0
    input_summary: str = ""
    output_summary: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def complete(
        self,
        status: AgentStatus = AgentStatus.SUCCESS,
        confidence: float = 1.0,
        output_summary: str = "",
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> AgentExecutionRecord:
        """Marks the execution step as complete and calculates duration."""
        self.end_time = current_utc_timestamp()
        self.duration_ms = calculate_duration_ms(self.start_time, self.end_time)
        self.status = status
        self.confidence = confidence
        self.output_summary = output_summary
        if warnings:
            self.warnings.extend(warnings)
        if errors:
            self.errors.extend(errors)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record to a dictionary representation."""
        data = asdict(self)
        data["status"] = self.status.value if isinstance(self.status, AgentStatus) else str(self.status)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentExecutionRecord:
        """Constructs an AgentExecutionRecord from a dictionary."""
        status_val = data.get("status", AgentStatus.SUCCESS.value)
        if isinstance(status_val, str):
            try:
                status_enum = AgentStatus(status_val)
            except ValueError:
                status_enum = AgentStatus.SUCCESS
        else:
            status_enum = status_val

        return cls(
            agent_name=data.get("agent_name", "UnknownAgent"),
            start_time=data.get("start_time", current_utc_timestamp()),
            end_time=data.get("end_time"),
            duration_ms=float(data.get("duration_ms", 0.0)),
            status=status_enum,
            confidence=float(data.get("confidence", 1.0)),
            input_summary=data.get("input_summary", ""),
            output_summary=data.get("output_summary", ""),
            warnings=list(data.get("warnings", [])),
            errors=list(data.get("errors", [])),
        )
