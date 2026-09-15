"""Valuation rule: price/earnings to growth.

Placeholder policy: until real market data is connected, this rule reports a
deterministic placeholder PEG measurement and performs no real scoring.
"""

from __future__ import annotations

from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection

RULE_ID = "valuation.peg"
_PLACEHOLDER_PEG = 1.2
_PLACEHOLDER_REFERENCES = (RULE_ID,)


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder PEG measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the placeholder PEG value.
    """
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_PEG,
        reason=(
            f"Placeholder PEG of {_PLACEHOLDER_PEG} for {evidence.asset.ticker}; "
            "real market data pending."
        ),
        evidence_references=_PLACEHOLDER_REFERENCES,
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Price/earnings to growth",
    description="Reports the placeholder PEG measurement.",
    enabled=True,
    execute=_execute,
)
