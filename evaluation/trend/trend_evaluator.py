"""Trend evaluator.

Runs the trend rules and assembles the Trend category score.

The category question, from the Constitution, is what the price has actually
been doing over a window that is stated. The Constitution requires the window to
be stated, and it is: every measurement name carries the window, so the report
shows "52 week" beside the number rather than leaving it in the code.

This evaluator measures two of the three aspects that question is read as
having, and reports coverage against all three, so a reader is told what has not
been looked at rather than only what has.

What is measured:

* **Position** — where the price sits within the range it has traded in.
* **Direction** — which way it moved over the window.

What is not measured:

* **Path** — how the price travelled between the two. Whether a rise was steady
  or arrived in one jump cannot be seen from a snapshot, and it needs the price
  over time rather than the two endpoints.

Note on shared evidence. Nothing here is read by another category. The broad
market's own change belongs to Market, and how the asset moves relative to that
market belongs to Risk as beta. This category is about the asset's own price.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evaluation.trend import direction_rule, position_rule
from evaluation.trend.trend_aspects import TrendAspect
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0

# Which aspect of price behaviour each rule speaks for.
_ASPECT_BY_RULE: dict[str, TrendAspect] = {
    position_rule.RULE_ID: TrendAspect.POSITION,
    direction_rule.RULE_ID: TrendAspect.DIRECTION,
}


class TrendEvaluator(BaseEvaluator):
    """Orchestrates the trend rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the trend rules in order."""
        self._rules = (position_rule.RULE, direction_rule.RULE)
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.TREND,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(TrendAspect),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every trend rule through the rule engine.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            EvaluationResult holding every rule outcome.
        """
        return self._engine.run(self._rules, evidence)

    def evaluate(self, evidence: EvidenceCollection) -> CategoryScore:
        """Execute the rules, normalize their results and assemble the score.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            CategoryScore for the TREND category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(
            normalized, assessed=_aspects_assessed(evaluation)
        )


def _aspects_assessed(evaluation: EvaluationResult) -> int:
    """Return how many distinct aspects of price behaviour were measured."""
    covered = {
        _ASPECT_BY_RULE[result.rule_id]
        for result in evaluation.results
        if result.rule_id in _ASPECT_BY_RULE
    }
    return len(covered)
