"""AIS category assembler.

The only component allowed to build a CategoryScore. It turns the successful
rule results of one category into the immutable category score, so that no
evaluator has to assemble one itself.
"""

from __future__ import annotations

from evaluation.rule_result import RuleResult
from evaluation.score_normalizer import ScoreNormalizer
from models.category import Category
from models.category_score import CategoryScore


class CategoryAssembler:
    """Assembles one CategoryScore from rule results."""

    def __init__(self, category: Category, confidence: float) -> None:
        """Create the assembler for one category.

        Args:
            category: Category every assembled score belongs to.
            confidence: Confidence recorded on the assembled score.
        """
        self._category = category
        self._confidence = confidence
        self._normalizer = ScoreNormalizer()

    def assemble(self, results: tuple[RuleResult, ...]) -> CategoryScore:
        """Assemble the category score from the successful rule results.

        Placeholder aggregation: the normalized scores are averaged. The AIS
        standard score is not defined yet, so this method is the single place
        that has to change once it is.

        Args:
            results: Results the rule engine reported as successful, in order.

        Returns:
            Immutable CategoryScore for the configured category.
        """
        scores = tuple(self._normalizer.normalize(result.score) for result in results)
        score = sum(scores) / len(scores) if scores else 0.0
        summary = "; ".join(result.reason for result in results)
        references = tuple(
            dict.fromkeys(
                reference
                for result in results
                for reference in result.evidence_references
            )
        )
        return CategoryScore(
            category=self._category,
            score=score,
            confidence=self._confidence,
            summary=summary,
            evidence_references=references,
        )
