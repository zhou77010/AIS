"""AIS category assembler.

The only component allowed to build a CategoryScore. It turns the normalized
scores of one category into the immutable category score, so that no evaluator
has to assemble one itself.
"""

from __future__ import annotations

from evaluation.normalized_score import NormalizedScore
from models.category import Category
from models.category_score import CategoryScore


class CategoryAssembler:
    """Assembles one CategoryScore from normalized scores."""

    def __init__(self, category: Category, confidence: float) -> None:
        """Create the assembler for one category.

        Args:
            category: Category every assembled score belongs to.
            confidence: Confidence recorded on the assembled score.
        """
        self._category = category
        self._confidence = confidence

    def assemble(self, scores: tuple[NormalizedScore, ...]) -> CategoryScore:
        """Assemble the category score from normalized scores only.

        Placeholder aggregation: the normalized values are averaged. The AIS
        standard scale is not defined yet, so this method is the single place
        that has to change once it is. Raw measurements are never aggregated.

        Args:
            scores: Normalized scores of the category, in rule order.

        Returns:
            Immutable CategoryScore for the configured category.
        """
        values = tuple(entry.normalized_value for entry in scores)
        aggregated_score = sum(values) / len(values) if values else 0.0
        summary = "; ".join(entry.reason for entry in scores)
        references = tuple(
            dict.fromkeys(
                reference for entry in scores for reference in entry.evidence_references
            )
        )
        return CategoryScore(
            category=self._category,
            score=aggregated_score,
            confidence=self._confidence,
            summary=summary,
            evidence_references=references,
        )
