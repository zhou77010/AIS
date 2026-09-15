"""AIS rule result.

A rule result records the raw outcome of running one rule. It is pure data and
carries no business logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    """Raw outcome of running one rule.

    Attributes:
        rule_id: Identifier of the rule that produced this result.
        score: Raw score produced by the rule, on the rule's own scale.
        reason: Human readable explanation of the outcome.
        evidence_references: Identifiers of the evidence supporting the result.
    """

    rule_id: str
    score: float
    reason: str
    evidence_references: tuple[str, ...]
