"""Opportunity assessor.

Turns the grades the categories already reached into an opportunity judgement.

It reads nothing but grades. No evidence is looked at again, no measurement is
re-read, and no source is consulted: everything here is a statement about
judgements that have already been made, which is what makes HPO a synthesis
rather than a ninth opinion about the data.

Nothing is weighted and nothing is normalized. Each condition either holds,
does not hold, or could not be judged, and the grade is how many of the judged
conditions hold — counted, not combined. A condition that could not be judged is
left out of that count and reported by name, because counting it as a failure
would state that a question which was never asked was answered no.
"""

from __future__ import annotations

from collections.abc import Mapping

from evaluation.hpo.opportunity_conditions import CONDITION_CATEGORY, SATISFIED_FROM
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
    """Reaches an opportunity judgement from the grades of the eight categories."""

    def assess(self, grades: Mapping[Category, int | None]) -> OpportunityAssessment:
        """Return the opportunity judgement for the grades given.

        Args:
            grades: The grade reached for each category, or None for a category
                that was not graded at all.

        Returns:
            OpportunityAssessment carrying every condition and the count of the
            ones that hold.
        """
        results = tuple(
            _decide(condition, grades.get(CONDITION_CATEGORY[condition]))
            for condition in OpportunityCondition
        )
        answered = [result for result in results if result.satisfied is not None]
        held = [result for result in answered if result.satisfied]
        return OpportunityAssessment(
            grade=(round(_MAX_GRADE * len(held) / len(answered)) if answered else None),
            summary=_summary(results, len(held), len(answered)),
            conditions=results,
        )


def _decide(
    condition: OpportunityCondition, grade: int | None
) -> OpportunityConditionResult:
    """Return one condition decided against the grade it reads."""
    if grade is None:
        return OpportunityConditionResult(
            condition=condition, grade=None, satisfied=None
        )
    return OpportunityConditionResult(
        condition=condition,
        grade=grade,
        satisfied=grade >= SATISFIED_FROM[condition],
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
