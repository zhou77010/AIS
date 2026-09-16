"""Catalyst rule: when do the shares next go ex-dividend?

Going ex-dividend is a scheduled corporate event with a date on it, and it is
the second event AIS can put a date on. It is a smaller catalyst than a results
report for most companies, and for a company that pays nothing it is not a
catalyst at all: the rule then reports an absence rather than a zero, because
zero would say the shares go ex-dividend today.

Direction: a shorter distance means a nearer event, so smaller means a more
immediate reading. As with the results rule, that says when and not which way.

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

RULE_ID = "catalyst.dividend_date"
_METRIC = MarketMetric.NEXT_EX_DIVIDEND_DAYS
_PLACEHOLDER_DAYS = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_DAYS,
        reason=(
            f"Placeholder distance of {_PLACEHOLDER_DAYS:.0f} days to the next "
            f"ex-dividend date for {evidence.asset.ticker}; no market data "
            f"source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the distance to the next ex-dividend date.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the number of days until the shares go ex-dividend.

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
            f"Shares of {evidence.asset.ticker} go ex-dividend {days} days from " f"now"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Ex-dividend date",
    description="Reports how far away the next ex-dividend date is.",
    enabled=True,
    execute=_execute,
)
