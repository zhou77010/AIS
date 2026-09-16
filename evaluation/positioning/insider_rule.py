"""Positioning rule: how much of the company do insiders hold?

Insider holding is the other half of who is on the register. It is the share of
the company held by the people who run it, which is a different fact from what
institutions hold: the two can both be large, and a company can have almost
neither.

Direction: as with the institutional rule, this states a reading and not a
preference. A large insider holding can mean the people making the decisions are
exposed to them, or that a founder still owns most of the company; the two are
not the same thing and this rule does not choose between them. The scale is not
defined yet, so no direction is declared here.

Insider transactions — who bought and sold, and when — are a different
measurement from how much is held, and no source connected to AIS reports them.
This rule therefore does not speak for insider activity, and says so by name in
the list of what positioning does not cover.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "positioning.insider"
_METRIC = MarketMetric.INSIDER_OWNERSHIP
_PLACEHOLDER_SHARE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_SHARE,
        reason=(
            f"Placeholder insider holding of {_PLACEHOLDER_SHARE:.1%} of "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the share of the company held by insiders.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the insider holding.

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
        reason=f"Insiders hold {reading.value:.1%} of {evidence.asset.ticker}",
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Insider holding",
    description="Reports the share of the company held by insiders.",
    enabled=True,
    execute=_execute,
)
