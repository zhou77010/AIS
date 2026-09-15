"""Runnable demonstration of the complete investment decision pipeline.

Run with: ``python -m core.demo``.

Executes the first vertical slice: an asset becomes evidence, the evidence
becomes a category score, the category score becomes an overall assessment, and
the assessment becomes a recommendation. Every stage is logged.
"""

from __future__ import annotations

from config.config import Config
from config.logging_config import configure_logging, get_logger
from core.overall_evaluator import OverallEvaluator
from core.recommendation_engine import RecommendationEngine
from evaluation.valuation.valuation_evaluator import ValuationEvaluator
from models.asset import Asset
from models.asset_profile import AssetProfile
from pipeline.evidence_builder import EvidenceBuilder


def main() -> None:
    """Run the demonstration."""
    configure_logging(Config.from_environment())
    logger = get_logger("core.demo")

    asset = Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )
    logger.info("stage 1 asset: %s (%s)", asset.ticker, asset.name)

    evidence = EvidenceBuilder().build(asset)
    logger.info("stage 2 evidence: %d item(s)", len(evidence.items))

    category_score = ValuationEvaluator().evaluate(evidence)
    logger.info(
        "stage 3 category score: %s = %s",
        category_score.category.value,
        category_score.score,
    )

    assessment = OverallEvaluator().evaluate((category_score,))
    logger.info(
        "stage 4 overall assessment: score=%s grade=%s",
        assessment.overall_score,
        assessment.grade,
    )

    recommendation = RecommendationEngine().recommend(assessment)
    logger.info(
        "stage 5 recommendation: %s (confidence=%s)",
        recommendation.decision_state.value,
        recommendation.confidence,
    )
    logger.info("thesis: %s", recommendation.investment_thesis)
    logger.info("evidence references: %s", list(recommendation.evidence_references))


if __name__ == "__main__":
    main()
