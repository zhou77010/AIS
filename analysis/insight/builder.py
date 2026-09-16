"""Building the interpretation of every category that has evidence to read.

Each category has one builder, and this module is the only place that knows
which builder answers for which category. A category with no builder is not
interpreted, and a category whose evidence supports nothing comes back empty
rather than filled in.

The builders live on the analysis side of the pipeline and so does this. A
renderer asks for the insight and writes it out; it never composes one, because
composing an interpretation is analysis and showing it is presentation.
"""

from __future__ import annotations

from collections.abc import Callable

from analysis.analysis_result import AnalysisResult
from analysis.insight.catalyst_insight import build as build_catalyst
from analysis.insight.context import InsightContext, context_for
from analysis.insight.earnings_insight import build as build_earnings
from analysis.insight.fundamental_insight import build as build_fundamental
from analysis.insight.market_insight import build as build_market
from analysis.insight.positioning_insight import build as build_positioning
from analysis.insight.risk_insight import build as build_risk
from analysis.insight.trend_insight import build as build_trend
from analysis.insight.valuation_insight import build as build_valuation
from models.category import Category
from models.insight import Insight

_Builder = Callable[[InsightContext], tuple]

# How many sentences one category may write. Three is what a reader will take in
# on a phone; beyond that the report stops being read and starts being skimmed,
# and the fourth sentence is always the least useful of the four.
_MAX_LINES_PER_CATEGORY = 3

# Which builder interprets which category. HPO has none on purpose: it is itself
# an interpretation of the other categories, and interpreting it again would be
# saying the same thing twice.
_BUILDERS: dict[Category, _Builder] = {
    Category.TREND: build_trend,
    Category.RISK: build_risk,
    Category.VALUATION: build_valuation,
    Category.FUNDAMENTAL: build_fundamental,
    Category.MARKET: build_market,
    Category.POSITIONING: build_positioning,
    Category.EARNINGS: build_earnings,
    Category.CATALYST: build_catalyst,
}


def build_insights(result: AnalysisResult) -> tuple[Insight, ...]:
    """Return the interpretation of every category that could be interpreted.

    A category whose builder produced nothing is left out rather than carried as
    an empty entry: an insight that says nothing is not an insight.

    Args:
        result: Analysis result to interpret.

    Returns:
        One insight per category that had something to say.
    """
    insights = (
        Insight(
            category=category,
            lines=tuple(builder(context_for(result, category)))[
                :_MAX_LINES_PER_CATEGORY
            ],
        )
        for category, builder in _BUILDERS.items()
    )
    return tuple(insight for insight in insights if not insight.is_empty)


def insight_for(result: AnalysisResult, category: Category) -> Insight | None:
    """Return the interpretation of one category, or None when there is none.

    Args:
        result: Analysis result to read.
        category: Category to look up.

    Returns:
        The insight recorded for the category, or None when none was built.
    """
    for insight in result.insights:
        if insight.category is category:
            return insight
    return None
