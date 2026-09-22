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
from analysis.premarket_report import render_premarket_brief
from analysis.report import generate_report
from app.decision_ledger import FILE_NAME as LEDGER_FILE_NAME
from app.decision_ledger import DecisionLedger
from app.morning_brief import MorningBrief
from app.premarket_brief import PreMarketBrief
from app.rating_tracker import RatingTracker
from app.runtime_state import BaselineName, RuntimeState
from app.scheduled_report import ReportOutcome
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
from contracts.market_environment import EnvironmentProvider, EnvironmentSnapshot
from data.catalyst_events import build_catalyst_event_provider
from data.market_data import build_market_data_provider
from data.market_environment import build_environment_provider
from models.asset import Asset
from models.watch_universe import WatchUniverse
from utils.constants import APP_NAME, APP_VERSION, CycleStatus, LoggerName
from utils.daily_moment import DailyMoment
from utils.exceptions import AISException
from utils.market_clock import MarketClock

# The hours AIS speaks at, stated in Beijing time because that is where the reader is.
# They sit at the two ends of the United States day and they answer different questions,
# which is the whole reason there are two of them rather than one sent twice.
#
# 09:00 Beijing is five hours after the previous session closed, with the extended
# session
# over: the completed state of a day that has ended, which is what the morning brief is
# for.
MORNING_BRIEF_MOMENT = DailyMoment.beijing(hour=9, minute=0)

# 21:00 Beijing is thirty minutes before the next session opens, with the pre-market
# already traded: what price is doing before the open, which is a fact that does not
# exist
# at the other hour and is stale by the time the next report is written.
PREMARKET_BRIEF_MOMENT = DailyMoment.beijing(hour=21, minute=0)


class Application:
    """AIS application."""

    def __init__(
        self,
        config: Config | None = None,
        market_clock: MarketClock | None = None,
        analyzer: AssetAnalyzer | None = None,
        environment_provider: EnvironmentProvider | None = None,
    ) -> None:
        """Wire the runtime together.

        Args:
            config: Configuration to run with. Defaults to the environment.
            market_clock: Clock deciding when the market is open. Defaults to
                the United States market clock.
            analyzer: Analysis flow to run. Defaults to the live flow, which
                retrieves market data over the network.
            environment_provider: Source of the environment every asset in a pass is
                judged in. Defaults to the live source. It is held here rather than by
                the analyzer because the runtime is what knows where a pass begins and
                ends, and the environment is retrieved once for a pass.
        """
        self._config = config if config is not None else Config.from_environment()
        self._universe, self._universe_loaded = _resolve_universe(self._config)
        self._market_clock = market_clock if market_clock is not None else MarketClock()
        self._state = RuntimeState(path=self._config.state_file)
        # What each pass concluded, kept beside the state so that a conclusion can be
        # replayed later without being read back out of a message.
        self._ledger = DecisionLedger(
            path=self._config.state_file.parent / LEDGER_FILE_NAME
        )
        # Held here rather than created inside the analyzer because the runtime is what
        # writes it down: the tracker remembers where each category stood, and a restart
        # that silently forgot it would turn every comparison into a first reading.
        self._ratings = RatingTracker()
        self._environment_provider = (
            environment_provider
            if environment_provider is not None
            else build_environment_provider(self._universe.sectors)
        )
        self._analyzer = (
            analyzer
            if analyzer is not None
            else AssetAnalyzer(
                build_market_data_provider(),
                self._ratings,
                build_catalyst_event_provider(),
            )
        )
        self._change_detector = ChangeDetector()
        self._scheduler = Scheduler()
        self._logger = get_logger(LoggerName.APPLICATION.value)

    def run(self) -> None:
        """Run the runtime until the process is interrupted.

        Three things are owed, and they are owed differently. The evaluation cycle runs
        on
        an interval for as long as the process lives, and the two reports run once a day
        each at an hour that comes from the clock. They are separate schedules because
        they answer different questions, and neither borrows the other's rules about
        when
        to speak.

        The baselines are restored before anything runs, because the first thing a
        restored process would otherwise do is compare the world with nothing.

        A keyboard interrupt stops the scheduler politely instead of tearing the process
        down.
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
        self._logger.info("pre-market brief at %s", PREMARKET_BRIEF_MOMENT.describe())
        self._restore_baselines()
        try:
            self._scheduler.run(
                IntervalSchedule(
                    self._config.analysis_interval_minutes, self._run_cycle
                ),
                self._morning_brief(),
                self._premarket_brief(),
            )
        except KeyboardInterrupt:
            self._logger.info("shutdown requested")
        self._logger.info("%s stopped", APP_NAME)

    def _environment(self) -> EnvironmentSnapshot | None:
        """Return the environment this pass is judged in.

        Retrieved once per pass and shared by every asset in it. The market is the
        same market for all of them: fetching it per asset would fetch one fact once
        per asset, and the copies could disagree with each other about the same
        morning.

        Returns:
            The environment as the source reports it. A source that could not be
            reached answers with a snapshot whose points have no values, which
            degrades the Market judgement rather than stopping the run.
        """
        if self._environment_provider is None:
            return None
        return self._environment_provider.fetch()

    def _morning_brief(self) -> MorningBrief:
        """Return the morning brief, reading and writing what it has already done."""
        return MorningBrief(MORNING_BRIEF_MOMENT, self._state, self._run_brief)

    def _premarket_brief(self) -> PreMarketBrief:
        """Return the pre-market brief, with its own day and its own delivery.

        It shares the state file with the morning brief and nothing else: its own key,
        its own attempts and its own delivery state, so that one report failing or being
        abandoned says nothing about the other.
        """
        return PreMarketBrief(
            PREMARKET_BRIEF_MOMENT, self._state, self._run_premarket_brief
        )

    def _restore_baselines(self) -> None:
        """Read back what the last process held, so a restart keeps a comparison.

        Both baselines are written down for the same reason: the first reading after a
        restart would otherwise look like a first reading ever, which turns a comparison
        into a false statement — an unchanged conclusion announced as news, and a
        measurement reported as never having moved.
        """
        ratings = self._ratings.restore(self._state.baseline(BaselineName.RATINGS))
        recommendations = self._change_detector.restore(
            self._state.baseline(BaselineName.RECOMMENDATIONS)
        )
        self._logger.info(
            "restored %d rating baseline(s) and %d recommendation baseline(s) from %s",
            ratings,
            recommendations,
            self._state.path,
        )

    def _commit_baselines(self) -> None:
        """Write down what the process holds, so the next one starts where this is."""
        ratings = self._ratings.snapshot()
        recommendations = self._change_detector.snapshot()
        # Instrumentation, and only instrumentation. A write that would leave the file
        # holding less than it held is the shape of the fault this is here to find, so
        # it is reported before it happens rather than discovered afterwards.
        for name, snapshot in (
            (BaselineName.RATINGS, ratings),
            (BaselineName.RECOMMENDATIONS, recommendations),
        ):
            held = len(self._state.baseline(name))
            if held and len(snapshot) < held:
                self._logger.warning(
                    "baseline shrink in %s: %s holds %d entries and this pass would "
                    "write %d",
                    name.value,
                    self._state.path,
                    held,
                    len(snapshot),
                )
        self._logger.info(
            "writing baselines to %s: %d rating(s), %d recommendation(s)",
            self._state.path,
            len(ratings),
            len(recommendations),
        )
        self._state.record_baseline(BaselineName.RATINGS, ratings)
        self._state.record_baseline(BaselineName.RECOMMENDATIONS, recommendations)

    def _run_brief(self) -> ReportOutcome:
        """Produce and deliver the morning brief over the whole watch universe."""
        return self._run_report(
            render=render_daily_brief, title=_brief_title, name="brief"
        )

    def _run_premarket_brief(self) -> ReportOutcome:
        """Produce and deliver the pre-market brief over the whole watch universe."""
        return self._run_report(
            render=render_premarket_brief,
            title=_premarket_title,
            name="pre-market brief",
        )

    def _run_report(
        self,
        *,
        render: Callable[[DailyBrief], str],
        title: Callable[[DailyBrief], str],
        name: str,
    ) -> ReportOutcome:
        """Produce and deliver one report over the whole watch universe.

        Both reports come through here, and they differ only in what they render and
        what
        they are called. They share this path deliberately: the analysis, the selection,
        the delivery and the outcome are the same question, and a second copy of them
        would be a second place for the two to disagree.

        No market clock and no change detector is consulted. The hour was chosen by a
        reader and falls outside the United States session by definition, and a report
        that waits for a market to open never arrives at the hour it is owed at. Nothing
        is suppressed either: a scheduled report is expected, and "nothing has changed"
        is
        what most days look like rather than a reason to say nothing.

        Every asset is analysed and **one** message is sent. Those are two different
        sets,
        and they are deliberately not the same size: AIS has to look at everything to
        know
        what matters, and a reader who receives seven messages has received a feed
        rather
        than a report. What each asset's run produced is still written to the log in
        full,
        so nothing is dropped by being left out of the message.

        Each asset is analysed as it is now, and the report is built from those results
        at
        the moment it is sent, so there is no earlier result delivered late.

        **Delivery is reported rather than inferred from the status.** A run can fail
        for
        two reasons that look alike from the outside and are not alike at all: an asset
        that could not be analysed, and a message that reached nobody. Only the second
        leaves the day owed, and telling them apart is why the outcome carries both.

        Args:
            render: Projection that turns the brief model into the text this report is.
            title: What the report is delivered under, for the channels that show one.
            name: How the report is named in the log.

        Returns:
            What the report did, and whether it reached anybody.
        """
        moment = datetime.now(MORNING_BRIEF_MOMENT.timezone)
        environment = self._environment()
        results: list[AnalysisResult] = []
        without_data: list[str] = []
        for asset in self._universe.assets:
            result = self._analyse(asset, environment)
            if result is None:
                without_data.append(asset.ticker)
                continue
            results.append(result)
            # The report has just told the reader about this asset, so the next cycle
            # must not announce the same conclusion again as though it were news.
            self._change_detector.observe(
                RecommendationFingerprint.of(result.recommendation, asset.ticker)
            )
        # The baselines are written after a report as well as after a cycle: a report is
        # what the reader was told, and what the next process must not tell them again.
        self._commit_baselines()

        if not results:
            self._logger.error(
                "no asset could be analysed, so no %s was produced or sent", name
            )
            return ReportOutcome(status=CycleStatus.EVALUATION_FAILED, delivered=False)

        brief = build_daily_brief(
            results,
            moment=moment,
            universe=self._universe,
            without_data=without_data,
        )
        message = render(brief)
        self._logger.info("%s: %s", name, _describe_brief(brief))
        for line in message.splitlines():
            self._logger.info("%s", line)

        delivered = True
        try:
            self._deliver(title(brief), message)
        except Exception as error:  # noqa: BLE001 - a report must not crash the runtime
            delivered = False
            self._logger.error("the %s was not delivered: %s", name, error)

        status = (
            CycleStatus.NOTIFICATION_SENT
            if delivered and not without_data
            else CycleStatus.EVALUATION_FAILED
        )
        return ReportOutcome(status=status, delivered=delivered)

    def _run_cycle(self) -> CycleStatus:
        """Run one evaluation cycle over every watched asset.

        Each asset is evaluated and decided on its own, and reports its own
        outcome. The status returned is the one outcome of the cycle as a whole.

        The environment is retrieved once for the whole cycle, because every asset in
        it is judged in the same market.

        Returns:
            The single status describing what this cycle did.
        """
        status = self._market_clock.status(datetime.now(UTC))
        if not status.is_open:
            self._logger.info("Skipped evaluation: %s", status.reason)
            return CycleStatus.MARKET_CLOSED

        environment = self._environment()
        outcomes = [
            self._run_asset(asset, environment) for asset in self._universe.assets
        ]
        # What the cycle concluded is written down here rather than only held in memory:
        # a restart that forgot it would report movement that did not happen and repeat
        # conclusions the reader has already been sent.
        self._commit_baselines()
        summary = _summarise(outcomes)
        self._logger.info("cycle outcome: %s", _describe_outcomes(outcomes))
        return summary

    def _run_asset(
        self, asset: Asset, environment: EnvironmentSnapshot | None
    ) -> CycleStatus:
        """Evaluate one asset and, when its conclusion moved, notify.

        The cycle reports change: it exists to tell a reader that something about an
        asset is not what it was, so an asset whose recommendation stands says
        nothing. The brief is the other shape and does not come through here.

        Args:
            asset: Asset to evaluate, carrying the identity the watch universe gave
                it.
            environment: The environment this pass is judged in.

        Returns:
            The outcome of this asset within the cycle.
        """
        ticker = asset.ticker
        result = self._analyse(asset, environment)
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

    def _analyse(
        self, asset: Asset, environment: EnvironmentSnapshot | None
    ) -> AnalysisResult | None:
        """Run one asset through the analysis flow and write its report to the log.

        The expanded report is rendered for every asset that is analysed, whether or
        not anything about it reaches a reader. That is what makes dropping a line
        from a phone safe: the fact moves here rather than disappearing, and a
        question about what AIS knew at nine o'clock can still be answered.

        Args:
            asset: Asset to analyse.
            environment: The environment this pass is judged in, or None when no
                environment source was consulted.

        Returns:
            The analysis result, or None when the run failed. A failure is logged
            and reported; it is not raised, because one asset must not stop the rest.
        """
        try:
            result = self._analyzer.analyze_result(asset, environment=environment)
        except Exception as error:  # noqa: BLE001 - one asset must not stop the rest
            self._logger.exception("Evaluation failed for %s: %s", asset.ticker, error)
            return None

        for line in generate_report(result).splitlines():
            self._logger.info("%s", line)
        self._ledger.record(result, moment=datetime.now(UTC))
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


def _premarket_title(brief: DailyBrief) -> str:
    """Return the title the pre-market brief is delivered under."""
    return f"AIS 盘前简报 {brief.day.isoformat()}"


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
