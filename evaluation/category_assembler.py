"""AIS category assembler.

The only component allowed to build a CategoryScore. It turns the normalized
scores of one category into the immutable category score, so that no evaluator
has to assemble one itself.
"""

from __future__ import annotations

from evaluation.normalized_score import NormalizedScore
from models.category import Category
from models.category_score import CategoryScore
from models.coverage import Coverage


class CategoryAssembler:
    """Assembles one CategoryScore from normalized scores."""

    def __init__(self, category: Category, confidence: float, total_units: int) -> None:
        """Create the assembler for one category.

        Args:
            category: Category every assembled score belongs to.
            confidence: Confidence recorded on the assembled score.
            total_units: How many units of assessment the category has. For most
                categories a unit is a rule, but a category may have fewer
                dimensions than rules, or rules that measure the same thing, so
                the count is declared rather than inferred.
        """
        self._category = category
        self._confidence = confidence
        self._total_units = total_units

    def assemble(
        self, scores: tuple[NormalizedScore, ...], *, assessed: int | None = None
    ) -> CategoryScore:
        """Assemble the category score from normalized scores only.

        Placeholder aggregation: the normalized values are averaged. The AIS
        standard scale is not defined yet, so this method is the single place
        that has to change once it is. Raw measurements are never aggregated,
        and that missing scale is why a larger risk measurement currently lifts
        the overall score rather than lowering it.

        Args:
            scores: Normalized scores of the category, in rule order.
            assessed: How many units of the category were assessed. Defaults to
                the number of scores, which is right whenever a unit is a rule.
                A category whose units are not rules passes its own count.

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
            coverage=Coverage(
                assessed=len(scores) if assessed is None else assessed,
                total=self._total_units,
            ),
            summary=summary,
            evidence_references=references,
        )
