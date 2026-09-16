"""AIS category score domain model.

A category score is what one category says about an asset, together with the
evidence that supports it and how much of the category was actually assessed.
The score itself is not computed here.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.category import Category
from models.coverage import Coverage


@dataclass(frozen=True)
class CategoryScore:
    """What one category says about an asset.

    Attributes:
        category: Category being scored.
        score: Score assigned to the category.
        confidence: Confidence in the score, from 0.0 to 1.0.
        coverage: How much of the category was actually assessed.
        summary: Short explanation of what the score says.
        evidence_references: Identifiers of the evidence supporting the score.
    """

    category: Category
    score: float
    confidence: float
    coverage: Coverage
    summary: str
    evidence_references: tuple[str, ...]
