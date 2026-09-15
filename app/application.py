"""AIS Application.

Main application lifecycle: configuration, logging, analysis and notification.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime

from analysis.analysis_result import AnalysisResult
from analysis.analyzer import AssetAnalyzer
from analysis.report import describe_data_source, generate_report
from communication.bark import BarkNotifier
from communication.pushplus import PushPlusNotifier
from communication.serverchan import ServerChanNotifier
from communication.wechat import WeChatNotifier, build_message
from communication.wecom_app import WeComAppNotifier
from config.config import Config
from config.logging_config import configure_logging, get_logger
from data.yahoo_market_data_provider import YahooMarketDataProvider
from models.asset import Asset
from models.asset_profile import AssetProfile
from utils.constants import APP_NAME, APP_VERSION, LoggerName
from utils.exceptions import AISException


class Application:
    """AIS application."""

    def __init__(self) -> None:
        """Load the runtime configuration from the environment."""
        self._config = Config.from_environment()

    def run(self) -> None:
        """Analyse the configured asset and notify, once or on a schedule."""
        configure_logging(self._config)
        logger = get_logger(LoggerName.APPLICATION.value)
        logger.info("%s %s started", APP_NAME, APP_VERSION)

        while True:
            self._analyse_and_notify(logger)
            interval_minutes = self._config.analysis_interval_minutes
            if interval_minutes <= 0:
                break
            logger.info("next analysis in %d minute(s)", interval_minutes)
            time.sleep(interval_minutes * 60)

    def _analyse_and_notify(self, logger: logging.Logger) -> None:
        """Run one analysis and send its recommendation to the phone."""
        ticker = self._config.ticker
        asset = Asset(
            ticker=ticker,
            name=ticker,
            exchange="UNKNOWN",
            currency="USD",
            profile=AssetProfile.UNKNOWN,
        )

        result = AssetAnalyzer(YahooMarketDataProvider()).analyze_result(asset)
        for line in generate_report(result).splitlines():
            logger.info("%s", line)

        self._notify(logger, result)

    def _notify(self, logger: logging.Logger, result: AnalysisResult) -> None:
        """Send the recommendation through every configured channel.

        Channels are additive: configuring another channel never replaces an
        existing one. A failing channel is logged and does not stop the others;
        the run only fails when every configured channel failed.
        """
        recommendation = result.recommendation
        symbol = result.asset.ticker
        generated_at = datetime.now()
        data_source = describe_data_source(result)

        title = f"AIS Recommendation {symbol}"
        message = build_message(
            recommendation,
            symbol,
            generated_at=generated_at,
            data_source=data_source,
        )
        config = self._config

        channels: list[tuple[str, Callable[[], None]]] = []
        if config.bark_url is not None:
            channels.append(
                ("bark", lambda: BarkNotifier(config.bark_url).send(title, message))
            )
        if config.pushplus_token is not None:
            channels.append(
                (
                    "pushplus",
                    lambda: PushPlusNotifier(config.pushplus_token).send(
                        title, message
                    ),
                )
            )
        if config.serverchan_url is not None:
            channels.append(
                (
                    "serverchan",
                    lambda: ServerChanNotifier(config.serverchan_url).send(
                        title, message
                    ),
                )
            )
        if config.wechat_webhook_url is not None:
            channels.append(
                (
                    "wechat",
                    lambda: WeChatNotifier(config.wechat_webhook_url).send(
                        recommendation,
                        symbol,
                        generated_at=generated_at,
                        data_source=data_source,
                    ),
                )
            )
        if (
            config.wecom_corp_id is not None
            and config.wecom_app_secret is not None
            and config.wecom_agent_id is not None
        ):
            channels.append(
                (
                    "wecom",
                    lambda: WeComAppNotifier(
                        config.wecom_corp_id,
                        config.wecom_app_secret,
                        config.wecom_agent_id,
                    ).send(message),
                )
            )

        if not channels:
            logger.warning("no notification channel configured; message not sent")
            return

        failures: list[str] = []
        for name, send in channels:
            try:
                send()
            except Exception as error:
                failures.append(f"{name}: {error}")

        for failure in failures:
            logger.warning("notification channel failed: %s", failure)
        if len(failures) == len(channels):
            raise AISException(
                "every notification channel failed: " + "; ".join(failures)
            )
