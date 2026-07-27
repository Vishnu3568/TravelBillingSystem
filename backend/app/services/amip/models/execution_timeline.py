"""
AMIP Execution Timeline.
Manages an ordered list of AgentExecutionRecords with aggregation helpers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.services.amip.models.agent_record import AgentExecutionRecord


@dataclass
class ExecutionTimeline:
    """
    Chronological ledger of agent executions within a workflow task.
    """
    records: List[AgentExecutionRecord] = field(default_factory=list)

    def append(self, record: AgentExecutionRecord) -> None:
        """Appends a new AgentExecutionRecord to the timeline."""
        self.records.append(record)

    def latest(self) -> Optional[AgentExecutionRecord]:
        """Returns the most recent AgentExecutionRecord, or None if timeline is empty."""
        if not self.records:
            return None
        return self.records[-1]

    def duration(self) -> float:
        """Calculates total accumulated execution duration in milliseconds across all records."""
        return sum(r.duration_ms for r in self.records)

    def summary(self) -> Dict[str, Any]:
        """Generates a structured summary report of all timeline agent executions."""
        return {
            "total_agents_executed": len(self.records),
            "total_duration_ms": self.duration(),
            "latest_agent": self.latest().agent_name if self.latest() else None,
            "agent_statuses": {r.agent_name: r.status.value for r in self.records},
            "warnings_count": sum(len(r.warnings) for r in self.records),
            "errors_count": sum(len(r.errors) for r in self.records),
        }

    def to_list(self) -> List[Dict[str, Any]]:
        """Serializes the timeline records to a list of dictionaries."""
        return [r.to_dict() for r in self.records]

    @classmethod
    def from_list(cls, record_list: List[Dict[str, Any]]) -> ExecutionTimeline:
        """Constructs an ExecutionTimeline from a list of dictionaries."""
        timeline = cls()
        for item in record_list:
            timeline.append(AgentExecutionRecord.from_dict(item))
        return timeline
