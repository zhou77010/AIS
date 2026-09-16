"""Earnings evaluator.

Runs the earnings rules and assembles the Earnings category score.

The category question, from the Constitution, is what the reported results have
said and what they are expected to say next. Both parts are measured, and
coverage is reported against those two parts, so a coverage of two of two means
the whole of the question this category answers was answered.

What is measured:

* **Reported** — the growth of quarterly earnings against a year earlier.
* **Expected** — the change the forward earnings expectation contains.

What is not covered, and is not claimed. Guidance and estimate revisions are
things investors watch and AIS has no source for either. They are not part of
the question as the Constitution states it, so nothing here pretends to cover
them; if the question is later read as wider than two parts, this category's
coverage becomes wrong and must change with it.

Note on shared evidence. Nothing here is read by another category. A price that
moved belongs to Trend, and whether the business is sound belongs to
Fundamental; this category is about what the results themselves said.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.earnings import expected_rule, reported_rule
from evaluation.earnings.earnings_parts import EarningsPart
from evaluation.evaluation_result import EvaluationResult
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0

# Which part of the earnings question each rule speaks for.
_PART_BY_RULE: dict[str, EarningsPart] = {
    reported_rule.RULE_ID: EarningsPart.REPORTED,
    expected_rule.RULE_ID: EarningsPart.EXPECTED,
}


class EarningsEvaluator(BaseEvaluator):
    """Orchestrates the earnings rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the earnings rules in order."""
        self._rules = (reported_rule.RULE, expected_rule.RULE)
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.EARNINGS,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(EarningsPart),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every earnings rule through the rule engine.

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
            CategoryScore for the EARNINGS category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(
            normalized, assessed=_parts_assessed(evaluation)
        )


def _parts_assessed(evaluation: EvaluationResult) -> int:
    """Return how many parts of the earnings question were measured."""
    covered = {
        _PART_BY_RULE[result.rule_id]
        for result in evaluation.results
        if result.rule_id in _PART_BY_RULE
    }
    return len(covered)
