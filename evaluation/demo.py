"""Runnable demonstration of the evaluation framework.

Run with: ``python -m evaluation.demo``.

Shows how the framework components compose: the rule engine executes the
enabled rules, skips a disabled one, records a failing one, and reports the
statistics of the run.
"""

from __future__ import annotations

import inspect

from config.config import Config
from config.logging_config import configure_logging, get_logger
from evaluation.base_evaluator import BaseEvaluator
from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_engine import RuleEngine
from evaluation.rule_result import RuleResult
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile


def _run_ok(evidence: EvidenceCollection) -> RuleResult:
    """Return a successful demonstration result."""
    return RuleResult(
        rule_id="demo.ok",
        score=1.0,
        reason=f"measured {evidence.asset.ticker}",
        evidence_references=("demo.ok",),
    )


def _run_failure(evidence: EvidenceCollection) -> RuleResult:
    """Raise, to demonstrate that a failure does not stop the engine."""
    raise RuntimeError("demonstration failure")


def main() -> None:
    """Run the demonstration."""
    configure_logging(Config.from_environment())
    logger = get_logger("evaluation.demo")

    asset = Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )
    rules = (
        EvaluationRule(
            id="demo.ok",
            name="Passing rule",
            description="Runs successfully.",
            enabled=True,
            execute=_run_ok,
        ),
        EvaluationRule(
            id="demo.disabled",
            name="Disabled rule",
            description="Is skipped.",
            enabled=False,
            execute=_run_ok,
        ),
        EvaluationRule(
            id="demo.failure",
            name="Failing rule",
            description="Raises an error.",
            enabled=True,
            execute=_run_failure,
        ),
    )

    evaluation = RuleEngine().run(rules, EvidenceCollection(asset=asset, items=()))
    statistics = evaluation.statistics

    logger.info("results: %s", [result.rule_id for result in evaluation.results])
    logger.info("skipped: %s", list(evaluation.skipped_rule_ids))
    for failure in evaluation.failures:
        logger.info(
            "failure: %s (%s: %s)",
            failure.rule_id,
            failure.error_type,
            failure.message,
        )
    logger.info(
        "statistics: total=%d succeeded=%d skipped=%d failed=%d",
        statistics.total,
        statistics.succeeded,
        statistics.skipped,
        statistics.failed,
    )
    logger.info("normalized sample: %s", ScoreNormalizer().normalize(3.0))
    logger.info("BaseEvaluator is abstract: %s", inspect.isabstract(BaseEvaluator))


if __name__ == "__main__":
    main()
