"""Risk rule: liquidity risk.

Liquidity risk is the possibility that the position cannot be entered or exited
on the terms the thesis assumes (Constitution, Section 5.2).

This rule measures the share of the tradable supply that changes hands on a
typical day. It is the ratio of the average daily volume to the number of shares
in the float, and it describes how easily a position of ordinary size can be
traded without moving the price.

Direction: a lower turnover means a position takes longer to build or unwind, so
lower means more liquidity risk. The score is a raw measurement on a scale that
is not defined yet, and the report labels it as such.

An exchange-traded fund still reports both of the measurements this rule needs,
so this is the one risk dimension that remains assessable for an asset with no
company financials of its own.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import MetricReading, read_metric
from evaluation.risk.risk_dimensions import RiskDimension
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

DIMENSION = RiskDimension.LIQUIDITY

RULE_ID = "risk.liquidity"
_PLACEHOLDER_TURNOVER = 0.01


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_TURNOVER,
        reason=(
            f"Placeholder daily turnover of {_PLACEHOLDER_TURNOVER:.2%} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the liquidity measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the share of the float traded on a typical day.

    Raises:
        DataError: When a market data source was consulted and did not provide
            both measurements this rule needs, or when the float is not a
            positive number and the ratio would be meaningless.
    """
    volume = read_metric(evidence, MarketMetric.AVERAGE_VOLUME)
    float_shares = read_metric(evidence, MarketMetric.FLOAT_SHARES)
    if volume is None and float_shares is None:
        return _placeholder(evidence)

    traded = _value_of(volume, MarketMetric.AVERAGE_VOLUME)
    supply = _value_of(float_shares, MarketMetric.FLOAT_SHARES)
    if supply <= 0:
        raise DataError(
            f"{RULE_ID}: the float is not a positive number of shares, so the "
            f"share traded each day cannot be measured"
        )
    turnover = traded / supply
    return RuleResult(
        rule_id=RULE_ID,
        score=turnover,
        reason=(
            f"Daily turnover {turnover:.2%} for {evidence.asset.ticker}; "
            f"a smaller share traded means a position is harder to move"
        ),
        evidence_references=tuple(
            reading.evidence_id
            for reading in (volume, float_shares)
            if reading is not None
        ),
    )


def _value_of(reading: MetricReading | None, metric: MarketMetric) -> float:
    """Return a retrieved value, refusing to continue without one."""
    if reading is None:
        raise DataError(f"no market data source provided {metric.label} for this asset")
    if reading.value is None:
        raise DataError(reading.reason)
    return reading.value


RULE = EvaluationRule(
    id=RULE_ID,
    name="Liquidity risk",
    description="Reports the share of the float traded on a typical day.",
    enabled=True,
    execute=_execute,
)
