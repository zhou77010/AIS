"""Market evaluator.

Runs the market rules and assembles the Market category score.

The category question, from the Constitution, is what the environment is in
which this asset is being judged. This evaluator measures that environment and
reports coverage against all four aspects the question is read as having, so a
reader is told how little of the environment has been examined rather than only
what it scored.

What is measured:

* **Direction** — how the broad market has moved over the last year.
* **Risk appetite** — what the equity futures have done since the last close, and
  whether growth is leading or lagging.
* **Volatility** — how turbulent the market is, and whether that is settling.
* **Rates** — which way the ten year yield moved over the session.

Two of those were listed as aspects long before anything measured them, which is
what the aspect set was for: the gap was visible in the report rather than hidden
by a fraction that read as complete. The evidence that closed them is shared
between every asset in a pass — the market is the same market for all of them —
and it arrives through the same evidence stream as everything else.

Note on shared evidence. Beta, which describes how an asset has moved relative to
its market, still belongs to Risk: it is a property of the asset's movement, not of
the environment. What this category does with the environment and with the asset's
own measurements *together* is interpret it, and that happens in the insight layer,
where a sentence can be written about one asset.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.market import (
    market_direction_rule,
    market_rates_rule,
    market_risk_appetite_rule,
    market_volatility_rule,
)
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
    market_risk_appetite_rule.RULE_ID: MarketAspect.RISK_APPETITE,
    market_volatility_rule.RULE_ID: MarketAspect.VOLATILITY,
    market_rates_rule.RULE_ID: MarketAspect.RATES,
}


class MarketEvaluator(BaseEvaluator):
    """Orchestrates the market rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the market rules in order."""
        self._rules = (
            market_direction_rule.RULE,
            market_risk_appetite_rule.RULE,
            market_volatility_rule.RULE,
            market_rates_rule.RULE,
        )
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
    """Return how many distinct aspects of the environment were actually measured.

    An aspect counts when a rule read something for it, and not merely when a rule
    produced a result. A placeholder — which is what a run without a source produces,
    so that the pipeline stays deterministic — read nothing, and counting it would
    report the environment as examined when not one measurement of it exists. That is
    the failure the aspect set was created to prevent, and it would be the same
    failure with better numbers.
    """
    covered = {
        _ASPECT_BY_RULE[result.rule_id]
        for result in evaluation.results
        if result.rule_id in _ASPECT_BY_RULE and result.evidence_references
    }
    return len(covered)
