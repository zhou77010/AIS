"""Valuation rule: enterprise value to EBITDA.

Placeholder policy: until real market data is connected, this rule reports a
deterministic placeholder EV/EBITDA measurement and performs no real scoring.
"""

from __future__ import annotations

from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection

RULE_ID = "valuation.ev_ebitda"
_PLACEHOLDER_EV_EBITDA = 10.0
_PLACEHOLDER_REFERENCES = (RULE_ID,)


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder EV/EBITDA measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the placeholder EV/EBITDA value.
    """
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_EV_EBITDA,
        reason=(
            f"Placeholder EV/EBITDA of {_PLACEHOLDER_EV_EBITDA} for "
            f"{evidence.asset.ticker}; real market data pending."
        ),
        evidence_references=_PLACEHOLDER_REFERENCES,
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Enterprise value to EBITDA",
    description="Reports the placeholder EV/EBITDA measurement.",
    enabled=True,
    execute=_execute,
)
