"""
Comprehensive Unit Test Suite for AMIP Decision Foundation (Phase 9 Checkpoint 2).
Tests DecisionResult, AgentVote, DecisionEvidence, DecisionMatrix, DecisionPolicy,
DecisionStatus, Exceptions, Decision Utilities, and Thread Safety.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest
import threading
from app.services.amip.models.enums import DecisionStatus, DecisionPolicy
from app.services.amip.models.agent_vote import AgentVote
from app.services.amip.models.decision_evidence import DecisionEvidence
from app.services.amip.models.decision_result import DecisionResult, generate_decision_id
from app.services.amip.decision.decision_matrix import DecisionMatrix
from app.services.amip.decision.decision_utils import (
    calculate_weighted_confidence,
    weighted_vote_tally,
    calculate_majority_vote,
)
from app.services.amip.exceptions import (
    DecisionConflict,
    DecisionFailed,
    DecisionTimeout,
)


# ============================================================================
# 1. AGENT VOTE TESTS
# ============================================================================
def test_agent_vote_creation_and_bounding():
    """Verify AgentVote creation, confidence bounding between 0.0 and 1.0, and serialization."""
    v1 = AgentVote(agent_name="LabelerAgent", confidence=0.95, vote="APPROVE", reason="High field match")
    assert v1.agent_name == "LabelerAgent"
    assert v1.confidence == 0.95
    assert v1.vote == "APPROVE"

    # Out of bounds confidence test
    v_over = AgentVote(agent_name="TestAgent", confidence=1.8, vote="APPROVE")
    assert v_over.confidence == 1.0

    v_under = AgentVote(agent_name="TestAgent", confidence=-0.5, vote="REJECT")
    assert v_under.confidence == 0.0

    # Serialization roundtrip
    d = v1.to_dict()
    assert d["agent_name"] == "LabelerAgent"
    assert d["vote"] == "APPROVE"

    restored = AgentVote.from_dict(d)
    assert restored.agent_name == v1.agent_name
    assert restored.confidence == v1.confidence
    assert restored.vote == v1.vote


# ============================================================================
# 2. DECISION EVIDENCE TESTS
# ============================================================================
def test_decision_evidence():
    """Verify DecisionEvidence initialization and serialization."""
    ev = DecisionEvidence(
        supporting_agents=["LabelerAgent", "ValidatorAgent"],
        conflicting_agents=["AnomalyAgent"],
        confidence_breakdown={"LabelerAgent": 0.92, "AnomalyAgent": 0.40},
        validation_summary={"issues_count": 0},
    )

    d = ev.to_dict()
    assert d["supporting_agents"] == ["LabelerAgent", "ValidatorAgent"]
    assert d["confidence_breakdown"]["LabelerAgent"] == 0.92

    restored = DecisionEvidence.from_dict(d)
    assert restored.supporting_agents == ev.supporting_agents
    assert restored.confidence_breakdown == ev.confidence_breakdown


# ============================================================================
# 3. DECISION RESULT TESTS
# ============================================================================
def test_decision_result_serialization():
    """Verify DecisionResult creation, enum parsing, and dictionary roundtrip."""
    dec_id = generate_decision_id()
    assert dec_id.startswith("dec-")

    res = DecisionResult(
        decision_id=dec_id,
        status=DecisionStatus.COMPLETED,
        confidence=0.89,
        reason="Consensus reached",
        summary="Auto-approved invoice processing",
        recommended_action="SAVE_TO_DATABASE",
        policy=DecisionPolicy.AUTO_APPROVE,
    )

    assert res.status == DecisionStatus.COMPLETED
    assert res.policy == DecisionPolicy.AUTO_APPROVE

    serialized = res.to_dict()
    assert serialized["decision_id"] == dec_id
    assert serialized["status"] == "COMPLETED"
    assert serialized["policy"] == "AUTO_APPROVE"

    deserialized = DecisionResult.from_dict(serialized)
    assert deserialized.decision_id == dec_id
    assert deserialized.status == DecisionStatus.COMPLETED
    assert deserialized.policy == DecisionPolicy.AUTO_APPROVE
    assert deserialized.confidence == 0.89


# ============================================================================
# 4. DECISION UTILITIES TESTS
# ============================================================================
def test_decision_utilities():
    """Verify weighted confidence calculation, vote tallying, and majority vote helpers."""
    votes = [
        AgentVote(agent_name="AgentA", confidence=0.90, vote="APPROVE"),
        AgentVote(agent_name="AgentB", confidence=0.80, vote="APPROVE"),
        AgentVote(agent_name="AgentC", confidence=0.70, vote="REJECT"),
    ]

    # Equal weighting (default 1.0 each)
    # Total weighted conf = 0.9 + 0.8 + 0.7 = 2.4 / 3 = 0.80
    conf_equal = calculate_weighted_confidence(votes)
    assert round(conf_equal, 4) == 0.8000

    # Custom weighting: AgentA weight=2.0, AgentB weight=1.0, AgentC weight=1.0
    # Total = (0.90*2 + 0.80*1 + 0.70*1) / (2+1+1) = 3.3 / 4 = 0.825
    weights = {"AgentA": 2.0, "AgentB": 1.0, "AgentC": 1.0}
    conf_custom = calculate_weighted_confidence(votes, weights)
    assert round(conf_custom, 4) == 0.8250

    # Vote tallies
    tally = weighted_vote_tally(votes, weights)
    # APPROVE score = 0.9*2 + 0.8*1 = 2.6
    # REJECT score = 0.7*1 = 0.7
    assert tally["APPROVE"] == 2.6
    assert tally["REJECT"] == 0.7

    # Majority vote
    winning_vote, share = calculate_majority_vote(votes, weights)
    assert winning_vote == "APPROVE"
    assert round(share, 4) == round(2.6 / 3.3, 4)

    # Empty votes test
    assert calculate_weighted_confidence([]) == 0.0
    assert weighted_vote_tally([]) == {}
    assert calculate_majority_vote([]) == (None, 0.0)


# ============================================================================
# 5. DECISION MATRIX TESTS
# ============================================================================
def test_decision_matrix_operations():
    """Verify DecisionMatrix vote addition, removal, highest confidence, majority, and conflicts."""
    matrix = DecisionMatrix()
    assert len(matrix.list_votes()) == 0

    v1 = AgentVote(agent_name="LabelerAgent", confidence=0.95, vote="APPROVE")
    v2 = AgentVote(agent_name="ValidatorAgent", confidence=0.90, vote="APPROVE")
    v3 = AgentVote(agent_name="AnomalyAgent", confidence=0.85, vote="REJECT")

    matrix.add_vote(v1)
    matrix.add_vote(v2)
    matrix.add_vote(v3)

    assert len(matrix.list_votes()) == 3
    assert matrix.get_vote("LabelerAgent").confidence == 0.95

    # Highest confidence
    highest = matrix.highest_confidence()
    assert highest.agent_name == "LabelerAgent"

    # Majority vote
    assert matrix.majority_vote() == "APPROVE"

    # Conflict detection (v1/v2 vote APPROVE vs v3 vote REJECT with conf > 0.5)
    conflicts = matrix.conflicts()
    assert len(conflicts) == 2  # (v1 vs v3) and (v2 vs v3)

    # Summary
    summ = matrix.summary()
    assert summ["total_votes"] == 3
    assert summ["majority_vote"] == "APPROVE"
    assert summ["has_conflicts"] is True
    assert summ["conflict_count"] == 2

    # Remove vote
    assert matrix.remove_vote("AnomalyAgent") is True
    assert len(matrix.list_votes()) == 2
    assert len(matrix.conflicts()) == 0

    # Invalid vote test
    with pytest.raises(ValueError):
        matrix.add_vote(AgentVote(agent_name="", confidence=0.5, vote="APPROVE"))


def test_decision_matrix_thread_safety():
    """Verify concurrent thread-safe operations on DecisionMatrix."""
    matrix = DecisionMatrix()
    errors = []

    def worker(thread_idx: int):
        try:
            for i in range(50):
                v = AgentVote(
                    agent_name=f"Agent_{thread_idx}_{i}",
                    confidence=0.8,
                    vote="APPROVE" if i % 2 == 0 else "REJECT",
                )
                matrix.add_vote(v)
                assert matrix.get_vote(f"Agent_{thread_idx}_{i}") is not None
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(matrix.list_votes()) == 250


# ============================================================================
# 6. DECISION EXCEPTION TESTS
# ============================================================================
def test_decision_exceptions():
    """Verify decision exception handling and error messages."""
    exc1 = DecisionConflict("dec-101", "Labeler vs Anomaly discrepancy")
    assert "dec-101" in str(exc1)
    assert "Labeler vs Anomaly" in str(exc1)

    exc2 = DecisionFailed("dec-202", "Zero votes submitted")
    assert "dec-202" in str(exc2)

    exc3 = DecisionTimeout("dec-303", 500.0)
    assert "dec-303" in str(exc3)
    assert "500.00ms" in str(exc3)
