"""Fundamental evaluator.

Runs the fundamental rules and assembles the Fundamental category score.

The category question, from the Constitution, is what the business is and
whether it is financially sound. This evaluator answers the second half of it.
The first half is descriptive rather than a judgement: it is carried by the
asset's identity in the report, not scored here.

Why there is no dimension layer. Risk has dimensions because the Constitution
fixes them: the kinds of uncertainty are named there, and the category's
coverage is reported against that closed set. The Constitution names no
dimensions for Fundamental. Inventing a taxonomy here would be creating
semantics, which belongs to the Constitution, so the parts of the question are
carried by the measurements themselves and coverage counts measurements.

The parts of "financially sound" that are measured, one measurement each:

* **Profitability** — does the business earn a profit from what it sells?
* **Cash conversion** — does that profit become cash the business can use?
* **Return on capital** — does it earn a return on what its owners committed?
* **Solvency** — can it meet what it owes at all?
* **Short term cover** — can it meet what it owes soon?

What is not measured. Nothing is assessed about the business's competitive
position, its management, its industry, or the durability of its earnings. None
of those has an evidence source connected, and a rule that guessed at them would
be stating an opinion rather than reading evidence. A reader is told how much of
the category was assessed rather than being left to assume it was all of it.

Note on shared evidence. Solvency and short term cover read the same two
measurements the Risk category reads. The questions differ — Fundamental asks
what the state of the business is, Risk asks how exposed a thesis is to it — so
one fact legitimately supports both. Nothing is recorded twice.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.fundamental import (
    cash_conversion_rule,
    profitability_rule,
    return_on_capital_rule,
    short_term_cover_rule,
    solvency_rule,
)
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0


class FundamentalEvaluator(BaseEvaluator):
    """Orchestrates the fundamental rules into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the fundamental rules in order."""
        self._rules = (
            profitability_rule.RULE,
            cash_conversion_rule.RULE,
            return_on_capital_rule.RULE,
            solvency_rule.RULE,
            short_term_cover_rule.RULE,
        )
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.FUNDAMENTAL,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(self._rules),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run every fundamental rule through the rule engine.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            EvaluationResult holding every rule outcome.
        """
        return self._engine.run(self._rules, evidence)

    def evaluate(self, evidence: EvidenceCollection) -> CategoryScore:
        """Execute the rules, normalize their results and assemble the score.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            CategoryScore for the FUNDAMENTAL category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(normalized)
