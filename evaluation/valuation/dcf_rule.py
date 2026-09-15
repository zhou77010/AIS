"""Valuation rule: discounted cash flow.

Placeholder policy: until real market data is connected, this rule reports a
deterministic placeholder DCF fair value and performs no real scoring.
"""

from __future__ import annotations

from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection

RULE_ID = "valuation.dcf"
_PLACEHOLDER_FAIR_VALUE = 100.0
_PLACEHOLDER_REFERENCES = (RULE_ID,)


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder DCF fair value measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the placeholder DCF fair value.
    """
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_FAIR_VALUE,
        reason=(
            f"Placeholder DCF fair value of {_PLACEHOLDER_FAIR_VALUE} for "
            f"{evidence.asset.ticker}; real market data pending."
        ),
        evidence_references=_PLACEHOLDER_REFERENCES,
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Discounted cash flow",
    description="Reports the placeholder DCF fair value measurement.",
    enabled=True,
    execute=_execute,
)
