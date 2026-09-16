"""Tests for the category assembler (Sprint 9)."""

from __future__ import annotations

from evaluation.category_assembler import CategoryAssembler
from evaluation.normalized_score import NormalizedScore
from models.category import Category
from models.category_score import CategoryScore


def _normalized(value: float, reason: str, reference: str) -> NormalizedScore:
    """Return a normalized score for the given value, reason and reference."""
    return NormalizedScore(
        raw_value=value,
        normalized_value=value,
        confidence=1.0,
        reason=reason,
        evidence_references=(reference,),
    )


def _assembler(confidence: float = 1.0, total_units: int = 5) -> CategoryAssembler:
    """Return an assembler bound to the VALUATION category."""
    return CategoryAssembler(
        category=Category.VALUATION, confidence=confidence, total_units=total_units
    )


def test_assembles_a_category_score_for_the_configured_category() -> None:
    score = _assembler().assemble((_normalized(2.0, "a measured 2.0", "ref-a"),))

    assert isinstance(score, CategoryScore)
    assert score.category is Category.VALUATION
    assert score.confidence == 1.0


def test_the_assembled_score_reports_how_much_of_the_category_was_assessed() -> None:
    score = _assembler(total_units=5).assemble(
        (
            _normalized(2.0, "a measured 2.0", "ref-a"),
            _normalized(3.0, "b measured 3.0", "ref-b"),
        )
    )

    assert score.coverage.assessed == 2
    assert score.coverage.total == 5
    assert score.coverage.is_complete is False


def test_the_assembled_score_accepts_a_coverage_the_caller_counts_itself() -> None:
    # Risk has four rules covering three dimensions, so counting scores would
    # overstate what was assessed.
    score = _assembler(total_units=8).assemble(
        (
            _normalized(2.0, "a measured 2.0", "ref-a"),
            _normalized(3.0, "b measured 3.0", "ref-b"),
        ),
        assessed=1,
    )

    assert score.coverage.describe() == "1/8"


def test_aggregates_normalized_values_as_placeholder_mean() -> None:
    score = _assembler().assemble(
        (
            _normalized(1.0, "a measured 1.0", "ref-a"),
            _normalized(3.0, "b measured 3.0", "ref-b"),
        )
    )

    assert score.score == 2.0


def test_aggregates_normalized_values_and_ignores_raw_values() -> None:
    scores = (
        NormalizedScore(
            raw_value=100.0, normalized_value=1.0, confidence=1.0, reason="a"
        ),
        NormalizedScore(
            raw_value=200.0, normalized_value=3.0, confidence=1.0, reason="b"
        ),
    )

    assert _assembler().assemble(scores).score == 2.0


def test_summary_preserves_rule_order() -> None:
    score = _assembler().assemble(
        (
            _normalized(1.0, "a measured 1.0", "ref-a"),
            _normalized(3.0, "b measured 3.0", "ref-b"),
        )
    )

    assert score.summary == "a measured 1.0; b measured 3.0"


def test_evidence_references_are_merged_and_deduplicated() -> None:
    score = _assembler().assemble(
        (
            _normalized(1.0, "a measured 1.0", "ref-a"),
            _normalized(3.0, "b measured 3.0", "ref-a"),
        )
    )

    assert score.evidence_references == ("ref-a",)


def test_empty_scores_produce_an_empty_score() -> None:
    score = _assembler(confidence=0.5).assemble(())

    assert score.score == 0.0
    assert score.summary == ""
    assert score.evidence_references == ()
    assert score.confidence == 0.5


def test_repeated_assembly_is_deterministic() -> None:
    assembler = _assembler()
    scores = (
        _normalized(1.0, "a measured 1.0", "ref-a"),
        _normalized(3.0, "b measured 3.0", "ref-b"),
    )

    assert assembler.assemble(scores) == assembler.assemble(scores)
