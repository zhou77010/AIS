"""Positioning rule: how long would the shorts need to cover?

Days to cover says how large the short position is against how much the asset
actually trades. It answers a question the share of float does not: a position
can be small next to the float and still take a long time to unwind if the shares
barely trade.

Direction: fewer days means a position that could be unwound sooner, so smaller
means a better reading for crowding. It is a statement about how crowded the
short side is and not about who is right.

The score is a raw measurement on a scale that is not defined yet, and the report
labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "positioning.short_ratio"
_METRIC = MarketMetric.SHORT_RATIO
_PLACEHOLDER_DAYS = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_DAYS,
        reason=(
            f"Placeholder {_PLACEHOLDER_DAYS:.1f} days to cover the short "
            f"position in {evidence.asset.ticker}; no market data source "
            f"connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the days needed to cover the short position.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the days to cover.

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
            f"Covering the short position in {evidence.asset.ticker} would take "
            f"{reading.value:.1f} days of average trading"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Days to cover",
    description="Reports how long the short position would take to cover.",
    enabled=True,
    execute=_execute,
)
