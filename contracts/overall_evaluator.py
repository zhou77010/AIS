"""Contract for the overall evaluator.

The overall evaluator consumes the assessment of every category and assembles
the overall assessment of the asset. This module defines the interface only.
"""

from __future__ import annotations

from typing import Protocol

from models.category_score import CategoryScore
from models.overall_assessment import OverallAssessment


class OverallEvaluator(Protocol):
    """Contract for the component that assembles the overall assessment."""

    def evaluate(self, category_scores: tuple[CategoryScore, ...]) -> OverallAssessment:
        """Assemble the overall assessment from category scores.

        Args:
            category_scores: Assessments of every category for the asset.

        Returns:
            Overall assessment built from the category scores.
        """
