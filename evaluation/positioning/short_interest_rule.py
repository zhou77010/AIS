"""Positioning rule: how much of the float is sold short?

Short interest is the clearest measurement of crowding that a market data source
publishes. It is the share of the tradeable shares that someone has borrowed and
sold, which is a direct statement that a position has been taken against the
asset.

Direction: a smaller share means less of the trade is already against the asset,
so smaller means a better reading for crowding. The measurement says how crowded
the short side is; it does not say whether the shorts are right.

A share of the float is a ratio rather than a filed figure, so the evidence
records the division it came from. The score is a raw measurement on a scale that
is not defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "positioning.short_interest"
_METRIC = MarketMetric.SHORT_PERCENT_OF_FLOAT
_PLACEHOLDER_SHARE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_SHARE,
        reason=(
            f"Placeholder short interest of {_PLACEHOLDER_SHARE:.1%} of the float "
            f"for {evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the short interest as a share of the float.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the share of the float sold short.

    Raises:
        DataError: When a market data source was consulted and did not provide
            the measurement, so that no invented value reaches the score.
    """
    reading = read_metric(evidence, _METRIC)
    if reading is None:
        return _placeholder(evidence)
    if reading.value is None:
        raise DataError(f"{RULE_ID}: {reading.reason}")
    return RuleResult(
        rule_id=RULE_ID,
        score=reading.value,
        reason=(
            f"{reading.value:.1%} of the float of {evidence.asset.ticker} is sold "
            f"short"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Short interest",
    description="Reports the share of the float that is sold short.",
    enabled=True,
    execute=_execute,
)
