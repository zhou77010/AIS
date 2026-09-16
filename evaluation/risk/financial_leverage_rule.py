"""Risk rule: financial risk, leverage.

Financial risk is the possibility that the business's finances cannot support it
or cannot support the assumption (Constitution, Section 5.2). This rule measures
one half of that question: how much the business is funded by borrowing rather
than by what its owners put in.

Debt to equity is evidence for financial risk. It is not the definition of it:
leverage is one way a business comes under strain, and a business can be
unlevered and still fail to fund itself.

Direction: a higher ratio means more borrowing relative to owners' capital, so
higher means more financial risk. The score is a raw measurement on a scale that
is not defined yet, and the report labels it as such.

A bank reports no such ratio at all, in the same way it reports no current
ratio: the concept assumes an operating business. That absence is correct, and
the rule fails with the reason rather than reporting a number.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "risk.financial_leverage"
_METRIC = MarketMetric.DEBT_TO_EQUITY
_PLACEHOLDER_DEBT_TO_EQUITY = 1.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_DEBT_TO_EQUITY,
        reason=(
            f"Placeholder debt to equity of {_PLACEHOLDER_DEBT_TO_EQUITY} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the financial leverage measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the retrieved debt to equity ratio.

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
            f"Debt to equity {reading.value:.2f} for {evidence.asset.ticker}; "
            f"more borrowing relative to owners' capital"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Financial risk, leverage",
    description="Reports the retrieved debt to equity ratio.",
    enabled=True,
    execute=_execute,
)
