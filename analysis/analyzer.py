"""AIS asset analyzer.

Orchestrates the complete analysis flow for one asset: market data, evidence,
category score, overall assessment and recommendation. It owns the orchestration
only and contains no business logic.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from analysis.analysis_result import AnalysisResult
from analysis.category_grade import catalyst_days, grade_for_category, reading_for
from analysis.insight.builder import build_insights, insight_for
from analysis.plain_language import measurements_of
from app.rating_tracker import RatingTracker
from config.logging_config import get_logger
from contracts.catalyst_event_provider import CatalystEventProvider
from contracts.category_evaluator import CategoryEvaluator
from contracts.market_data_provider import MarketDataProvider, MarketDataSnapshot
from contracts.market_environment import EnvironmentSnapshot
from core.overall_evaluator import OverallEvaluator
from core.recommendation_engine import RecommendationEngine
from evaluation.catalyst.catalyst_evaluator import CatalystEvaluator
from evaluation.decision.decision_assessor import DecisionAssessor
from evaluation.earnings.earnings_evaluator import EarningsEvaluator
from evaluation.fundamental.fundamental_evaluator import FundamentalEvaluator
from evaluation.hpo.opportunity_assessor import OpportunityAssessor
from evaluation.market.market_evaluator import MarketEvaluator
from evaluation.positioning.positioning_evaluator import PositioningEvaluator
from evaluation.risk.risk_evaluator import RiskEvaluator
from evaluation.trend.trend_evaluator import TrendEvaluator
from evaluation.valuation.valuation_evaluator import ValuationEvaluator
from models.asset import Asset
from models.catalyst_event import CatalystEvent
from models.category import Category
from models.category_rating import CategoryRating
from models.opportunity_assessment import OpportunityAssessment
from models.recommendation import Recommendation
from pipeline.evidence_builder import EvidenceBuilder

_LOGGER_NAME = "analysis"


class AssetAnalyzer:
    """Runs the complete analysis flow for one asset."""

    def __init__(
        self,
        market_data_provider: MarketDataProvider | None = None,
        rating_tracker: RatingTracker | None = None,
        event_provider: CatalystEventProvider | None = None,
    ) -> None:
        """Create the analyzer with the components it orchestrates.

        Args:
            market_data_provider: Source live market data is retrieved from, or
                None to run without one. Without a provider the flow stays
                deterministic and builds placeholder evidence, which is how the
                pipeline behaved before live market data existed.
            rating_tracker: Holder of where each category stood last time, or
                None to run without one. Without a tracker the result carries no
                ratings, because a rating is about successive runs and a single
                run does not know the previous one.
            event_provider: Source dated catalyst events are retrieved from, or
                None to run without one. Without a provider the catalyst
                category finds no forthcoming event and says so, which is the
                truth rather than a placeholder.
        """
        self._evidence_builder = EvidenceBuilder()
        self._market_data_provider = market_data_provider
        self._rating_tracker = rating_tracker
        self._event_provider = event_provider
        self._category_evaluators: tuple[CategoryEvaluator, ...] = (
            ValuationEvaluator(),
            RiskEvaluator(),
            FundamentalEvaluator(),
            MarketEvaluator(),
            TrendEvaluator(),
            EarningsEvaluator(),
            CatalystEvaluator(),
            PositioningEvaluator(),
        )
        self._overall_evaluator = OverallEvaluator()
        self._recommendation_engine = RecommendationEngine()
        self._opportunity_assessor = OpportunityAssessor()
        self._logger = get_logger(_LOGGER_NAME)

    def analyze(self, asset: Asset) -> Recommendation:
        """Analyse one asset and return its recommendation.

        Args:
            asset: Asset to analyse.

        Returns:
            Recommendation reached for the asset.
        """
        return self.analyze_result(asset).recommendation

    def analyze_result(
        self, asset: Asset, *, environment: EnvironmentSnapshot | None = None
    ) -> AnalysisResult:
        """Run the complete flow and return every stage it produced.

        This is the single orchestration path: every stage is executed exactly
        once per call, in the order the architecture defines.

        Args:
            asset: Asset to analyse.
            environment: The environment the asset is being judged in, or None when
                none was retrieved. It is retrieved once per pass and shared by
                every asset in it, so it is handed in rather than fetched here:
                fetching it per asset would fetch one fact once per asset and could
                have the copies disagree.

        Returns:
            AnalysisResult holding the asset, its assessment, its recommendation
            and the market data the run was built on.
        """
        market_data = self._collect_market_data(asset)
        events = self._collect_events(asset)
        evidence = self._evidence_builder.build(asset, market_data, events, environment)
        category_scores = tuple(
            evaluator.evaluate(evidence) for evaluator in self._category_evaluators
        )
        assessment = self._overall_evaluator.evaluate(category_scores)
        recommendation = self._recommendation_engine.recommend(assessment)
        result = AnalysisResult(
            asset=asset,
            assessment=assessment,
            recommendation=recommendation,
            events=events,
            market_data=market_data,
            environment=environment,
        )
        result = replace(result, ratings=self._rate(asset, result))
        result = replace(result, opportunity=self._assess_opportunity(result))
        result = replace(result, decision=DecisionAssessor().assess(result))
        return replace(result, insights=build_insights(result))

    def _assess_opportunity(self, result: AnalysisResult) -> OpportunityAssessment:
        """Return the opportunity judgement for a result just produced.

        The judgement reads what each category's measurements read as, and nothing
        else: no evidence is consulted again, because HPO is a synthesis of
        judgements already reached rather than a second reading of the data. The
        catalyst is passed as a distance rather than as a reading, because a date
        is not a measurement that fits a snapshot.

        Args:
            result: Analysis result just produced.

        Returns:
            Opportunity judgement over the categories that could be read.
        """
        readings = {
            category_score.category: reading_for(result, category_score.category)
            for category_score in result.assessment.category_scores
        }
        return self._opportunity_assessor.assess(readings, catalyst_days(result))

    def _rate(self, asset: Asset, result: AnalysisResult) -> tuple[CategoryRating, ...]:
        """Return the rating of every category a judgement was reached for.

        A category assembled from no rule results carries no evidence and is not
        rated: a grade would say where nothing stands.

        Args:
            asset: Asset the result is about.
            result: Analysis result just produced.

        Returns:
            The ratings, empty when no tracker is in use.
        """
        if self._rating_tracker is None:
            return ()

        moment = datetime.now()
        ratings: list[CategoryRating] = []
        for category_score in result.assessment.category_scores:
            if not category_score.evidence_references:
                continue
            grade = grade_for_category(result, category_score.category)
            if grade is None:
                continue
            reason = _reason_for(result, category_score.category)
            readings = {
                point.metric: point.value
                for point in measurements_of(result, category_score.category)
                if point.value is not None
            }
            ratings.append(
                self._rating_tracker.update(
                    symbol=asset.ticker,
                    category=category_score.category,
                    grade=grade,
                    score=category_score.score,
                    reason=reason,
                    measurements=readings,
                    moment=moment,
                )
            )
        return tuple(ratings)

    def _collect_market_data(self, asset: Asset) -> MarketDataSnapshot | None:
        """Retrieve market data for the asset, or None when no source is set.

        Every metric that could not be retrieved is logged here. The evidence
        records the reason for each one, and the log makes the degradation
        visible in a run, so a missing input never looks like a retrieved one.

        Args:
            asset: Asset to retrieve market data for.

        Returns:
            Snapshot of the retrieved market data, or None when no market data
            provider was configured.
        """
        if self._market_data_provider is None:
            return None
        snapshot = self._market_data_provider.fetch(asset.ticker)
        for point in snapshot.missing_points:
            self._logger.warning(
                "market data unavailable for %s: %s", asset.ticker, point.reason
            )
        return snapshot

    def _collect_events(self, asset: Asset) -> tuple[CatalystEvent, ...]:
        """Retrieve the dated catalyst events known for the asset.

        An empty result is not logged as a failure: a calendar with nothing on it
        and a calendar that could not be reached look the same here, and the
        provider that could not be reached says so in its own log line. What the
        category reports either way is that it found no forthcoming event, which
        is true of both.

        Args:
            asset: Asset to retrieve events for.

        Returns:
            The forthcoming events, empty when no provider was configured or
            nothing was found.
        """
        if self._event_provider is None:
            return ()
        events = self._event_provider.fetch_events(asset.ticker)
        self._logger.info("catalyst events for %s: %d", asset.ticker, len(events))
        return events


def _reason_for(result: AnalysisResult, category: Category) -> str:
    """Return one line saying what a category reads as, for the rating record.

    The interpretation belongs to the insight layer, so this takes its first
    sentence rather than writing one: a reason composed here would be a second
    opinion about what the category means, which is what the reading layer exists
    to prevent. A category the insight layer had nothing to say about falls back to
    the summary the assembler built.
    """
    insight = insight_for(result, category)
    if insight is not None and not insight.is_empty:
        return insight.lines[0].text
    return next(
        (
            score.summary
            for score in result.assessment.category_scores
            if score.category is category
        ),
        "",
    )
