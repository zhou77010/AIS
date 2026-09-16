"""Valuation rule: enterprise value to EBITDA.

The rule reports the EV/EBITDA the market data source retrieved. When the source
could not provide it, the rule fails instead of inventing a value, and the reason
recorded with the evidence states why.

Placeholder policy: a collection built without a market data source carries no
market evidence, and the rule falls back to the deterministic placeholder
measurement it reported before live data existed.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "valuation.ev_ebitda"
_METRIC = MarketMetric.EV_EBITDA
_PLACEHOLDER_EV_EBITDA = 10.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a collection without market data."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_EV_EBITDA,
        reason=(
            f"Placeholder EV/EBITDA of {_PLACEHOLDER_EV_EBITDA} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(RULE_ID,),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the EV/EBITDA measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the retrieved EV/EBITDA, or the placeholder value
        when no market data source was consulted.

    Raises:
        DataError: When a market data source was consulted and did not provide
            the metric, so that no invented value reaches the score.
    """
    reading = read_metric(evidence, _METRIC)
    if reading is None:
        return _placeholder(evidence)
    if reading.value is None:
        raise DataError(f"{RULE_ID}: {reading.reason}")
    return RuleResult(
        rule_id=RULE_ID,
        score=reading.value,
        reason=f"EV/EBITDA of {reading.value:.2f} for {evidence.asset.ticker}",
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Enterprise value to EBITDA",
    description="Reports the retrieved EV/EBITDA measurement.",
    enabled=True,
    execute=_execute,
)
