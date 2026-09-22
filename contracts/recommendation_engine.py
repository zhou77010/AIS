"""Contract for the recommendation engine.

The recommendation engine expresses a Decision in the form its consumers read. A
Recommendation is not a second judgement: it is the Decision under the name Portfolio
and
the report use, holding the answer, its grounds and its evidence, and adding nothing the
Decision does not contain. This module defines the interface only.
"""

from __future__ import annotations

from typing import Protocol

from models.decision_result import DecisionResult
from models.recommendation import Recommendation


class RecommendationEngine(Protocol):
    """Contract for the component that expresses a Decision outward."""

    def recommend(
        self, decision: DecisionResult, *, confidence: float
    ) -> Recommendation:
        """Return the Recommendation that expresses one Decision.

        Args:
            decision: The Decision reached for the asset.
            confidence: Confidence carried from the judgements the Decision rests on. It
                is carried and never computed here: the aggregation of confidence is
                deferred by the Constitution, and an invented aggregate would be a
                number
                nobody reached.

        Returns:
            The Recommendation, holding the Decision's answer, grounds and evidence.
        """
