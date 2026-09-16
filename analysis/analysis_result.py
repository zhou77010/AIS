"""AIS analysis result.

One analysis run of a single asset: the asset itself, the overall assessment
reached for it, and the recommendation derived from that assessment.
"""

from __future__ import annotations

from dataclasses import dataclass

from contracts.market_data_provider import MarketDataSnapshot
from models.asset import Asset
from models.category import Category
from models.category_rating import CategoryRating
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
    """

    asset: Asset
    assessment: OverallAssessment
    recommendation: Recommendation
    market_data: MarketDataSnapshot | None = None
    ratings: tuple[CategoryRating, ...] = ()

    def rating_for(self, category: Category) -> CategoryRating | None:
        """Return the rating recorded for one category, or None."""
        for rating in self.ratings:
            if rating.category is category:
                return rating
        return None
