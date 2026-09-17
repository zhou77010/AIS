"""Tests for the opportunity assessor.

HPO is not a ninth reading of the data. It reads what the categories already read,
decides a small set of named conditions from them, and counts how many hold. These
tests describe that: what makes a condition hold, that a condition which could not
be judged is not counted as a failure, and that the outcome is a count and not a
combined score.
"""

from __future__ import annotations

import pytest

from contracts.market_data_provider import MarketMetric
from evaluation.hpo.opportunity_assessor import OpportunityAssessor
from evaluation.hpo.opportunity_conditions import CONDITION_CATEGORY
from evaluation.reading.bands import Band
from evaluation.reading.category import CategoryReading, MetricRead
from evaluation.reading.conditions import OPPORTUNITY_CONDITIONS
from evaluation.reading.windows import CATALYST_NEAR_TERM_SCORE, NEAR_TERM_DAYS
from models.category import Category
from models.opportunity_assessment import OpportunityCondition

_ASSESSOR = OpportunityAssessor()


def _reading(category: Category, scores: tuple[int, ...]) -> CategoryReading:
    """Return a reading carrying the given scores, one per measurement."""
    return CategoryReading(
        category=category,
        reads=tuple(
            MetricRead(
                metric=MarketMetric.PE,
                value=0.0,
                band=Band(threshold=0.0, word="word"),
                score=score,
            )
            for score in scores
        ),
    )


def _all_strong() -> dict[Category, CategoryReading]:
    """Return readings that clear every metric condition."""
    return {
        Category.VALUATION: _reading(Category.VALUATION, (5, 5, 5, 4)),
        Category.TREND: _reading(Category.TREND, (5, 4, 4)),
        Category.RISK: _reading(Category.RISK, (4, 3, 3)),
        Category.POSITIONING: _reading(Category.POSITIONING, (4, 3)),
    }


def _condition(assessment, condition: OpportunityCondition):
    return next(
        entry for entry in assessment.conditions if entry.condition is condition
    )


# --------------------------------------------------------------------------
# Which categories it reads
# --------------------------------------------------------------------------


def test_every_condition_reads_exactly_one_category() -> None:
    read = list(CONDITION_CATEGORY.values())

    assert len(read) == len(set(read))


def test_every_metric_condition_has_a_bar() -> None:
    # The catalyst is decided by a window rather than by a bar, so it is the one
    # condition that is not in the table.
    metric_conditions = {
        category
        for category in CONDITION_CATEGORY.values()
        if category is not Category.CATALYST
    }

    assert metric_conditions == set(OPPORTUNITY_CONDITIONS)


def test_the_assessor_is_deterministic() -> None:
    readings = _all_strong()

    assert _ASSESSOR.assess(readings, catalyst_days=3) == _ASSESSOR.assess(
        readings, catalyst_days=3
    )


# --------------------------------------------------------------------------
# When a condition holds
# --------------------------------------------------------------------------


def test_every_condition_holds_when_every_category_reads_well() -> None:
    assessment = _ASSESSOR.assess(_all_strong(), catalyst_days=3)

    assert len(assessment.satisfied) == len(CONDITION_CATEGORY)


@pytest.mark.parametrize("category", sorted(OPPORTUNITY_CONDITIONS))
def test_a_condition_does_not_hold_when_the_mean_falls_short(
    category: Category,
) -> None:
    bar = OPPORTUNITY_CONDITIONS[category]

    assessment = _ASSESSOR.assess(
        {category: _reading(category, (bar.least_mean - 1,) * 4)}
    )

    assert (
        _condition(assessment, OpportunityCondition(category.value)).satisfied is False
    )


@pytest.mark.parametrize("category", sorted(OPPORTUNITY_CONDITIONS))
def test_a_condition_does_not_hold_when_one_reading_disqualifies_it(
    category: Category,
) -> None:
    # This is the clause the report was missing. A category that reads well on
    # average while holding a measurement at the bottom of its scale has not
    # cleared the bar: the question is whether the category reads well, not whether
    # it reads well on balance.
    bar = OPPORTUNITY_CONDITIONS[category]
    scores = (5, 5, 5, bar.least_weakest - 1)

    assessment = _ASSESSOR.assess({category: _reading(category, scores)})

    assert (
        _condition(assessment, OpportunityCondition(category.value)).satisfied is False
    )


def test_a_category_that_read_nothing_is_not_counted_as_a_failure() -> None:
    readings = _all_strong()
    readings[Category.VALUATION] = _reading(Category.VALUATION, ())

    assessment = _ASSESSOR.assess(readings, catalyst_days=3)

    assert _condition(assessment, OpportunityCondition.VALUATION).satisfied is None
    assert len(assessment.unknown) == 1


# --------------------------------------------------------------------------
# The catalyst reads a window, not a mean
# --------------------------------------------------------------------------


def test_a_catalyst_inside_the_near_term_holds() -> None:
    assessment = _ASSESSOR.assess(_all_strong(), catalyst_days=NEAR_TERM_DAYS)
    catalyst = _condition(assessment, OpportunityCondition.CATALYST)

    assert catalyst.satisfied is True
    assert catalyst.grade == CATALYST_NEAR_TERM_SCORE


def test_a_catalyst_outside_the_near_term_does_not_hold() -> None:
    # The bar and the sentence underneath it read one window, so a report can no
    # longer claim a near term catalyst above a sentence saying there is no clear
    # catalyst in the near term.
    assessment = _ASSESSOR.assess(_all_strong(), catalyst_days=NEAR_TERM_DAYS + 1)

    assert _condition(assessment, OpportunityCondition.CATALYST).satisfied is False


def test_no_catalyst_at_all_is_not_judged_rather_than_failed() -> None:
    assessment = _ASSESSOR.assess(_all_strong(), catalyst_days=None)

    assert _condition(assessment, OpportunityCondition.CATALYST).satisfied is None


# --------------------------------------------------------------------------
# What the count means
# --------------------------------------------------------------------------


def test_every_condition_holding_reads_at_the_top_of_the_scale() -> None:
    assert _ASSESSOR.assess(_all_strong(), catalyst_days=3).grade == 5


def test_the_grade_counts_the_conditions_that_hold() -> None:
    readings = _all_strong()
    readings[Category.VALUATION] = _reading(Category.VALUATION, (2, 1, 2))

    assessment = _ASSESSOR.assess(readings, catalyst_days=3)

    assert assessment.grade == 4
    assert len(assessment.unsatisfied) == 1


def test_a_condition_that_could_not_be_judged_is_left_out_of_the_count() -> None:
    # Four conditions hold and the catalyst could not be judged, so the count is
    # of what was judged and the unknown one is reported rather than counted.
    assessment = _ASSESSOR.assess(_all_strong(), catalyst_days=None)

    assert assessment.grade == 5
    assert assessment.is_complete is False


def test_no_grade_is_given_when_no_condition_could_be_judged() -> None:
    assessment = _ASSESSOR.assess({}, catalyst_days=None)

    assert assessment.grade is None
    assert len(assessment.unknown) == len(OpportunityCondition)


def test_the_summary_states_what_holds_and_what_does_not() -> None:
    readings = _all_strong()
    readings[Category.VALUATION] = _reading(Category.VALUATION, (1, 1))

    summary = _ASSESSOR.assess(readings, catalyst_days=3).summary

    assert "hold" in summary
    assert "does not hold: valuation" in summary


def test_the_summary_names_the_conditions_that_could_not_be_judged() -> None:
    readings = _all_strong()
    del readings[Category.RISK]

    summary = _ASSESSOR.assess(readings, catalyst_days=3).summary

    assert "not judged: risk" in summary
