"""AIS overall assessment domain model.

The overall assessment is the whole picture of an asset: every category score,
the score and grade that summarise them, and the recommendation drawn from it.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.category_score import CategoryScore
from models.recommendation import Recommendation


@dataclass(frozen=True)
class OverallAssessment:
    """Whole picture of an asset, built from its category scores.

    Attributes:
        overall_score: Score summarising the asset across all categories.
        confidence: Confidence in the assessment, from 0.0 to 1.0.
        grade: Grade label that summarises the assessment.
        recommendation: Recommendation drawn from the assessment.
        category_scores: Category scores the assessment is built from.
    """

    overall_score: float
    confidence: float
    grade: str
    recommendation: Recommendation
    category_scores: tuple[CategoryScore, ...]
