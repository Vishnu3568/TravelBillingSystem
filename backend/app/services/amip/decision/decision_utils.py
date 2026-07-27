"""
AMIP Decision Utilities.
Provides weighted confidence calculators, vote tallies, and majority voting helpers.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from app.services.amip.models.agent_vote import AgentVote


def calculate_weighted_confidence(
    votes: List[AgentVote],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculates the normalized overall weighted confidence rating from a list of AgentVotes.
    If custom weights dictionary is not provided, all agents are assigned equal weight (1.0).
    """
    if not votes:
        return 0.0

    weights = weights or {}
    total_weighted_confidence = 0.0
    total_weights = 0.0

    for vote in votes:
        w = max(0.0, float(weights.get(vote.agent_name, 1.0)))
        total_weighted_confidence += vote.confidence * w
        total_weights += w

    if total_weights == 0.0:
        return 0.0

    return max(0.0, min(1.0, total_weighted_confidence / total_weights))


def weighted_vote_tally(
    votes: List[AgentVote],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Tallies weighted score for each unique vote choice.
    Score for a vote = sum(vote.confidence * agent_weight).
    """
    if not votes:
        return {}

    weights = weights or {}
    tally: Dict[str, float] = defaultdict(float)

    for vote in votes:
        if not vote.vote:
            continue
        w = max(0.0, float(weights.get(vote.agent_name, 1.0)))
        tally[vote.vote] += vote.confidence * w

    return dict(tally)


def calculate_majority_vote(
    votes: List[AgentVote],
    weights: Optional[Dict[str, float]] = None
) -> Tuple[Optional[str], float]:
    """
    Determines the winning majority vote option and its relative share of the overall score.
    Returns Tuple[winning_vote_option, relative_share_float].
    Returns (None, 0.0) if no valid votes exist.
    """
    tally = weighted_vote_tally(votes, weights)
    if not tally:
        return (None, 0.0)

    total_score = sum(tally.values())
    if total_score == 0.0:
        return (None, 0.0)

    # Find highest scoring vote
    winning_vote = max(tally.items(), key=lambda x: x[1])
    share = winning_vote[1] / total_score

    return (winning_vote[0], round(share, 4))
