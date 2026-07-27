"""
AMIP Decision Matrix.
Stores agent votes, evaluates consensus, detects conflicts, and computes matrix summaries.
"""
from __future__ import annotations
import threading
from typing import Dict, List, Optional, Tuple, Any
from app.services.amip.models.agent_vote import AgentVote
from app.services.amip.decision.decision_utils import (
    calculate_weighted_confidence,
    weighted_vote_tally,
    calculate_majority_vote,
)


class DecisionMatrix:
    """
    Thread-safe decision matrix evaluating agent votes, confidence weights, and conflicts.
    """

    def __init__(self, initial_votes: Optional[List[AgentVote]] = None):
        self._votes: Dict[str, AgentVote] = {}
        self._lock: threading.RLock = threading.RLock()

        if initial_votes:
            for v in initial_votes:
                self.add_vote(v)

    def add_vote(self, vote: AgentVote) -> None:
        """Adds or updates an agent vote in the matrix (thread-safe)."""
        if not vote or not vote.agent_name:
            raise ValueError("AgentVote must have a valid agent_name.")
        with self._lock:
            self._votes[vote.agent_name] = vote

    def remove_vote(self, agent_name: str) -> bool:
        """Removes an agent's vote from the matrix (thread-safe). Returns True if vote existed."""
        with self._lock:
            if agent_name in self._votes:
                del self._votes[agent_name]
                return True
            return False

    def get_vote(self, agent_name: str) -> Optional[AgentVote]:
        """Retrieves a specific agent's vote from the matrix (thread-safe)."""
        with self._lock:
            return self._votes.get(agent_name)

    def list_votes(self) -> List[AgentVote]:
        """Returns a list copy of all current agent votes in the matrix (thread-safe)."""
        with self._lock:
            return list(self._votes.values())

    def calculate_confidence(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculates the normalized overall weighted confidence across all registered votes (thread-safe)."""
        with self._lock:
            return calculate_weighted_confidence(list(self._votes.values()), weights)

    def highest_confidence(self) -> Optional[AgentVote]:
        """Returns the AgentVote instance with the highest individual confidence score (thread-safe)."""
        with self._lock:
            if not self._votes:
                return None
            return max(self._votes.values(), key=lambda v: v.confidence)

    def majority_vote(self, weights: Optional[Dict[str, float]] = None) -> Optional[str]:
        """Determines the winning majority vote option across all registered votes (thread-safe)."""
        with self._lock:
            winning_option, _ = calculate_majority_vote(list(self._votes.values()), weights)
            return winning_option

    def conflicts(self) -> List[Tuple[AgentVote, AgentVote]]:
        """
        Identifies pairs of votes that have differing vote choices with high confidence (>0.5).
        Returns a list of conflicting AgentVote tuples (thread-safe).
        """
        with self._lock:
            conflict_pairs: List[Tuple[AgentVote, AgentVote]] = []
            vote_list = list(self._votes.values())

            for i in range(len(vote_list)):
                for j in range(i + 1, len(vote_list)):
                    v1 = vote_list[i]
                    v2 = vote_list[j]
                    if v1.vote != v2.vote and v1.confidence > 0.5 and v2.confidence > 0.5:
                        conflict_pairs.append((v1, v2))

            return conflict_pairs

    def summary(self, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Generates a structured summary report of the decision matrix (thread-safe)."""
        with self._lock:
            vote_list = list(self._votes.values())
            overall_conf = calculate_weighted_confidence(vote_list, weights)
            maj_option, maj_share = calculate_majority_vote(vote_list, weights)
            highest_conf_vote = self.highest_confidence()
            conflict_pairs = self.conflicts()

            return {
                "total_votes": len(self._votes),
                "overall_confidence": round(overall_conf, 4),
                "majority_vote": maj_option,
                "majority_share": maj_share,
                "highest_confidence_agent": highest_conf_vote.agent_name if highest_conf_vote else None,
                "conflict_count": len(conflict_pairs),
                "has_conflicts": len(conflict_pairs) > 0,
                "vote_tallies": weighted_vote_tally(vote_list, weights),
            }

    def clear(self) -> None:
        """Clears all registered votes from the matrix (thread-safe)."""
        with self._lock:
            self._store.clear() if hasattr(self, "_store") else self._votes.clear()
