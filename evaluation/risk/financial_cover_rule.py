"""Risk rule: financial risk, short term cover.

Financial risk is the possibility that the business's finances cannot support it
or cannot support the assumption (Constitution, Section 5.2). This rule measures
the second half of that question: whether what the business owes soon is covered
by what it holds now.

The current ratio is evidence for financial risk. It is not the definition of
it: short term cover is one way a business comes under strain, and it says
nothing about long term funding.

Direction: a lower ratio means less cover for what is owed soon, so lower means
more financial risk. The score is a raw measurement on a scale that is not
defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.risk.risk_dimensions import RiskDimension
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

DIMENSION = RiskDimension.FINANCIAL

RULE_ID = "risk.financial_cover"
_METRIC = MarketMetric.CURRENT_RATIO
_PLACEHOLDER_CURRENT_RATIO = 1.5


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_CURRENT_RATIO,
        reason=(
            f"Placeholder current ratio of {_PLACEHOLDER_CURRENT_RATIO} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the short term cover measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the retrieved current ratio.

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
            f"Current ratio {reading.value:.2f} for {evidence.asset.ticker}; "
            f"less cover for what is owed soon"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Financial risk, short term cover",
    description="Reports the retrieved current ratio.",
    enabled=True,
    execute=_execute,
)
