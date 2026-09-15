"""AIS overall evaluator.

Builds the overall assessment of an asset from its category scores. The current
implementation is a placeholder: it defines no investment methodology.
"""

from __future__ import annotations

from models.category_score import CategoryScore
from models.overall_assessment import OverallAssessment

_PLACEHOLDER_CONFIDENCE = 1.0
_PLACEHOLDER_GRADE = "PLACEHOLDER"


class OverallEvaluator:
    """Assembles the overall assessment from the category scores."""

    def evaluate(self, category_scores: tuple[CategoryScore, ...]) -> OverallAssessment:
        """Build the overall assessment from the category scores.

        Placeholder only: the overall score is the average of the category
        scores and the grade is a placeholder label. The AIS standard scale and
        the grade vocabulary belong to the Constitution.

        Args:
            category_scores: Category scores of the asset, in order.

        Returns:
            OverallAssessment built from the category scores, without a
            recommendation: the recommendation is derived from it afterwards.
        """
        scores = tuple(entry.score for entry in category_scores)
        overall_score = sum(scores) / len(scores) if scores else 0.0
        return OverallAssessment(
            overall_score=overall_score,
            confidence=_PLACEHOLDER_CONFIDENCE,
            grade=_PLACEHOLDER_GRADE,
            category_scores=category_scores,
        )
