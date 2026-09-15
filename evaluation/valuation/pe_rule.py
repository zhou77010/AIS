"""Valuation rule: price to earnings.

Placeholder policy: until real market data is connected, this rule reports a
deterministic placeholder P/E measurement and performs no real scoring.
"""

from __future__ import annotations

from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection

RULE_ID = "valuation.pe"
_PLACEHOLDER_PE = 15.0
_PLACEHOLDER_REFERENCES = (RULE_ID,)


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder price-to-earnings measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the placeholder P/E value.
    """
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_PE,
        reason=(
            f"Placeholder P/E of {_PLACEHOLDER_PE} for {evidence.asset.ticker}; "
            "real market data pending."
        ),
        evidence_references=_PLACEHOLDER_REFERENCES,
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Price to earnings",
    description="Reports the placeholder P/E measurement.",
    enabled=True,
    execute=_execute,
)
