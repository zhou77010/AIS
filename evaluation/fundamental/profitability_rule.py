"""Fundamental rule: can the business earn a profit from what it sells?

The Fundamental category asks what the business is and whether it is
financially sound (Constitution, Section 4). One part of being sound is earning
more from a sale than the sale costs, and the net profit margin measures how
much of each unit of revenue survives to the bottom line.

The margin is evidence for the question. It is not the question: a business can
run a thin margin and be perfectly sound, and a wide margin says nothing about
how the profit is funded.

Direction: a larger margin means more of each sale is kept, so larger means a
more sound business. The score is a raw measurement on a scale that is not
defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "fundamental.profitability"
_METRIC = MarketMetric.PROFIT_MARGIN
_PLACEHOLDER_MARGIN = 0.10


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_MARGIN,
        reason=(
            f"Placeholder net profit margin of {_PLACEHOLDER_MARGIN:.1%} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the profitability measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the retrieved net profit margin.

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
            f"Net profit margin {reading.value:.2%} for {evidence.asset.ticker}; "
            f"the share of each sale kept as profit"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Profitability",
    description="Reports the net profit margin as a measurement of soundness.",
    enabled=True,
    execute=_execute,
)
