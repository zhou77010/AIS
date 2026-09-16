"""Fundamental rule: does the business earn a return on its owners' capital?

Being profitable is not the same as being worth the money in it. A business can
earn a profit every year and still be financially unsound if that profit is
small relative to the capital its owners have committed. Return on equity
measures that relationship.

The return is evidence for the question. It is not the question: a high return
may come from borrowing rather than from the business, and a low one may follow
a year of deliberate investment.

Direction: a larger return means more earned on each unit of owners' capital, so
larger means a more sound business. The score is a raw measurement on a scale
that is not defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "fundamental.return_on_capital"
_METRIC = MarketMetric.RETURN_ON_EQUITY
_PLACEHOLDER_RETURN = 0.15


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_RETURN,
        reason=(
            f"Placeholder return on equity of {_PLACEHOLDER_RETURN:.1%} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the return on capital measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the retrieved return on equity.

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
            f"Return on equity {reading.value:.2%} for {evidence.asset.ticker}; "
            f"what the business earns on its owners' capital"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Return on capital",
    description="Reports return on equity as a measurement of soundness.",
    enabled=True,
    execute=_execute,
)
