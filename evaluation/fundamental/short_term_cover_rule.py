"""Fundamental rule: can the business meet what it owes soon?

Solvency is about what is owed overall; this is about what is owed shortly. A
business can be soundly financed in the long run and still be unable to pay its
bills this year, so short term cover is a separate part of the Fundamental
question rather than a restatement of solvency.

This measurement is also read by the Risk category, and that is deliberate. The
questions differ: this one asks what the business's short term position *is*,
while Risk asks how exposed a thesis is to it. The fact is stored once as
evidence and read by both.

Direction: a larger ratio means more held against what is owed soon, so larger
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

RULE_ID = "fundamental.short_term_cover"
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
            f"what it holds against what it owes soon"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Short term cover",
    description="Reports the current ratio as a measurement of soundness.",
    enabled=True,
    execute=_execute,
)
