"""Risk evaluator.

Runs the risk rules and assembles the Risk category score.

Risk is the category that asks what could make an investment thesis wrong
(Constitution, Section 5). The kinds of uncertainty it is about are the eight
dimensions the Constitution fixes. This evaluator assesses three of them, and
the category reports the resulting coverage as a fraction of all eight, so a
reader is told how much of the category was examined rather than only what it
scored.

The dimensions that are measured:

* **Market risk** is measured from beta.
* **Financial risk** is measured from leverage and from short term cover.
* **Liquidity risk** is measured from the share of the float traded each day.

The dimensions that are deliberately not measured, and why. Their absence is
reported as missing coverage and must never be read as an absence of risk:

* **Business risk** — separating how uncertain a business is from how it is
  currently doing needs more than one snapshot. It needs the same measurement
  over time, which this version does not retrieve.
* **Valuation risk** — not measured, because no evidence this version retrieves
  speaks to it. The measurements behind the Valuation category describe the
  level of a multiple. Whether a multiple is at risk of compressing needs
  something about expectations or history, which is not retrieved here. Reusing
  the valuation measurements would answer the valuation question a second time,
  not answer this one.
* **Event risk** — no source of dated events is connected. A rule that guessed
  at events would be stating an opinion, not reading evidence.
* **Evidence risk** — reported by the coverage line of the category itself and
  of every report, so that it is measured once rather than twice.
* **Horizon risk** — cannot be measured without knowing the horizon a holder
  needs. AIS is not told that and will not assume it.

Note on shared evidence. Two rules here read measurements the Fundamental
category also reads: debt to equity and the current ratio. That is not double
counting. The rule is that the same evidence must not answer the same question
twice under two names, and these are not the same question. Fundamental asks
whether the business is financially sound, which describes its state; the rules
here ask how exposed a thesis is to that state, which describes what could
invalidate it. One fact may support both. Nothing is recorded twice either: the
measurement is stored once as evidence and read by both.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.risk import (
    financial_cover_rule,
    financial_leverage_rule,
    liquidity_rule,
    market_risk_rule,
)
from evaluation.risk.risk_dimensions import RiskDimension
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0

# Which dimension each rule speaks for. Two rules may serve one dimension, which
# is why coverage counts dimensions rather than rules.
_DIMENSION_BY_RULE: dict[str, RiskDimension] = {
    market_risk_rule.RULE_ID: market_risk_rule.DIMENSION,
    financial_leverage_rule.RULE_ID: financial_leverage_rule.DIMENSION,
    financial_cover_rule.RULE_ID: financial_cover_rule.DIMENSION,
    liquidity_rule.RULE_ID: liquidity_rule.DIMENSION,
}


class RiskEvaluator(BaseEvaluator):
    """Orchestrates the risk rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the risk rules in order."""
        self._rules = (
            market_risk_rule.RULE,
            financial_leverage_rule.RULE,
            financial_cover_rule.RULE,
            liquidity_rule.RULE,
        )
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.RISK,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(RiskDimension),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every risk rule through the rule engine.

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
            CategoryScore for the RISK category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(
            normalized, assessed=_dimensions_assessed(evaluation)
        )


def _dimensions_assessed(evaluation: EvaluationResult) -> int:
    """Return how many distinct risk dimensions produced a measurement.

    Counting rules would overstate it: two rules measure financial risk, so a
    successful pair still leaves one dimension covered rather than two.
    """
    covered = {
        _DIMENSION_BY_RULE[result.rule_id]
        for result in evaluation.results
        if result.rule_id in _DIMENSION_BY_RULE
    }
    return len(covered)
