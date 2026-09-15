"""Runnable demonstration of the WeChat notification.

Run with: ``python -m communication.demo``.

Sends one already rendered report through the WeChat webhook. The point is to
verify the transport, so the report is produced by the same renderer the
application uses and the notifier only carries it: a notifier never builds
report content.
"""

from __future__ import annotations

from datetime import datetime

from analysis.analysis_result import AnalysisResult
from analysis.mobile_report import render_mobile_report
from communication.wechat import WeChatNotifier
from config.config import Config
from config.logging_config import configure_logging, get_logger
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_DEMO_SYMBOL = "DEMO"


def _demo_result() -> AnalysisResult:
    """Return a minimal analysis result, standing in for a real run."""
    score = CategoryScore(
        category=Category.VALUATION,
        score=42.0,
        confidence=0.5,
        summary="Demo category summary.",
        evidence_references=("demo.evidence",),
    )
    return AnalysisResult(
        asset=Asset(
            ticker=_DEMO_SYMBOL,
            name=_DEMO_SYMBOL,
            exchange="UNKNOWN",
            currency="USD",
            profile=AssetProfile.UNKNOWN,
        ),
        assessment=OverallAssessment(
            overall_score=42.0,
            confidence=0.5,
            grade="DEMO",
            category_scores=(score,),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=0.42,
            investment_thesis="Dummy thesis used to verify the WeChat notification.",
            evidence_references=("demo.evidence",),
        ),
    )


def main() -> None:
    """Render one demo report and send it through WeChat."""
    config = Config.from_environment()
    configure_logging(config)
    logger = get_logger("communication.demo")

    message = render_mobile_report(_demo_result(), generated_at=datetime.now())

    logger.info("report to send:")
    for line in message.splitlines():
        logger.info("%s", line)

    WeChatNotifier(config.wechat_webhook_url).send(message)


if __name__ == "__main__":
    main()
