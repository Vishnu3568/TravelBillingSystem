"""
AMIP Decision Explanation Package export bridge.
Re-exports DecisionExplanation model from app.services.amip.models.decision_explanation.
"""
from app.services.amip.models.decision_explanation import DecisionExplanation

__all__ = ["DecisionExplanation"]
