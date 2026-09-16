"""Catalyst evaluator.

Runs the catalyst rules and assembles the Catalyst category score.

The category question, from the Constitution, is what identifiable event could
change this picture, and when. Two parts of the answer exist: events a market
data source can date, and events it cannot. Only the first is measured, so
coverage is reported against both and reads one part of two.

That is deliberate. Coverage here is not a progress bar; it is the statement
that this category looked at the calendar and not at the world. Product
launches, regulatory decisions, launch windows, shareholder meetings and macro
events have no source connected to AIS, and nothing here pretends otherwise.

When no date at all could be retrieved the rules fail with their reasons and the
category carries no judgement. The report says so in words — there is no
evaluable catalyst — rather than showing a low grade for a calendar that had
nothing on it.

Note on shared evidence. Nothing here is read by another category. What the
results have already said belongs to Earnings, and how the price has behaved
belongs to Trend; this category is about what is coming.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.catalyst import dividend_date_rule, earnings_date_rule
from evaluation.catalyst.catalyst_parts import CatalystPart
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0

# Which part of the catalyst question each rule speaks for. Both rules date an
# event the source publishes, so both answer the scheduled half.
_PART_BY_RULE: dict[str, CatalystPart] = {
    earnings_date_rule.RULE_ID: CatalystPart.SCHEDULED,
    dividend_date_rule.RULE_ID: CatalystPart.SCHEDULED,
}


class CatalystEvaluator(BaseEvaluator):
    """Orchestrates the catalyst rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the catalyst rules in order."""
        self._rules = (earnings_date_rule.RULE, dividend_date_rule.RULE)
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.CATALYST,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(CatalystPart),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every catalyst rule through the rule engine.

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
            CategoryScore for the CATALYST category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(
            normalized, assessed=_parts_assessed(evaluation)
        )


def _parts_assessed(evaluation: EvaluationResult) -> int:
    """Return how many parts of the catalyst question were measured."""
    covered = {
        _PART_BY_RULE[result.rule_id]
        for result in evaluation.results
        if result.rule_id in _PART_BY_RULE
    }
    return len(covered)
