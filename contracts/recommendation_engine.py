"""Contract for the recommendation engine.

The recommendation engine consumes an overall assessment and produces the
recommendation for the asset. This module defines the interface only.
"""

from __future__ import annotations

from typing import Protocol

from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation


class RecommendationEngine(Protocol):
    """Contract for the component that turns an assessment into a recommendation."""

    def recommend(self, assessment: OverallAssessment) -> Recommendation:
        """Derive the recommendation from an overall assessment.

        Args:
            assessment: Overall assessment of the asset.

        Returns:
            Recommendation drawn from the assessment.
        """
