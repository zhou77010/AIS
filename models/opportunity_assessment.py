"""The opportunity judgement reached for one asset.

HPO answers a different question from the eight factual categories: not what is
known, but whether what is known adds up to an opportunity worth allocating
capital to today.

It is built from **named conditions** rather than from a combined number. Each
condition reads one category and reports whether it holds, does not hold, or
could not be judged at all. A condition that could not be judged is kept and
reported as such: it is not folded into the others, and it is not treated as
having failed.

Nothing here is weighted and nothing is normalized. The conditions are counted,
because counting named conditions is something a reader can check, and a combined
score on an undefined scale is not.

This model holds the outcome. How a condition is decided belongs to the evaluator
that decides it, and how it is worded belongs to the renderer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OpportunityCondition(StrEnum):
    """A named condition an opportunity is judged against.

    The set is deliberately small and each member reads exactly one category, so
    that a condition which does not hold can be traced to the category that said
    so.
    """

    VALUATION = "valuation"
    TREND = "trend"
    RISK = "risk"
    CATALYST = "catalyst"
    POSITIONING = "positioning"


@dataclass(frozen=True)
class OpportunityConditionResult:
    """One named condition, as it was decided.

    Attributes:
        condition: Condition that was decided.
        grade: Grade the condition was read from, or None when the category it
            reads had no grade to read.
        satisfied: Whether the condition holds, or None when it could not be
            judged. None is not a failure: it says the question was not answered
            rather than that the answer was no.
    """

    condition: OpportunityCondition
    grade: int | None
    satisfied: bool | None


@dataclass(frozen=True)
class OpportunityAssessment:
    """What the opportunity conditions amount to for one asset.

    Attributes:
        grade: How many of the answered conditions hold, on the same one to five
            scale a category grade uses, or None when no condition could be
            judged. It is a count and not a score: it says how many named
            conditions were met, and it cannot be compared with a category grade.
        summary: One line stating what holds and what does not, for logs and for
            any renderer that needs the facts without the wording.
        conditions: Every condition, in a stable order, whether it was judged or
            not.
    """

    grade: int | None
    summary: str
    conditions: tuple[OpportunityConditionResult, ...]

    @property
    def satisfied(self) -> tuple[OpportunityConditionResult, ...]:
        """Return the conditions that hold."""
        return tuple(result for result in self.conditions if result.satisfied is True)

    @property
    def unsatisfied(self) -> tuple[OpportunityConditionResult, ...]:
        """Return the conditions that were judged and do not hold."""
        return tuple(result for result in self.conditions if result.satisfied is False)

    @property
    def unknown(self) -> tuple[OpportunityConditionResult, ...]:
        """Return the conditions that could not be judged."""
        return tuple(result for result in self.conditions if result.satisfied is None)

    @property
    def is_complete(self) -> bool:
        """Return whether every condition was judged."""
        return not self.unknown
