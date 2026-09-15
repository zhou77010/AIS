"""AIS overall assessment domain model.

The overall assessment is the whole picture of an asset: every category score
and the score and grade that summarise them. It is a pure analysis result: the
recommendation derived from it is a separate, downstream object.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.category_score import CategoryScore


@dataclass(frozen=True)
class OverallAssessment:
    """Whole picture of an asset, built from its category scores.

    Attributes:
        overall_score: Score summarising the asset across all categories.
        confidence: Confidence in the assessment, from 0.0 to 1.0.
        grade: Grade label that summarises the assessment.
        category_scores: Category scores the assessment is built from.
    """

    overall_score: float
    confidence: float
    grade: str
    category_scores: tuple[CategoryScore, ...]
