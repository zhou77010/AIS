"""Positioning evaluator.

Runs the positioning rules and assembles the Positioning category score.

The category question, from the Constitution, is who else holds this asset, and
how crowded is that. Three parts of the answer exist: who is on the register, how
crowded the short side is, and whether money is arriving or leaving. The first
two are measured, so coverage reads two parts of three.

Institutional and insider *changes*, fund flows, options positioning and
sentiment have no source connected to AIS. They are named as not covered rather
than approximated from a holding that happens to be available.

Note on shared evidence. Nothing here is read by another category: how many
shares trade belongs to Risk, and what the price has done belongs to Trend. This
category is about who is holding, and it reads a holding as a fact rather than as
a verdict.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.positioning import (
    insider_rule,
    institutional_rule,
    short_interest_rule,
    short_ratio_rule,
)
from evaluation.positioning.positioning_parts import PositioningPart
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0

# Which part of the positioning question each rule speaks for.
_PART_BY_RULE: dict[str, PositioningPart] = {
    institutional_rule.RULE_ID: PositioningPart.OWNERSHIP,
    insider_rule.RULE_ID: PositioningPart.OWNERSHIP,
    short_interest_rule.RULE_ID: PositioningPart.CROWDING,
    short_ratio_rule.RULE_ID: PositioningPart.CROWDING,
}


class PositioningEvaluator(BaseEvaluator):
    """Orchestrates the positioning rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the positioning rules in order."""
        self._rules = (
            institutional_rule.RULE,
            insider_rule.RULE,
            short_interest_rule.RULE,
            short_ratio_rule.RULE,
        )
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.POSITIONING,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(PositioningPart),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every positioning rule through the rule engine.

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
            CategoryScore for the POSITIONING category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(
            normalized, assessed=_parts_assessed(evaluation)
        )


def _parts_assessed(evaluation: EvaluationResult) -> int:
    """Return how many parts of the positioning question were measured."""
    covered = {
        _PART_BY_RULE[result.rule_id]
        for result in evaluation.results
        if result.rule_id in _PART_BY_RULE
    }
    return len(covered)
