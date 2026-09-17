"""Opportunity assessor.

Turns what the categories read into an opportunity judgement.

It reads nothing but category readings. No evidence is looked at again, no
measurement is re-read, and no source is consulted: everything here is a statement
about judgements that have already been made, which is what makes HPO a synthesis
rather than a ninth opinion about the data.

Nothing is weighted and nothing is normalized. Each condition either holds, does
not hold, or could not be judged, and the grade is how many of the judged
conditions hold — counted, not combined. A condition that could not be judged is
left out of that count and reported by name, because counting it as a failure
would state that a question which was never asked was answered no.

Where each bar sits is not decided here. It lives in the reading layer, so that a
condition and the sentence underneath it cannot disagree about what a category
reading means.
"""

from __future__ import annotations

from collections.abc import Mapping

from evaluation.hpo.opportunity_conditions import CONDITION_CATEGORY
from evaluation.reading.category import CategoryReading
from evaluation.reading.conditions import meets_condition
from evaluation.reading.windows import catalyst_score, is_near_term
from models.category import Category
from models.opportunity_assessment import (
    OpportunityAssessment,
    OpportunityCondition,
    OpportunityConditionResult,
)

# The scale the counted conditions are shown on, matching the category grade. It
# is a count of conditions and not a score: the two are never compared.
_MAX_GRADE = 5


class OpportunityAssessor:
    """Reaches an opportunity judgement from what the categories read."""

    def assess(
        self,
        readings: Mapping[Category, CategoryReading],
        catalyst_days: int | None = None,
    ) -> OpportunityAssessment:
        """Return the opportunity judgement for the readings given.

        Args:
            readings: What each category's measurements read as, keyed by
                category. A category that is absent or read nothing is reported
                as not judged rather than as having failed.
            catalyst_days: How far away the nearest event that could change a view
                is, or None when there is none. It is a distance rather than a
                reading, because a date is not a measurement that fits a snapshot.

        Returns:
            OpportunityAssessment carrying every condition and the count of the
            ones that hold.
        """
        results = tuple(
            _decide(condition, readings.get(category), catalyst_days)
            for condition, category in CONDITION_CATEGORY.items()
        )
        answered = [result for result in results if result.satisfied is not None]
        held = [result for result in answered if result.satisfied]
        return OpportunityAssessment(
            grade=(round(_MAX_GRADE * len(held) / len(answered)) if answered else None),
            summary=_summary(results, len(held), len(answered)),
            conditions=results,
        )


def _decide(
    condition: OpportunityCondition,
    reading: CategoryReading | None,
    catalyst_days: int | None,
) -> OpportunityConditionResult:
    """Return one condition decided against what its category read."""
    if condition is OpportunityCondition.CATALYST:
        return _decide_catalyst(condition, catalyst_days)
    if reading is None or reading.is_empty:
        return OpportunityConditionResult(
            condition=condition, grade=None, satisfied=None
        )
    return OpportunityConditionResult(
        condition=condition,
        grade=reading.mean_score,
        satisfied=meets_condition(reading.category, reading),
    )


def _decide_catalyst(
    condition: OpportunityCondition, catalyst_days: int | None
) -> OpportunityConditionResult:
    """Return the catalyst condition decided against the nearest event.

    The bar is the near term window, which is the same window the catalyst
    sentence reads. When the two were separate numbers, a report could say an
    asset had a near term catalyst above a sentence saying there was no clear
    catalyst in the near term — about the same calendar, from the same run.
    """
    if catalyst_days is None:
        return OpportunityConditionResult(
            condition=condition, grade=None, satisfied=None
        )
    return OpportunityConditionResult(
        condition=condition,
        grade=catalyst_score(catalyst_days),
        satisfied=is_near_term(catalyst_days),
    )


def _summary(
    results: tuple[OpportunityConditionResult, ...], held: int, answered: int
) -> str:
    """Return one line stating what holds and what does not, without wording."""
    met = ", ".join(result.condition.value for result in results if result.satisfied)
    missing = ", ".join(
        result.condition.value for result in results if result.satisfied is False
    )
    unknown = ", ".join(
        result.condition.value for result in results if result.grade is None
    )

    parts = [f"{held} of {answered} judged conditions hold"]
    if met:
        parts.append(f"holds: {met}")
    if missing:
        parts.append(f"does not hold: {missing}")
    if unknown:
        parts.append(f"not judged: {unknown}")
    return "; ".join(parts)
