"""Fundamental rule: does the profit become cash?

A business that reports a profit it never collects is not financially sound, so
whether earnings turn into cash is a part of the Fundamental question rather
than a restatement of profitability. The free cash flow margin measures how much
of each unit of revenue ends up as cash the business is free to use.

The margin is evidence for the question. It is not the question: a business can
burn cash in one period while soundly investing, and the margin says nothing
about how the cash is spent.

Direction: a larger margin means more of each sale becomes free cash, so larger
means a more sound business. The score is a raw measurement on a scale that is
not defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "fundamental.cash_conversion"
_METRIC = MarketMetric.FREE_CASH_FLOW_MARGIN
_PLACEHOLDER_MARGIN = 0.05


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_MARGIN,
        reason=(
            f"Placeholder free cash flow margin of {_PLACEHOLDER_MARGIN:.1%} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the cash conversion measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the retrieved free cash flow margin.

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
            f"Free cash flow margin {reading.value:.2%} for "
            f"{evidence.asset.ticker}; the share of each sale kept as cash"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Cash conversion",
    description="Reports the free cash flow margin as a measurement of soundness.",
    enabled=True,
    execute=_execute,
)
