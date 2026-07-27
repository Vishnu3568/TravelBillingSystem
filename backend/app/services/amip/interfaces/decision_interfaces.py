"""
AMIP Decision Abstract Interfaces.
Defines contracts for DecisionEngine, DecisionPolicy, and DecisionMatrix components.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from app.services.amip.models.agent_vote import AgentVote
from app.services.amip.models.enums import DecisionStatus, DecisionPolicy


class IDecisionMatrix(ABC):
    """Abstract interface contract for DecisionMatrix."""

    @abstractmethod
    def add_vote(self, vote: AgentVote) -> None:
        pass

    @abstractmethod
    def remove_vote(self, agent_name: str) -> bool:
        pass

    @abstractmethod
    def calculate_confidence(self, weights: Optional[Dict[str, float]] = None) -> float:
        pass

    @abstractmethod
    def highest_confidence(self) -> Optional[AgentVote]:
        pass

    @abstractmethod
    def majority_vote(self, weights: Optional[Dict[str, float]] = None) -> Optional[str]:
        pass

    @abstractmethod
    def conflicts(self) -> List[Tuple[AgentVote, AgentVote]]:
        pass

    @abstractmethod
    def summary(self, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        pass


class IDecisionPolicy(ABC):
    """Abstract interface contract for decision policy evaluators."""

    @abstractmethod
    def evaluate_policy(self, matrix: IDecisionMatrix) -> DecisionPolicy:
        pass


class IDecisionEngine(ABC):
    """Abstract interface contract for AMIP Decision Engine."""

    @abstractmethod
    def evaluate_decision(
        self,
        matrix: IDecisionMatrix,
        context: Any,
        policy: Optional[DecisionPolicy] = None
    ) -> Any:
        pass
