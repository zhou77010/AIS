"""AIS Application.

Main application lifecycle: configuration, logging, scheduling, analysis and
notification.

The application owns the runtime only. It decides which cycle runs when, and
what each cycle reports; it holds no business logic. Every cycle ends with
exactly one :class:`CycleStatus`, so a cycle can never finish without saying
what it did.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime

from analysis.analysis_result import AnalysisResult
from analysis.analyzer import AssetAnalyzer
from analysis.mobile_report import render_mobile_report
from analysis.report import generate_report
from app.rating_tracker import RatingTracker
from app.scheduler import Scheduler
from communication.bark import BarkNotifier
from communication.change_detector import ChangeDetector, RecommendationFingerprint
from communication.pushplus import PushPlusNotifier
from communication.serverchan import ServerChanNotifier
from communication.wechat import WeChatNotifier
from communication.wecom_app import WeComAppNotifier
from config.config import Config
from config.logging_config import configure_logging, get_logger
from data.catalyst_events import build_catalyst_event_provider
from data.market_data import build_market_data_provider
from models.asset import Asset
from models.asset_profile import AssetProfile
from utils.constants import APP_NAME, APP_VERSION, CycleStatus, LoggerName
from utils.exceptions import AISException
from utils.market_clock import MarketClock


class Application:
    """AIS application."""

    def __init__(
        self,
        config: Config | None = None,
        market_clock: MarketClock | None = None,
        analyzer: AssetAnalyzer | None = None,
    ) -> None:
        """Wire the runtime together.

        Args:
            config: Configuration to run with. Defaults to the environment.
            market_clock: Clock deciding when the market is open. Defaults to
                the United States market clock.
            analyzer: Analysis flow to run. Defaults to the live flow, which
                retrieves market data over the network.
        """
        self._config = config if config is not None else Config.from_environment()
        self._market_clock = market_clock if market_clock is not None else MarketClock()
        self._analyzer = (
            analyzer
            if analyzer is not None
            else AssetAnalyzer(
                build_market_data_provider(),
                RatingTracker(),
                build_catalyst_event_provider(),
            )
        )
        self._change_detector = ChangeDetector()
        self._scheduler = Scheduler(self._config.analysis_interval_minutes)
        self._logger = get_logger(LoggerName.APPLICATION.value)

    def run(self) -> None:
        """Run evaluation cycles until the process is interrupted.

        The first cycle runs immediately; the rest follow on the configured
        interval. A keyboard interrupt stops the scheduler politely instead of
        tearing the process down.
        """
        configure_logging(self._config)
        self._logger.info("%s %s started", APP_NAME, APP_VERSION)
        self._logger.info(
            "analysing %s on a %d minute interval",
            ", ".join(self._config.tickers),
            self._config.analysis_interval_minutes,
        )
        try:
            self._scheduler.run(self._run_cycle)
        except KeyboardInterrupt:
            self._logger.info("shutdown requested")
        self._logger.info("%s stopped", APP_NAME)

    def _run_cycle(self) -> CycleStatus:
        """Run one evaluation cycle over every configured asset.

        Each asset is evaluated and decided on its own, and reports its own
        outcome. The status returned is the one outcome of the cycle as a whole.

        Returns:
            The single status describing what this cycle did.
        """
        status = self._market_clock.status(datetime.now(UTC))
        if not status.is_open:
            self._logger.info("Skipped evaluation: %s", status.reason)
            return CycleStatus.MARKET_CLOSED

        outcomes = [self._run_asset(ticker) for ticker in self._config.tickers]
        summary = _summarise(outcomes)
        self._logger.info("cycle outcome: %s", _describe_outcomes(outcomes))
        return summary

    def _run_asset(self, ticker: str) -> CycleStatus:
        """Evaluate one asset and notify when its recommendation changed.

        Args:
            ticker: Symbol to evaluate.

        Returns:
            The outcome of this asset within the cycle.
        """
        asset = self._asset(ticker)
        try:
            result = self._analyzer.analyze_result(asset)
        except Exception as error:  # noqa: BLE001 - one asset must not stop the rest
            self._logger.exception("Evaluation failed for %s: %s", ticker, error)
            return CycleStatus.EVALUATION_FAILED

        for line in generate_report(result).splitlines():
            self._logger.info("%s", line)

        fingerprint = RecommendationFingerprint.of(result.recommendation, ticker)
        if not self._change_detector.observe(fingerprint):
            self._logger.info(
                "Skipped notification for %s: recommendation unchanged (%s)",
                ticker,
                fingerprint.describe(),
            )
            return CycleStatus.RECOMMENDATION_UNCHANGED

        try:
            self._notify(result)
        except Exception as error:  # noqa: BLE001 - one asset must not stop the rest
            self._logger.error("Notification failed for %s: %s", ticker, error)
            return CycleStatus.EVALUATION_FAILED

        self._logger.info("Notification sent (%s)", fingerprint.describe())
        return CycleStatus.NOTIFICATION_SENT

    def _asset(self, ticker: str) -> Asset:
        """Return the asset for one configured symbol."""
        return Asset(
            ticker=ticker,
            name=ticker,
            exchange="UNKNOWN",
            currency="USD",
            profile=AssetProfile.UNKNOWN,
        )

    def _notify(self, result: AnalysisResult) -> None:
        """Send the report through every configured channel.

        The report is rendered once, here, and every channel transports that
        same text: a channel is a transport, not a report format. Channels are
        additive, so configuring another channel never replaces an existing one.
        A failing channel is logged and does not stop the others; the cycle only
        fails when every configured channel failed.
        """
        symbol = result.asset.ticker
        generated_at = datetime.now()

        title = f"AIS Recommendation {symbol}"
        message = render_mobile_report(result, generated_at=generated_at)
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
                    lambda: WeChatNotifier(config.wechat_webhook_url).send(message),
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
            raise AISException(
                "no notification channel is configured, so the recommendation "
                "was not sent"
            )

        failures: list[str] = []
        for name, send in channels:
            try:
                send()
            except (
                Exception
            ) as error:  # noqa: BLE001 - one channel must not stop the rest
                failures.append(f"{name}: {error}")

        for failure in failures:
            self._logger.warning("notification channel failed: %s", failure)
        if len(failures) == len(channels):
            raise AISException(
                "every notification channel failed: " + "; ".join(failures)
            )


def _summarise(outcomes: list[CycleStatus]) -> CycleStatus:
    """Reduce the outcomes of every asset to the outcome of the cycle.

    A failure anywhere is reported as a failure, because a cycle that could not
    finish its work must not look like one that did. Otherwise a notification
    makes the cycle a notifying one, and a cycle where nothing changed is
    reported as unchanged.

    Args:
        outcomes: Outcome of each asset evaluated in the cycle.

    Returns:
        The single status describing the cycle.
    """
    if CycleStatus.EVALUATION_FAILED in outcomes:
        return CycleStatus.EVALUATION_FAILED
    if CycleStatus.NOTIFICATION_SENT in outcomes:
        return CycleStatus.NOTIFICATION_SENT
    return CycleStatus.RECOMMENDATION_UNCHANGED


def _describe_outcomes(outcomes: list[CycleStatus]) -> str:
    """Return the counts of one cycle's outcomes, for the log line."""
    counts = Counter(outcomes)
    return ", ".join(
        f"{count} {status.value}" for status, count in sorted(counts.items())
    )
