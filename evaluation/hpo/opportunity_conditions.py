"""The named conditions an opportunity is judged against.

Each condition reads exactly one category and asks a question an investor would
ask before allocating capital. The conditions are named rather than combined
because the AIS Standard Score does not exist: there is no common scale to add
them on, and inventing one here would put a number where there is only a list.

**Where a condition is decided.** Not here. The bar a condition is decided at is
part of what a reading means, so it lives in
:mod:`evaluation.reading.conditions` beside the scales, and the catalyst condition
is decided by a window beside every other window. This module only says which
category answers which question.

That separation is the point of the reading layer: a threshold written here would
be a second opinion about what "attractive" means, and a second opinion is how a
report comes to disagree with itself.

**What no condition does.** None of them reads evidence. Every input is a category
result that has already been reached, which is what keeps HPO a synthesis of
judgements rather than a second opinion about the data.
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
