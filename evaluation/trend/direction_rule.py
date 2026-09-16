"""Trend rule: which way has the price moved over the window?

Position says where the price is; this says how it got there, net of the
journey. A price can sit in the middle of its range having risen over the year
or having fallen, and the two are different trends.

The change over the window is evidence for the question. It is not the
definition of trend: a net change hides everything that happened inside the
window, and the window is one choice among many.

Direction: a larger change means a price that has risen more over the window, so
larger means a stronger trend. The score is a raw measurement on a scale that is
not defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "trend.direction"
_METRIC = MarketMetric.TREND_DIRECTION
_PLACEHOLDER_CHANGE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_CHANGE,
        reason=(
            f"Placeholder 52 week price change of {_PLACEHOLDER_CHANGE:+.1%} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the direction measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the price change over the last 52 weeks.

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
            f"Price {reading.value:+.1%} over 52 weeks for " f"{evidence.asset.ticker}"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Trend direction",
    description="Reports the price change over the last 52 weeks.",
    enabled=True,
    execute=_execute,
)
