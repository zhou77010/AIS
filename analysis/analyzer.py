"""AIS asset analyzer.

Orchestrates the complete analysis flow for one asset: market data, evidence,
category score, overall assessment and recommendation. It owns the orchestration
only and contains no business logic.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult
from config.logging_config import get_logger
from contracts.category_evaluator import CategoryEvaluator
from contracts.market_data_provider import MarketDataProvider, MarketDataSnapshot
from core.overall_evaluator import OverallEvaluator
from core.recommendation_engine import RecommendationEngine
from evaluation.earnings.earnings_evaluator import EarningsEvaluator
from evaluation.fundamental.fundamental_evaluator import FundamentalEvaluator
from evaluation.market.market_evaluator import MarketEvaluator
from evaluation.risk.risk_evaluator import RiskEvaluator
from evaluation.trend.trend_evaluator import TrendEvaluator
from evaluation.valuation.valuation_evaluator import ValuationEvaluator
from models.asset import Asset
from models.recommendation import Recommendation
from pipeline.evidence_builder import EvidenceBuilder

_LOGGER_NAME = "analysis"


class AssetAnalyzer:
    """Runs the complete analysis flow for one asset."""

    def __init__(self, market_data_provider: MarketDataProvider | None = None) -> None:
        """Create the analyzer with the components it orchestrates.

        Args:
            market_data_provider: Source live market data is retrieved from, or
                None to run without one. Without a provider the flow stays
                deterministic and builds placeholder evidence, which is how the
                pipeline behaved before live market data existed.
        """
        self._evidence_builder = EvidenceBuilder()
        self._market_data_provider = market_data_provider
        self._category_evaluators: tuple[CategoryEvaluator, ...] = (
            ValuationEvaluator(),
            RiskEvaluator(),
            FundamentalEvaluator(),
            MarketEvaluator(),
            TrendEvaluator(),
            EarningsEvaluator(),
        )
        self._overall_evaluator = OverallEvaluator()
        self._recommendation_engine = RecommendationEngine()
        self._logger = get_logger(_LOGGER_NAME)

    def analyze(self, asset: Asset) -> Recommendation:
        """Analyse one asset and return its recommendation.

        Args:
            asset: Asset to analyse.

        Returns:
            Recommendation reached for the asset.
        """
        return self.analyze_result(asset).recommendation

    def analyze_result(self, asset: Asset) -> AnalysisResult:
        """Run the complete flow and return every stage it produced.

        This is the single orchestration path: every stage is executed exactly
        once per call, in the order the architecture defines.

        Args:
            asset: Asset to analyse.

        Returns:
            AnalysisResult holding the asset, its assessment, its recommendation
            and the market data the run was built on.
        """
        market_data = self._collect_market_data(asset)
        evidence = self._evidence_builder.build(asset, market_data)
        category_scores = tuple(
            evaluator.evaluate(evidence) for evaluator in self._category_evaluators
        )
        assessment = self._overall_evaluator.evaluate(category_scores)
        recommendation = self._recommendation_engine.recommend(assessment)
        return AnalysisResult(
            asset=asset,
            assessment=assessment,
            recommendation=recommendation,
            market_data=market_data,
        )

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
