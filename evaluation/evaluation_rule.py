"""AIS evaluation rule.

An evaluation rule is the metadata object that governs one reusable step of an
evaluation. It carries the rule identity, its enabled state, and the callable
the rule engine executes to produce a RuleResult.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection


@dataclass(frozen=True)
class EvaluationRule:
    """Metadata and execution entry point for one evaluation rule.

    Attributes:
        id: Identifier of the rule.
        name: Short name of the rule.
        description: What the rule checks for.
        enabled: Whether the rule is currently applied.
        execute: Callable that runs the rule and returns its result.
    """

    id: str
    name: str
    description: str
    enabled: bool
    execute: Callable[[EvidenceCollection], RuleResult]
