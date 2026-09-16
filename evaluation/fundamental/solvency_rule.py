"""Fundamental rule: can the business meet what it owes?

A business that owes more than its owners have put in is not financially sound,
however profitable it is in a good year. Debt to equity measures what the
business owes against what its owners have committed to it.

This measurement is also read by the Risk category, and that is deliberate. The
rule is that one fact must not answer the same question twice under two names.
These are different questions: this one asks what the balance sheet *is*, a
statement about the business's state, while Risk asks how exposed a thesis is to
that state. The fact is stored once as evidence and read by both.

Direction: a larger ratio means more borrowing relative to owners' capital, so
larger means a less sound business. The score is a raw measurement on a scale
that is not defined yet, and the report labels it as such.

A bank reports no such ratio, because the concept assumes an operating business
rather than a balance-sheet one. That absence is correct, and the rule fails
with the reason rather than reporting a number.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "fundamental.solvency"
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
    """Return the solvency measurement for the asset.

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
            f"what the business owes against what its owners put in"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Solvency",
    description="Reports debt to equity as a measurement of soundness.",
    enabled=True,
    execute=_execute,
)
