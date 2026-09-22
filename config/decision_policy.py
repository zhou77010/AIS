"""The first, provisional Decision Policy: the bars the Decision Layer applies.

**This module holds numbers and no logic.** It is the first piece of Policy the Decision
Methodology asked for: the methodology requires that each Required Condition is
evaluated, and it deliberately does not say how. That "how" is here, separated on
purpose
so that changing a bar never means editing a method.

**It is provisional, and provisional in one specific way.** The bars below are not newly
invented: they are the bars the Runtime already applies to the same two questions,
reused
so that the Decision Layer does not introduce a second opinion about what "reads well"
means while the Reading Layer is the owner of that meaning. Two consequences are
accepted
for now and recorded rather than solved:

* they were chosen for an opportunity judgement rather than for this one, so the answer
  they produce will be roughly as selective as that judgement was;
* the risk judgement is thin today, because several risk dimensions are not assessed at
  all, which makes the risk condition easier to satisfy now than it will be later.

The point of this file is to let AIS run and be observed. It is expected to be revised
from observed data, not argued into correctness here.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.category import Category
from models.decision_result import DecisionCondition


@dataclass(frozen=True)
class ConditionBar:
    """The bar one Required Condition is evaluated against.

    Attributes:
        least_mean: The reading's mean step must reach this.
        least_weakest: And no single reading may fall below this, because a category
        that
            reads well on average while holding a disqualifying measurement has not been
            read well.
    """

    least_mean: int
    least_weakest: int


# Which category answers which condition. It is a Policy choice, not a meaning: the
# condition says what must exist, and this says where it is read from.
CONDITION_CATEGORY: dict[DecisionCondition, Category] = {
    DecisionCondition.TERMS: Category.VALUATION,
    DecisionCondition.RISK: Category.RISK,
}

# The bar for each condition. The exchange condition reuses the bar the Runtime already
# applies to a valuation, and the risk condition reuses the bar it already applies to
# risk, so that nothing here is a second opinion.
BARS: dict[DecisionCondition, ConditionBar] = {
    DecisionCondition.TERMS: ConditionBar(least_mean=4, least_weakest=3),
    DecisionCondition.RISK: ConditionBar(least_mean=3, least_weakest=3),
}
