"""Market rule: where has the market the asset trades in been going?

The Market category asks what the environment is in which this asset is being
judged. One part of that environment is the direction of the market itself: an
asset is judged against the conditions it trades in, and a market that has been
falling is a different environment from one that has been rising.

The broad market's change over the last year is evidence for that. It is not the
definition of market direction: one index is a summary of a whole market, and a
year is one window among many.

Direction: a larger change means a market that has been rising, so larger means
a more favourable environment. The score is a raw measurement on a scale that is
not defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "market.direction"
_METRIC = MarketMetric.MARKET_DIRECTION
_PLACEHOLDER_CHANGE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_CHANGE,
        reason=(
            f"Placeholder broad market change of {_PLACEHOLDER_CHANGE:.1%} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the market direction measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the broad market's change over the last year.

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
            f"Broad market {reading.value:+.1%} over the last year for "
            f"{evidence.asset.ticker}; the conditions it is judged in"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Market direction",
    description="Reports how the broad market has moved over the last year.",
    enabled=True,
    execute=_execute,
)
