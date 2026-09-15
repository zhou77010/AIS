"""Runnable demonstration of the valuation evaluator.

Run with: ``python -m evaluation.valuation.demo``.
"""

from __future__ import annotations

from config.config import Config
from config.logging_config import configure_logging, get_logger
from evaluation.valuation.valuation_evaluator import ValuationEvaluator
from models.asset import Asset
from models.asset_profile import AssetProfile
from pipeline.evidence_builder import EvidenceBuilder


def main() -> None:
    """Run the demonstration."""
    configure_logging(Config.from_environment())
    logger = get_logger("valuation.demo")

    asset = Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )
    evidence = EvidenceBuilder().build(asset)
    evaluator = ValuationEvaluator()

    results = evaluator.collect_results(evidence)
    score = evaluator.evaluate(evidence)

    logger.info("collected %d rule results", len(results.results))
    for result in results.results:
        logger.info(
            "%s: score=%s reason=%s", result.rule_id, result.score, result.reason
        )
    logger.info(
        "category=%s score=%s confidence=%s",
        score.category.value,
        score.score,
        score.confidence,
    )
    logger.info("references=%s", score.evidence_references)


if __name__ == "__main__":
    main()
