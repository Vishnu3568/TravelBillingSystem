"""
AMIP Explainability Abstract Interfaces.
Defines contracts for ExplainabilityEngine, TimelineRenderer, and ExecutionNarrator components.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ITimelineRenderer(ABC):
    """Abstract interface contract for TimelineRenderer."""

    @abstractmethod
    def render_timeline(self, timeline: Any) -> Dict[str, Any]:
        """Renders an ExecutionTimeline into a structured dictionary layout."""
        pass


class IExecutionNarrator(ABC):
    """Abstract interface contract for ExecutionNarrator."""

    @abstractmethod
    def generate_narrative(
        self,
        context: Any,
        plan: Optional[Any] = None,
        decision: Optional[Any] = None,
    ) -> str:
        """Generates a human-readable text explanation for a workflow execution."""
        pass


class IExplainabilityEngine(ABC):
    """Abstract interface contract for ExplainabilityEngine."""

    @abstractmethod
    def generate_report(
        self,
        context: Any,
        plan: Optional[Any] = None,
        state: Optional[Any] = None,
        decision: Optional[Any] = None,
    ) -> Any:
        """Compiles a complete ExplainabilityReport DTO."""
        pass
