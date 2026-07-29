"""
AMIP Planning Policy Model.
Defines policy constraints for plan validation, scheduling order, and retry rules.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class PlanningPolicy:
    """
    Policy options controlling planning behavior and task execution rules.
    """
    strict_order: bool = True
    allow_parallel: bool = False
    retry_failed_tasks: bool = True
    require_human_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes PlanningPolicy to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PlanningPolicy:
        """Constructs a PlanningPolicy instance from a dictionary."""
        return cls(
            strict_order=bool(data.get("strict_order", True)),
            allow_parallel=bool(data.get("allow_parallel", False)),
            retry_failed_tasks=bool(data.get("retry_failed_tasks", True)),
            require_human_review=bool(data.get("require_human_review", False)),
        )
