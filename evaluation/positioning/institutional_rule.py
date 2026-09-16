"""Positioning rule: how much of the company do institutions hold?

Institutional ownership says who is on the register. It is the answer to "who
else holds this", in the plainest form a source publishes it: the share of the
company held by institutions rather than by individuals.

Direction: this rule states a reading and not a preference. A large institutional
holding is neither good nor bad on its own — it can mean the asset has been
examined and bought, or that it is already crowded with the same kind of holder —
and the scale is not defined yet, so a larger number is not declared better here.
The report says what the reading is and leaves the direction to the score that
will define it.

A company with no institutional register reports nothing, and the absence is
information rather than a zero.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "positioning.institutional"
_METRIC = MarketMetric.INSTITUTIONAL_OWNERSHIP
_PLACEHOLDER_SHARE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_SHARE,
        reason=(
            f"Placeholder institutional holding of {_PLACEHOLDER_SHARE:.1%} of "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the share of the company held by institutions.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the institutional holding.

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
            f"Institutions hold {reading.value:.1%} of " f"{evidence.asset.ticker}"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Institutional holding",
    description="Reports the share of the company held by institutions.",
    enabled=True,
    execute=_execute,
)
