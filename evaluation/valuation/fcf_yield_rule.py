"""Valuation rule: free cash flow yield.

Placeholder policy: until real market data is connected, this rule reports a
deterministic placeholder FCF yield and performs no real scoring.
"""

from __future__ import annotations

from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection

RULE_ID = "valuation.fcf_yield"
_PLACEHOLDER_FCF_YIELD = 0.05
_PLACEHOLDER_REFERENCES = (RULE_ID,)


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder FCF yield measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the placeholder FCF yield value.
    """
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_FCF_YIELD,
        reason=(
            f"Placeholder FCF yield of {_PLACEHOLDER_FCF_YIELD:.1%} for "
            f"{evidence.asset.ticker}; real market data pending."
        ),
        evidence_references=_PLACEHOLDER_REFERENCES,
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Free cash flow yield",
    description="Reports the placeholder FCF yield measurement.",
    enabled=True,
    execute=_execute,
)
