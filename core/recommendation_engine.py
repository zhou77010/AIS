"""AIS recommendation engine.

Turns an overall assessment into the recommendation for an asset. The current
implementation is a placeholder: it maps the overall score onto a decision state
through a temporary table and defines no investment methodology.

Placeholder only. Real thresholds belong to Constitution.
"""

from __future__ import annotations

from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

# Placeholder only. Real thresholds belong to Constitution.
_PLACEHOLDER_BANDS = (
    (80.0, DecisionState.BUY),
    (60.0, DecisionState.ACCUMULATE),
    (40.0, DecisionState.HOLD),
)
_PLACEHOLDER_FALLBACK_STATE = DecisionState.WATCH


def _decision_state_for(score: float) -> DecisionState:
    """Return the placeholder decision state for an overall score."""
    for threshold, state in _PLACEHOLDER_BANDS:
        if score >= threshold:
            return state
    return _PLACEHOLDER_FALLBACK_STATE


class RecommendationEngine:
    """Turns an overall assessment into a recommendation."""

    def recommend(self, assessment: OverallAssessment) -> Recommendation:
        """Derive the recommendation from the overall assessment.

        Placeholder only: the decision state comes from a temporary score table
        and the thesis states that fact. Real thresholds belong to Constitution.
        The evidence references of every category score are merged and carried
        forward, so the conclusion stays explainable.

        Args:
            assessment: Overall assessment of the asset.

        Returns:
            Recommendation drawn from the assessment.
        """
        references = tuple(
            dict.fromkeys(
                reference
                for category_score in assessment.category_scores
                for reference in category_score.evidence_references
            )
        )
        return Recommendation(
            decision_state=_decision_state_for(assessment.overall_score),
            confidence=assessment.confidence,
            investment_thesis=(
                f"Placeholder decision from overall score "
                f"{assessment.overall_score:.2f}; real scoring belongs to the "
                "Constitution."
            ),
            evidence_references=references,
        )
