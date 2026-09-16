"""Catalyst rule: when are the next results due?

The first answerable half of the Catalyst question is the calendar. A results
report is the one event AIS can put a date on for almost every company, and a
date that is coming is the clearest reason a picture could change soon.

What is measured is the distance to the event, not the event itself. An event
with no distance to it cannot be said to be coming, and a date the source
reports that has already passed is not forthcoming at all; both are absences,
and the source that could not supply one says so in the evidence.

Direction: a shorter distance means a nearer event, so smaller means a more
immediate reading. That is a statement about when the picture could change, not
about which way it would change; whether the results will be good is a question
this rule does not ask and cannot answer.

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

RULE_ID = "catalyst.earnings_date"
_METRIC = MarketMetric.NEXT_EARNINGS_DAYS
_PLACEHOLDER_DAYS = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_DAYS,
        reason=(
            f"Placeholder distance of {_PLACEHOLDER_DAYS:.0f} days to the next "
            f"results for {evidence.asset.ticker}; no market data source "
            f"connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the distance to the next scheduled results.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the number of days until the next report.

    Raises:
        DataError: When a market data source was consulted and did not provide a
            forthcoming date, so that no invented value reaches the score.
    """
    reading = read_metric(evidence, _METRIC)
    if reading is None:
        return _placeholder(evidence)
    if reading.value is None:
        raise DataError(f"{RULE_ID}: {reading.reason}")
    days = round(reading.value)
    return RuleResult(
        rule_id=RULE_ID,
        score=reading.value,
        reason=(
            f"Next results for {evidence.asset.ticker} scheduled {days} days "
            f"from now"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Next results",
    description="Reports how far away the next scheduled results are.",
    enabled=True,
    execute=_execute,
)
