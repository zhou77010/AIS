"""Valuation evaluator.

The first concrete evaluator. It declares the reusable valuation rules, lets the
rule engine execute them, and delegates the assembly of the category score to
the category assembler.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.rule_engine import RuleEngine
from evaluation.valuation import (
    dcf_rule,
    ev_ebitda_rule,
    fcf_yield_rule,
    pe_rule,
    peg_rule,
)
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0


class ValuationEvaluator(BaseEvaluator):
    """Orchestrates the valuation rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the valuation rules in order."""
        self._rules = (
            pe_rule.RULE,
            peg_rule.RULE,
            ev_ebitda_rule.RULE,
            fcf_yield_rule.RULE,
            dcf_rule.RULE,
        )
        self._engine = RuleEngine()
        self._assembler = CategoryAssembler(
            category=Category.VALUATION, confidence=_PLACEHOLDER_CONFIDENCE
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every valuation rule through the rule engine.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            EvaluationResult holding every rule outcome.
        """
        return self._engine.run(self._rules, evidence)

    def evaluate(self, evidence: EvidenceCollection) -> CategoryScore:
        """Execute the valuation rules and assemble their category score.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            CategoryScore for the VALUATION category.
        """
        evaluation = self.collect_results(evidence)
        return self._assembler.assemble(evaluation.results)
