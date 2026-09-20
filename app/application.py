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
from analysis.brief import DailyBrief, build_daily_brief
from analysis.brief_report import render_daily_brief
from analysis.mobile_report import render_mobile_report
from analysis.report import generate_report
from app.morning_brief import BriefOutcome, MorningBrief
from app.rating_tracker import RatingTracker
from app.runtime_state import RuntimeState
from app.scheduler import IntervalSchedule, Scheduler
from communication.bark import BarkNotifier
from communication.change_detector import ChangeDetector, RecommendationFingerprint
from communication.pushplus import PushPlusNotifier
from communication.serverchan import ServerChanNotifier
from communication.wechat import WeChatNotifier
from communication.wecom_app import WeComAppNotifier
from config.config import Config
from config.logging_config import configure_logging, get_logger
from config.watchlist import load_watch_universe, universe_from_tickers
from data.catalyst_events import build_catalyst_event_provider
from data.market_data import build_market_data_provider
from models.asset import Asset
from models.watch_universe import WatchUniverse
from utils.constants import APP_NAME, APP_VERSION, CycleStatus, LoggerName
from utils.daily_moment import DailyMoment
from utils.exceptions import AISException
from utils.market_clock import MarketClock

# The hour the daily brief is owed at. It is stated in Beijing time because that is
# where the reader is, and it falls half an hour before the United States session
# opens, which is the point: the reader gets the freshest state before the market
# they are exposed to starts moving again.
MORNING_BRIEF_MOMENT = DailyMoment.beijing(hour=9, minute=0)


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
        self._universe, self._universe_loaded = _resolve_universe(self._config)
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
        self._scheduler = Scheduler()
        self._logger = get_logger(LoggerName.APPLICATION.value)

    def run(self) -> None:
        """Run the runtime until the process is interrupted.

        Two things are owed, and they are owed differently. The evaluation cycle
        runs on an interval for as long as the process lives; the morning brief runs
        once a day at an hour that comes from the clock. They are separate schedules
        because they answer different questions, and neither borrows the other's
        rules about when to speak.

        A keyboard interrupt stops the scheduler politely instead of tearing the
        process down.
        """
        configure_logging(self._config)
        self._logger.info("%s %s started", APP_NAME, APP_VERSION)
        self._logger.info(
            "watching %s from %s",
            ", ".join(self._universe.tickers),
            "the watchlist" if self._universe_loaded else "the configured tickers",
        )
        self._logger.info(
            "analysing on a %d minute interval",
            self._config.analysis_interval_minutes,
        )
        self._logger.info("morning brief at %s", MORNING_BRIEF_MOMENT.describe())
        try:
            self._scheduler.run(
                IntervalSchedule(
                    self._config.analysis_interval_minutes, self._run_cycle
                ),
                self._morning_brief(),
            )
        except KeyboardInterrupt:
            self._logger.info("shutdown requested")
        self._logger.info("%s stopped", APP_NAME)

    def _morning_brief(self) -> MorningBrief:
        """Return the daily brief, reading and writing what it has already done."""
        return MorningBrief(
            MORNING_BRIEF_MOMENT,
            RuntimeState(path=self._config.state_file),
            self._run_brief,
        )

    def _run_brief(self) -> BriefOutcome:
        """Produce and deliver one brief over the whole watch universe.

        No market clock and no change detector is consulted. The hour was chosen by
        a reader and falls outside the United States session by definition, and a
        brief that waits for a market to open never arrives at the hour it is owed
        at. Nothing is suppressed either: the brief is expected, and "nothing has
        changed" is what most days look like rather than a reason to say nothing.

        Every asset is analysed and **one** message is sent. Those are two different
        sets, and they are deliberately not the same size: AIS has to look at
        everything to know what matters, and a reader who receives seven messages
        has received a feed rather than a brief. What each asset's run produced is
        still written to the log in full, so nothing is dropped by being left out of
        the message.

        Each asset is analysed as it is now, and the brief is built from those
        results at the moment it is sent, so there is no earlier result delivered
        late.

        **Delivery is reported rather than inferred from the status.** A run can fail
        for two reasons that look alike from the outside and are not alike at all: an
        asset that could not be analysed, and a message that reached nobody. Only the
        second leaves the day owed, and telling them apart is why the outcome carries
        both.

        Returns:
            What the brief did, and whether it reached anybody.
        """
        moment = datetime.now(MORNING_BRIEF_MOMENT.timezone)
        results: list[AnalysisResult] = []
        without_data: list[str] = []
        for asset in self._universe.assets:
            result = self._analyse(asset)
            if result is None:
                without_data.append(asset.ticker)
                continue
            results.append(result)
            # The brief has just told the reader about this asset, so the next cycle
            # must not announce the same conclusion again as though it were news.
            self._change_detector.observe(
                RecommendationFingerprint.of(result.recommendation, asset.ticker)
            )

        if not results:
            self._logger.error(
                "no asset could be analysed, so no brief was produced or sent"
            )
            return BriefOutcome(status=CycleStatus.EVALUATION_FAILED, delivered=False)

        brief = build_daily_brief(
            results,
            moment=moment,
            universe=self._universe,
            without_data=without_data,
        )
        message = render_daily_brief(brief)
        self._logger.info("brief: %s", _describe_brief(brief))
        for line in message.splitlines():
            self._logger.info("%s", line)

        delivered = True
        try:
            self._deliver(_brief_title(brief), message)
        except (
            Exception
        ) as error:  # noqa: BLE001 - the brief must not crash the runtime
            delivered = False
            self._logger.error("the brief was not delivered: %s", error)

        status = (
            CycleStatus.NOTIFICATION_SENT
            if delivered and not without_data
            else CycleStatus.EVALUATION_FAILED
        )
        return BriefOutcome(status=status, delivered=delivered)

    def _run_cycle(self) -> CycleStatus:
        """Run one evaluation cycle over every watched asset.

        Each asset is evaluated and decided on its own, and reports its own
        outcome. The status returned is the one outcome of the cycle as a whole.

        Returns:
            The single status describing what this cycle did.
        """
        status = self._market_clock.status(datetime.now(UTC))
        if not status.is_open:
            self._logger.info("Skipped evaluation: %s", status.reason)
            return CycleStatus.MARKET_CLOSED

        outcomes = [self._run_asset(asset) for asset in self._universe.assets]
        summary = _summarise(outcomes)
        self._logger.info("cycle outcome: %s", _describe_outcomes(outcomes))
        return summary

    def _run_asset(self, asset: Asset) -> CycleStatus:
        """Evaluate one asset and, when its conclusion moved, notify.

        The cycle reports change: it exists to tell a reader that something about an
        asset is not what it was, so an asset whose recommendation stands says
        nothing. The brief is the other shape and does not come through here.

        Args:
            asset: Asset to evaluate, carrying the identity the watch universe gave
                it.

        Returns:
            The outcome of this asset within the cycle.
        """
        ticker = asset.ticker
        result = self._analyse(asset)
        if result is None:
            return CycleStatus.EVALUATION_FAILED

        fingerprint = RecommendationFingerprint.of(result.recommendation, ticker)
        changed = self._change_detector.observe(fingerprint)
        if not changed:
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

    def _analyse(self, asset: Asset) -> AnalysisResult | None:
        """Run one asset through the analysis flow and write its report to the log.

        The expanded report is rendered for every asset that is analysed, whether or
        not anything about it reaches a reader. That is what makes dropping a line
        from a phone safe: the fact moves here rather than disappearing, and a
        question about what AIS knew at nine o'clock can still be answered.

        Args:
            asset: Asset to analyse.

        Returns:
            The analysis result, or None when the run failed. A failure is logged
            and reported; it is not raised, because one asset must not stop the rest.
        """
        try:
            result = self._analyzer.analyze_result(asset)
        except Exception as error:  # noqa: BLE001 - one asset must not stop the rest
            self._logger.exception("Evaluation failed for %s: %s", asset.ticker, error)
            return None

        for line in generate_report(result).splitlines():
            self._logger.info("%s", line)
        return result

    def _notify(self, result: AnalysisResult) -> None:
        """Send the report for one asset through every configured channel."""
        self._deliver(
            f"AIS Recommendation {result.asset.ticker}",
            render_mobile_report(result, generated_at=datetime.now()),
        )

    def _deliver(self, title: str, message: str) -> None:
        """Send one rendered message through every configured channel.

        The text is rendered before it arrives here, and a channel transports it: a
        channel is a transport, not a report format. Channels are additive, so
        configuring another channel never replaces an existing one. A failing
        channel is logged and does not stop the others; the send only fails when
        every configured channel failed.
        """
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
                "no notification channel is configured, so nothing was sent"
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


def _brief_title(brief: DailyBrief) -> str:
    """Return the title the brief is delivered under.

    Channels differ in what they do with a title — one shows it above the message,
    another ignores it — so it names the report and the day and carries nothing the
    message does not already state.
    """
    return f"AIS 晨报 {brief.day.isoformat()}"


def _describe_brief(brief: DailyBrief) -> str:
    """Return one line saying what the brief covered and what it showed."""
    return (
        f"{len(brief.entries)} of {len(brief.analysed)} assets written out, "
        f"{len(brief.external_events)} shared events, "
        f"{len(brief.without_data)} without data"
    )


def _resolve_universe(config: Config) -> tuple[WatchUniverse, bool]:
    """Return the universe to run with, and whether a watchlist supplied it.

    A watchlist wins when it can be used. When it is absent, empty or unusable the
    configured tickers are used instead, as a universe whose only set is the core
    watchlist — which is what a watchlist listing the same symbols would produce.
    The fallback is not a degraded mode: it is the same universe, with nothing
    known about the assets beyond their symbols.

    Args:
        config: Configuration naming both the watchlist and the fallback tickers.

    Returns:
        The universe, and whether it came from the watchlist.
    """
    from_watchlist = load_watch_universe(config.watchlist_file)
    if from_watchlist is not None:
        return from_watchlist, True
    return universe_from_tickers(config.tickers), False


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
