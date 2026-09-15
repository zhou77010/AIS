"""AIS category score domain model.

A category score is what one category says about an asset, together with the
evidence that supports it. The score itself is not computed here.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.category import Category


@dataclass(frozen=True)
class CategoryScore:
    """What one category says about an asset.

    Attributes:
        category: Category being scored.
        score: Score assigned to the category.
        confidence: Confidence in the score, from 0.0 to 1.0.
        summary: Short explanation of what the score says.
        evidence_references: Identifiers of the evidence supporting the score.
    """

    category: Category
    score: float
    confidence: float
    summary: str
    evidence_references: tuple[str, ...]
