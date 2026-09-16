"""Market evaluator.

Runs the market rules and assembles the Market category score.

The category question, from the Constitution, is what the environment is in
which this asset is being judged. This evaluator measures one aspect of that
environment and reports coverage against all three aspects the question is read
as having, so a reader is told how little of the environment has been examined
rather than only what it scored.

What is measured:

* **Direction** — how the broad market has moved over the last year.

What is not measured, and why it is listed as an aspect anyway:

* **Volatility** — how turbulent the market has been needs price history over
  time. This version retrieves one snapshot, so it cannot see turbulence.
* **Rates** — the cost of money the environment sets. No source for it is
  connected.

Both would materially change what the environment looks like. An asset judged in
a calm, rising market is in a different position from one judged in a turbulent
falling one, and AIS currently cannot tell those apart beyond the direction.

Note on shared evidence. Nothing here is read by another category. Beta, which
describes how an asset has moved relative to its market, belongs to Risk: it is
a property of the asset's movement, not of the environment.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.market import market_direction_rule
from evaluation.market.market_aspects import MarketAspect
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0

# Which aspect of the environment each rule speaks for. Kept beside the
# evaluator because the rules themselves only know their measurement.
_ASPECT_BY_RULE: dict[str, MarketAspect] = {
    market_direction_rule.RULE_ID: MarketAspect.DIRECTION,
}


class MarketEvaluator(BaseEvaluator):
    """Orchestrates the market rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the market rules in order."""
        self._rules = (market_direction_rule.RULE,)
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.MARKET,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(MarketAspect),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every market rule through the rule engine.

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
            CategoryScore for the MARKET category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(
            normalized,
            assessed=_aspects_assessed(evaluation),
        )


def _aspects_assessed(evaluation: EvaluationResult) -> int:
    """Return how many distinct aspects of the environment were measured."""
    covered = {
        _ASPECT_BY_RULE[result.rule_id]
        for result in evaluation.results
        if result.rule_id in _ASPECT_BY_RULE
    }
    return len(covered)
