"""The bar each opportunity condition is decided at.

An opportunity condition asks whether a category reads well enough to be worth
allocating to. What "well enough" means is written here, once, and it is asked of
the category's own reading rather than of a rounded star.

**Two bars, not one.** A condition needs the category to read well on average and
to hold nothing that disqualifies it. One bar was not enough, and the failure was
visible in public: a valuation whose multiples were generous averaged out to
attractive while one of its measurements read at the bottom of its scale, so the
report claimed an attractive valuation directly above a sentence saying the cash
flow did not support it. The average was not wrong; it was answering a different
question from the one the sentence was about.

**Catalyst is not decided here.** It is a date rather than a measurement, so its
bar is a window, and the window lives in
:mod:`evaluation.reading.windows` beside every other window.
"""

from __future__ import annotations

from dataclasses import dataclass

from evaluation.reading.category import CategoryReading
from models.category import Category


@dataclass(frozen=True)
class CategoryCondition:
    """The bar one category must clear for an opportunity condition to hold.

    Attributes:
        least_mean: The rounded mean of the category's readings must reach this.
        least_weakest: And no single reading may fall below this. A category that
            reads well on average while holding a disqualifying measurement has
            not cleared the bar: the question the condition asks is whether the
            category reads well, not whether it reads well on balance.
    """

    least_mean: int
    least_weakest: int


OPPORTUNITY_CONDITIONS: dict[Category, CategoryCondition] = {
    Category.VALUATION: CategoryCondition(least_mean=4, least_weakest=3),
    Category.TREND: CategoryCondition(least_mean=4, least_weakest=3),
    Category.RISK: CategoryCondition(least_mean=3, least_weakest=3),
    Category.POSITIONING: CategoryCondition(least_mean=3, least_weakest=3),
}

# How the weakest bar is chosen, so that it is a rule and not a preference: **it is
# set so that no sentence denying the condition can fire.** A condition says a
# category reads well; a sentence drawn from the same readings must not be able to
# say it does not. The denying sentences are the ones keyed to the bottom two bands,
# so the bar is three: nothing the category reads may be in the bottom two.
#
# That is what the bar is for, and it is why the sentences below it had to be moved
# as well. `tests/test_report_consistency.py` holds both ends of it.


def meets_condition(category: Category, reading: CategoryReading) -> bool | None:
    """Return whether a category clears its bar, or None when it was not read.

    Args:
        category: Category the condition is about.
        reading: The category's own reading.

    Returns:
        True when the condition holds, False when it does not, and None when
        nothing about the category could be read. None is not a failure: it says
        the question was not answered rather than that the answer was no.
    """
    condition = OPPORTUNITY_CONDITIONS.get(category)
    if condition is None or reading.is_empty:
        return None
    mean = reading.mean_score
    weakest = reading.weakest_score
    if mean is None or weakest is None:
        return None
    return mean >= condition.least_mean and weakest >= condition.least_weakest
