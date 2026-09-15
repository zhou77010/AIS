"""Valuation rule: discounted cash flow.

A discounted cash flow fair value is the output of a valuation model, not a
datum any market data source publishes. It therefore cannot be retrieved, and
this rule never reports one: when a market data source was consulted the rule
fails with that reason, which the evaluation records and continues past. The
input is left missing rather than approximated, because a made up discount rate
or growth assumption would be a fabricated measurement, not evidence.

Placeholder policy: a collection built without a market data source carries no
market evidence, and the rule falls back to the deterministic placeholder
measurement it reported before live data existed.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evaluation.valuation.market_evidence import read_metric
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "valuation.dcf"
_METRIC = MarketMetric.DCF
_PLACEHOLDER_FAIR_VALUE = 100.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a collection without market data."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_FAIR_VALUE,
        reason=(
            f"Placeholder DCF fair value of {_PLACEHOLDER_FAIR_VALUE} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(RULE_ID,),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the DCF measurement for the asset, or refuse to report one.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the placeholder value when no market data source
        was consulted.

    Raises:
        DataError: Whenever a market data source was consulted, because no
            source can supply this metric and no value may be invented for it.
    """
    reading = read_metric(evidence, _METRIC)
    if reading is None:
        return _placeholder(evidence)
    raise DataError(f"{RULE_ID}: {reading.reason}")


RULE = EvaluationRule(
    id=RULE_ID,
    name="Discounted cash flow",
    description=("Reports the DCF fair value; unavailable from market data by nature."),
    enabled=True,
    execute=_execute,
)
