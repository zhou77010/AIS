"""AIS analysis result.

One analysis run of a single asset: the asset itself, the overall assessment
reached for it, and the recommendation derived from that assessment.
"""

from __future__ import annotations

from dataclasses import dataclass

from contracts.market_data_provider import MarketDataSnapshot
from contracts.market_environment import EnvironmentSnapshot
from models.asset import Asset
from models.catalyst_event import CatalystEvent
from models.category import Category
from models.category_rating import CategoryRating
from models.insight import Insight
from models.opportunity_assessment import OpportunityAssessment
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation


@dataclass(frozen=True)
class AnalysisResult:
    """Outcome of one analysis run for a single asset.

    The category scores are not duplicated here: they are reachable through the
    assessment, which is the model that owns them.

    Attributes:
        asset: Asset that was analysed.
        assessment: Overall assessment reached for the asset.
        recommendation: Recommendation derived from the assessment.
        market_data: Market data the analysis was built on, or None when no
            market data source was consulted. It is the input the run started
            from, not a copy of anything the assessment owns, and it is what
            lets the report and the notification state truthfully whether live
            market data was used.
        ratings: Where each category stands and how it has moved inside that
            standing, empty when no rating tracker is in use. A rating is about
            successive runs, so a run that does not know the previous one has
            nothing to say here.
        opportunity: The opportunity judgement reached from the categories, or
            None when the run reached none. It sits beside the assessment rather
            than inside it: the assessment is a composite of the categories, and
            an opportunity built from those same categories would be counted
            twice if it were folded into them.
        events: Dated catalyst events the run was built on, in date order. They
            are the input the catalyst judgement started from, like the market
            data, and the report writes them out so that a reader sees the
            calendar rather than a score about it.
        insights: What the evidence of each category means, one entry per
            category that had something to say. They are built here rather than
            by a renderer, because interpreting evidence is analysis and showing
            it is presentation.
        environment: The environment the run was judged in, or None when no
            environment source was consulted. It is not about this asset — it is
            the same object for every asset analysed in the same pass — and it sits
            here because the Market judgement is made from it beside the asset's
            own measurements. It is the input the run started from, like the market
            data, and the report writes it out once rather than once per asset.
    """

    asset: Asset
    assessment: OverallAssessment
    recommendation: Recommendation
    market_data: MarketDataSnapshot | None = None
    ratings: tuple[CategoryRating, ...] = ()
    opportunity: OpportunityAssessment | None = None
    events: tuple[CatalystEvent, ...] = ()
    insights: tuple[Insight, ...] = ()
    environment: EnvironmentSnapshot | None = None

    def rating_for(self, category: Category) -> CategoryRating | None:
        """Return the rating recorded for one category, or None."""
        for rating in self.ratings:
            if rating.category is category:
                return rating
        return None
