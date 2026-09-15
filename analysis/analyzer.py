"""AIS asset analyzer.

Orchestrates the complete analysis flow for one asset: evidence, category score,
overall assessment and recommendation. It owns the orchestration only and
contains no business logic.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult
from core.overall_evaluator import OverallEvaluator
from core.recommendation_engine import RecommendationEngine
from evaluation.valuation.valuation_evaluator import ValuationEvaluator
from models.asset import Asset
from models.recommendation import Recommendation
from pipeline.evidence_builder import EvidenceBuilder


class AssetAnalyzer:
    """Runs the complete analysis flow for one asset."""

    def __init__(self) -> None:
        """Create the analyzer with the components it orchestrates."""
        self._evidence_builder = EvidenceBuilder()
        self._category_evaluator = ValuationEvaluator()
        self._overall_evaluator = OverallEvaluator()
        self._recommendation_engine = RecommendationEngine()

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
            AnalysisResult holding the asset, its assessment and its
            recommendation.
        """
        evidence = self._evidence_builder.build(asset)
        category_score = self._category_evaluator.evaluate(evidence)
        assessment = self._overall_evaluator.evaluate((category_score,))
        recommendation = self._recommendation_engine.recommend(assessment)
        return AnalysisResult(
            asset=asset,
            assessment=assessment,
            recommendation=recommendation,
        )
