"""Earnings rule: what have the reported results said?

The first half of the Earnings question is about what has actually been
reported. The growth of quarterly earnings against the same quarter a year
earlier is one direct reading of that: it says whether the results themselves
have been improving or deteriorating.

The growth rate is evidence for the question. It is not the definition of it: a
single quarter's growth is a noisy reading of a business, and it says nothing
about why the earnings moved.

Direction: a larger growth rate means results that improved more, so larger
means a better reading. The score is a raw measurement on a scale that is not
defined yet, and the report labels it as such.

A business with no positive earnings to compare reports no growth rate at all.
That absence is information, and the rule fails with the reason rather than
reporting a zero.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "earnings.reported"
_METRIC = MarketMetric.EARNINGS_GROWTH
_PLACEHOLDER_GROWTH = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_GROWTH,
        reason=(
            f"Placeholder quarterly earnings growth of {_PLACEHOLDER_GROWTH:+.1%} "
            f"for {evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the reported earnings measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the reported quarterly earnings growth.

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
            f"Reported earnings {reading.value:+.1%} against a year earlier for "
            f"{evidence.asset.ticker}"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Reported earnings",
    description="Reports the growth of reported quarterly earnings.",
    enabled=True,
    execute=_execute,
)
