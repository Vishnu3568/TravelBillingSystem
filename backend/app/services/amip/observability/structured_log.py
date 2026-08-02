"""
AMIP Structured Log Record.
Represents a structured telemetry log record with context, trace details, level, and metadata.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from app.services.amip.utils.time_utils import current_utc_timestamp


@dataclass
class StructuredLogRecord:
    """
    Immutable structured log record capturing execution state, metadata, and tracing markers.
    """
    message: str
    level: str = "INFO"
    timestamp: str = field(default_factory=current_utc_timestamp)
    trace_id: str = ""
    workflow_id: str = ""
    task_id: str = ""
    agent_name: str = ""
    execution_time_ms: float = 0.0
    status: str = "COMPLETED"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes log record to dictionary representation."""
        return asdict(self)

    def to_json(self) -> str:
        """Serializes log record to JSON string representation."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StructuredLogRecord:
        """Constructs StructuredLogRecord instance from dictionary."""
        return cls(
            message=data.get("message", ""),
            level=data.get("level", "INFO"),
            timestamp=data.get("timestamp", current_utc_timestamp()),
            trace_id=data.get("trace_id", ""),
            workflow_id=data.get("workflow_id", ""),
            task_id=data.get("task_id", ""),
            agent_name=data.get("agent_name", ""),
            execution_time_ms=float(data.get("execution_time_ms", 0.0)),
            status=data.get("status", "COMPLETED"),
            metadata=dict(data.get("metadata", {})),
        )
