"""The named conditions an opportunity is judged against.

Each condition reads exactly one category and asks a question an investor would
ask before allocating capital. The conditions are named rather than combined
because the AIS Standard Score does not exist: there is no common scale to add
them on, and inventing one here would put a number where there is only a list.

Where a condition is decided. Each reads the provisional grade of its category,
which is itself read from conventional bands. HPO therefore inherits the
provisionality of that grade and is to be revisited when the standard score
defines what a category reading means. It is recorded here rather than hidden:
the alternative — waiting for the standard score — would leave the question
unanswered for as long as the score is undefined.

What no condition does. None of them reads evidence again. Every input is a
category result that has already been reached, which is what keeps HPO a
synthesis of judgements rather than a second opinion about the data.
"""

from __future__ import annotations

from models.category import Category
from models.opportunity_assessment import OpportunityCondition

# The category each condition reads. One condition, one category, so that a
# condition which does not hold names the category that said so.
CONDITION_CATEGORY: dict[OpportunityCondition, Category] = {
    OpportunityCondition.VALUATION: Category.VALUATION,
    OpportunityCondition.TREND: Category.TREND,
    OpportunityCondition.RISK: Category.RISK,
    OpportunityCondition.CATALYST: Category.CATALYST,
    OpportunityCondition.POSITIONING: Category.POSITIONING,
}

# The grade at which a condition starts to hold. These are thresholds on a
# provisional presentation grade and not on a measurement: valuation at four or
# above reads cheap, risk at three or above reads acceptable. They are the
# simplest thing that can be explained, and they are to be replaced together with
# the grade they read.
SATISFIED_FROM: dict[OpportunityCondition, int] = {
    OpportunityCondition.VALUATION: 4,
    OpportunityCondition.TREND: 4,
    OpportunityCondition.RISK: 3,
    OpportunityCondition.CATALYST: 3,
    OpportunityCondition.POSITIONING: 3,
}
