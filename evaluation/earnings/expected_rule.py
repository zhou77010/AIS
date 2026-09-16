"""Earnings rule: what are the results expected to say next?

The second half of the Earnings question is forward looking. What is expected
next is already embedded in the forward earnings figure, and comparing it with
what has actually been reported says how much improvement or deterioration the
expectation contains.

The expected change is evidence for the question. It is not the definition of
it: it is a consensus the source reports rather than a view AIS holds, and a
consensus can be wrong in either direction.

Direction: a larger expected change means more improvement is priced into the
expectation, so larger means a better reading. The score is a raw measurement on
a scale that is not defined yet, and the report labels it as such.

A business with no positive reported earnings carries no meaningful change:
dividing by a loss says nothing. That absence is information, and the rule fails
with the reason rather than reporting a number.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "earnings.expected"
_METRIC = MarketMetric.EXPECTED_EARNINGS_CHANGE
_PLACEHOLDER_CHANGE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_CHANGE,
        reason=(
            f"Placeholder expected earnings change of {_PLACEHOLDER_CHANGE:+.1%} "
            f"for {evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the expected earnings measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the change the expectation contains.

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
            f"Earnings expected to change {reading.value:+.1%} against what was "
            f"reported for {evidence.asset.ticker}"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Expected earnings",
    description="Reports the change the earnings expectation contains.",
    enabled=True,
    execute=_execute,
)
