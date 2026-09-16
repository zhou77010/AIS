"""Tests for the opportunity assessor.

HPO is not a ninth reading of the data. It reads the grades the categories
already reached, decides a small set of named conditions from them, and counts
how many hold. These tests describe that: what makes a condition hold, that a
condition which could not be judged is not counted as a failure, and that the
outcome is a count and not a combined score.
"""

from __future__ import annotations

from evaluation.hpo.opportunity_assessor import OpportunityAssessor
from evaluation.hpo.opportunity_conditions import (
    CONDITION_CATEGORY,
    SATISFIED_FROM,
)
from models.category import Category
from models.opportunity_assessment import OpportunityCondition

_ASSESSOR = OpportunityAssessor()

_ALL_HELD = {
    Category.VALUATION: 5,
    Category.TREND: 4,
    Category.RISK: 3,
    Category.CATALYST: 3,
    Category.POSITIONING: 3,
}


def _assessment(**grades: int | None):
    return _ASSESSOR.assess(_ALL_HELD | grades)


# --------------------------------------------------------------------------
# Which categories it reads, and which it does not
# --------------------------------------------------------------------------


def test_every_condition_reads_exactly_one_category() -> None:
    read = list(CONDITION_CATEGORY.values())

    assert len(read) == len(set(read))


def test_every_condition_has_a_threshold() -> None:
    assert set(SATISFIED_FROM) == set(OpportunityCondition)


def test_the_assessor_reads_only_the_grades_it_was_given() -> None:
    # A category that is not part of any condition cannot change the outcome.
    with_market = _assessment(**{Category.MARKET: 5})
    without_market = _assessment()

    assert with_market == without_market


# --------------------------------------------------------------------------
# When a condition holds
# --------------------------------------------------------------------------


def test_a_condition_holds_at_its_threshold() -> None:
    for condition, category in CONDITION_CATEGORY.items():
        assessment = _assessment(**{category: SATISFIED_FROM[condition]})
        result = next(
            entry for entry in assessment.conditions if entry.condition is condition
        )
        assert result.satisfied is True, condition


def test_a_condition_does_not_hold_below_its_threshold() -> None:
    for condition, category in CONDITION_CATEGORY.items():
        assessment = _assessment(**{category: SATISFIED_FROM[condition] - 1})
        result = next(
            entry for entry in assessment.conditions if entry.condition is condition
        )
        assert result.satisfied is False, condition


def test_a_condition_is_not_judged_when_its_category_has_no_grade() -> None:
    assessment = _assessment(**{Category.CATALYST: None})

    assert assessment.unknown[0].condition is OpportunityCondition.CATALYST
    assert assessment.unknown[0].satisfied is None
    assert assessment.unknown[0].grade is None


# --------------------------------------------------------------------------
# What the count means
# --------------------------------------------------------------------------


def test_every_condition_holding_reads_at_the_top_of_the_scale() -> None:
    assert _assessment().grade == 5


def test_the_grade_counts_the_conditions_that_hold() -> None:
    assessment = _assessment(**{Category.VALUATION: 2, Category.TREND: 2})

    assert assessment.grade == 3
    assert len(assessment.satisfied) == 3
    assert len(assessment.unsatisfied) == 2


def test_a_condition_that_could_not_be_judged_is_not_counted_as_a_failure() -> None:
    # One condition unknown, four judged and all four holding: the count is of
    # what was judged, and the unknown one is reported rather than counted.
    assessment = _assessment(
        **{Category.CATALYST: None, Category.VALUATION: 5, Category.TREND: 4}
    )

    assert assessment.grade == 5
    assert len(assessment.satisfied) == 4
    assert assessment.is_complete is False


def test_no_grade_is_given_when_no_condition_could_be_judged() -> None:
    assessment = _ASSESSOR.assess({})

    assert assessment.grade is None
    assert len(assessment.unknown) == len(OpportunityCondition)


def test_the_summary_states_what_holds_and_what_does_not() -> None:
    summary = _assessment(**{Category.VALUATION: 1}).summary

    assert "4 of 5 judged conditions hold" in summary
    assert "does not hold: valuation" in summary
    assert "not judged" not in summary


def test_the_summary_names_the_conditions_that_could_not_be_judged() -> None:
    summary = _assessment(**{Category.RISK: None}).summary

    assert "not judged: risk" in summary


def test_the_assessor_is_deterministic() -> None:
    assert _ASSESSOR.assess(_ALL_HELD) == _ASSESSOR.assess(_ALL_HELD)
