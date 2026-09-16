"""Trend rule: where does the price sit within the range it has traded in?

The Trend category asks what the price has actually been doing, over a window
that is stated. One part of that is where the price is now relative to the range
it has covered: a price near the top of its range has behaved differently from
one near the bottom, whatever the direction over the window.

The position is evidence for the question. It is not the definition of trend: a
price at the top of its range says nothing about how it got there, and the
window is one choice among many.

Direction: a higher position means the price is nearer the top of its range, so
higher means a stronger trend. The score is a raw measurement on a scale that is
not defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "trend.position"
_METRIC = MarketMetric.TREND_RANGE_POSITION
_PLACEHOLDER_POSITION = 0.5


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_POSITION,
        reason=(
            f"Placeholder range position of {_PLACEHOLDER_POSITION:.0%} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the range position measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying where the price sits in its 52 week range.

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
            f"Price sits {reading.value:.0%} up its 52 week range for "
            f"{evidence.asset.ticker}"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Range position",
    description="Reports where the price sits within its 52 week range.",
    enabled=True,
    execute=_execute,
)
