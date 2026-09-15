"""Runnable demonstration of the complete asset analysis.

Run with: ``python -m analysis.demo``.

Creates one asset, analyses it end to end, and logs the generated report.
"""

from __future__ import annotations

from analysis.analyzer import AssetAnalyzer
from analysis.report import generate_report
from config.config import Config
from config.logging_config import configure_logging, get_logger
from models.asset import Asset
from models.asset_profile import AssetProfile


def main() -> None:
    """Run the demonstration."""
    configure_logging(Config.from_environment())
    logger = get_logger("analysis.demo")

    asset = Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )
    result = AssetAnalyzer().analyze_result(asset)

    for line in generate_report(result).splitlines():
        logger.info("%s", line)


if __name__ == "__main__":
    main()
