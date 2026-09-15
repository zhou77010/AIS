"""Tests for the category assembler (Sprint 9)."""

from __future__ import annotations

from evaluation.category_assembler import CategoryAssembler
from evaluation.rule_result import RuleResult
from models.category import Category
from models.category_score import CategoryScore


def _result(rule_id: str, score: float, reference: str) -> RuleResult:
    """Return a rule result for the given rule, score and reference."""
    return RuleResult(
        rule_id=rule_id,
        score=score,
        reason=f"{rule_id} measured {score}",
        evidence_references=(reference,),
    )


def _assembler(confidence: float = 1.0) -> CategoryAssembler:
    """Return an assembler bound to the VALUATION category."""
    return CategoryAssembler(category=Category.VALUATION, confidence=confidence)


def test_assembles_a_category_score_for_the_configured_category() -> None:
    score = _assembler().assemble((_result("a", 2.0, "ref-a"),))

    assert isinstance(score, CategoryScore)
    assert score.category is Category.VALUATION
    assert score.confidence == 1.0


def test_aggregates_normalized_scores_as_placeholder_mean() -> None:
    score = _assembler().assemble(
        (_result("a", 1.0, "ref-a"), _result("b", 3.0, "ref-b"))
    )

    assert score.score == 2.0


def test_summary_preserves_rule_order() -> None:
    score = _assembler().assemble(
        (_result("a", 1.0, "ref-a"), _result("b", 3.0, "ref-b"))
    )

    assert score.summary == "a measured 1.0; b measured 3.0"


def test_evidence_references_are_merged_and_deduplicated() -> None:
    score = _assembler().assemble(
        (_result("a", 1.0, "ref-a"), _result("b", 3.0, "ref-a"))
    )

    assert score.evidence_references == ("ref-a",)


def test_empty_results_produce_an_empty_score() -> None:
    score = _assembler(confidence=0.5).assemble(())

    assert score.score == 0.0
    assert score.summary == ""
    assert score.evidence_references == ()
    assert score.confidence == 0.5


def test_repeated_assembly_is_deterministic() -> None:
    assembler = _assembler()
    results = (_result("a", 1.0, "ref-a"), _result("b", 3.0, "ref-b"))

    assert assembler.assemble(results) == assembler.assemble(results)
