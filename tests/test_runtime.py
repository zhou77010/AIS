"""Tests for continuous runtime behaviour (Runtime Sprint 13)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from analysis.analysis_result import AnalysisResult
from app.application import Application
from app.scheduler import IntervalSchedule, Scheduler
from communication.change_detector import ChangeDetector, RecommendationFingerprint
from config.config import Config
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation
from utils.constants import CycleStatus, Environment, LogLevel
from utils.market_clock import MarketClock, MarketStatus

# 2026-09-16 is a Wednesday, 2026-09-19 a Saturday, 2026-01-15 and 2026-07-15
# are Thursdays and Wednesdays respectively. The dates are fixed so the tests
# describe the market calendar rather than the day they happen to run on.


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    """Return a UTC moment, so the tests never depend on the local zone."""
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


# --------------------------------------------------------------------------
# T2 - market hours
# --------------------------------------------------------------------------


def test_market_is_open_during_the_regular_session() -> None:
    status = MarketClock().status(_utc(2026, 9, 16, 14, 0))

    assert status.is_open is True
    assert "open" in status.reason


def test_market_is_closed_at_the_weekend() -> None:
    status = MarketClock().status(_utc(2026, 9, 19, 16, 0))

    assert status.is_open is False
    assert "weekend" in status.reason


def test_market_is_closed_before_the_open() -> None:
    status = MarketClock().status(_utc(2026, 9, 16, 13, 0))

    assert status.is_open is False
    assert "before the 09:30 open" in status.reason


def test_market_is_closed_after_the_close() -> None:
    status = MarketClock().status(_utc(2026, 9, 16, 20, 30))

    assert status.is_open is False
    assert "after the 16:00 close" in status.reason


def test_market_session_boundaries_are_inclusive_at_the_open() -> None:
    clock = MarketClock()

    assert clock.status(_utc(2026, 9, 16, 13, 29)).is_open is False
    assert clock.status(_utc(2026, 9, 16, 13, 30)).is_open is True
    assert clock.status(_utc(2026, 9, 16, 19, 59)).is_open is True
    assert clock.status(_utc(2026, 9, 16, 20, 0)).is_open is False


def test_market_clock_follows_daylight_saving() -> None:
    clock = MarketClock()

    # 14:30 UTC is 09:30 in standard time, and closed an hour later in summer.
    assert clock.status(_utc(2026, 1, 15, 14, 30)).is_open is True
    assert clock.status(_utc(2026, 1, 15, 14, 29)).is_open is False

    # 13:30 UTC is 09:30 in daylight saving time.
    assert clock.status(_utc(2026, 7, 15, 13, 30)).is_open is True
    assert clock.status(_utc(2026, 7, 15, 13, 29)).is_open is False


def test_market_clock_switches_offset_on_the_daylight_saving_transition() -> None:
    clock = MarketClock()

    # Friday before the second Sunday of March 2026, and the Monday after it.
    assert clock.status(_utc(2026, 3, 6, 14, 30)).is_open is True
    assert clock.status(_utc(2026, 3, 6, 13, 30)).is_open is False
    assert clock.status(_utc(2026, 3, 9, 13, 30)).is_open is True
    assert clock.status(_utc(2026, 3, 9, 14, 30)).is_open is True


def test_market_clock_rejects_a_naive_moment() -> None:
    with pytest.raises(ValueError, match="timezone aware"):
        MarketClock().status(datetime(2026, 9, 16, 14, 0))


# --------------------------------------------------------------------------
# T3 - change detection
# --------------------------------------------------------------------------


def _recommendation(
    state: DecisionState = DecisionState.ACCUMULATE,
    confidence: float = 0.72,
    thesis: str = "The evidence supports accumulating.",
    references: tuple[str, ...] = ("ev-1",),
) -> Recommendation:
    """Return a recommendation built from the given fields."""
    return Recommendation(
        decision_state=state,
        confidence=confidence,
        investment_thesis=thesis,
        evidence_references=references,
    )


def _fingerprint(
    recommendation: Recommendation | None = None,
) -> RecommendationFingerprint:
    """Return the fingerprint of a recommendation, or of a default one."""
    return RecommendationFingerprint.of(recommendation or _recommendation(), "AAPL")


def test_change_detector_reports_the_first_recommendation_as_changed() -> None:
    assert ChangeDetector().observe(_fingerprint()) is True


def test_change_detector_reports_an_identical_recommendation_as_unchanged() -> None:
    detector = ChangeDetector()
    detector.observe(_fingerprint())

    assert detector.observe(_fingerprint()) is False


def test_change_detector_reports_a_new_decision_as_changed() -> None:
    detector = ChangeDetector()
    detector.observe(_fingerprint())

    changed = detector.observe(_fingerprint(_recommendation(state=DecisionState.TRIM)))

    assert changed is True


def test_change_detector_ignores_prose_that_only_embeds_a_measurement() -> None:
    detector = ChangeDetector()
    detector.observe(_fingerprint())

    changed = detector.observe(
        _fingerprint(_recommendation(thesis="Overall score moved to 13.11."))
    )

    assert changed is False


def test_fingerprint_describes_itself_for_a_log_line() -> None:
    description = _fingerprint().describe()

    assert "AAPL" in description
    assert DecisionState.ACCUMULATE.value in description
    assert "1 evidence reference(s)" in description


# --------------------------------------------------------------------------
# T1 - scheduler
# --------------------------------------------------------------------------


def test_scheduler_runs_a_single_cycle_when_the_interval_is_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.scheduler.time.sleep", _no_sleep)
    statuses: list[CycleStatus] = []

    Scheduler().run(IntervalSchedule(0, lambda: _record(statuses)))

    assert statuses == [CycleStatus.MARKET_CLOSED]


def test_scheduler_repeats_on_the_configured_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The clock is supplied, because a real sleep advances the wall clock and a
    # pretend one does not: without it the scheduler would never see the interval
    # elapse and the test would be checking nothing.
    slept: list[float] = []
    moment = [_START]
    _install_clock(monkeypatch, moment, slept, interrupt_on=2)
    statuses: list[CycleStatus] = []

    with pytest.raises(KeyboardInterrupt):
        Scheduler(lambda: moment[0]).run(
            IntervalSchedule(30, lambda: _record(statuses))
        )

    # Two cycles and two waits: the interrupt lands during the second wait.
    assert len(statuses) == 2
    assert slept == [1800, 1800]


def test_scheduler_keeps_running_when_a_cycle_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slept: list[float] = []
    moment = [_START]
    _install_clock(monkeypatch, moment, slept, interrupt_on=2)

    def failing_cycle() -> CycleStatus:
        raise RuntimeError("boom")

    with pytest.raises(KeyboardInterrupt):
        Scheduler(lambda: moment[0]).run(IntervalSchedule(30, failing_cycle))

    assert slept == [1800, 1800]


_START = datetime(2026, 9, 18, 0, 0, 0, tzinfo=UTC)


def _install_clock(
    monkeypatch: pytest.MonkeyPatch,
    moment: list[datetime],
    slept: list[float],
    *,
    interrupt_on: int,
) -> None:
    """Make the scheduler's wait advance a clock the test owns.

    Args:
        monkeypatch: Fixture used to replace the wait.
        moment: One element holding the moment the scheduler reads.
        slept: Collects how long each wait lasted.
        interrupt_on: Which wait raises, stopping the loop.
    """

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        moment[0] += timedelta(seconds=seconds)
        if len(slept) == interrupt_on:
            raise KeyboardInterrupt

    monkeypatch.setattr("app.scheduler.time.sleep", fake_sleep)


def _no_sleep(seconds: float) -> None:
    """Fail the test if the scheduler waits when it should not."""
    pytest.fail(f"scheduler slept for {seconds} seconds")


def _record(statuses: list[CycleStatus]) -> CycleStatus:
    """Record a cycle run and report a fixed status."""
    statuses.append(CycleStatus.MARKET_CLOSED)
    return CycleStatus.MARKET_CLOSED


# --------------------------------------------------------------------------
# T4 and T5 - one status per cycle, with a reason
# --------------------------------------------------------------------------


class _Clock:
    """Clock stand-in reporting a fixed session status."""

    def __init__(self, is_open: bool) -> None:
        self._is_open = is_open

    def status(self, moment: datetime) -> MarketStatus:
        reason = "test market open" if self._is_open else "test market closed"
        return MarketStatus(is_open=self._is_open, reason=reason)


class _Analyzer:
    """Analyzer stand-in returning a fixed result, or raising."""

    def __init__(
        self, result: AnalysisResult | None = None, error: Exception | None = None
    ) -> None:
        self.calls = 0
        self._result = result
        self._error = error

    def analyze_result(self, asset: Asset) -> AnalysisResult:
        self.calls += 1
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError("the stand-in analyzer has no result to return")
        return self._result


def _config(
    interval_minutes: int = 30,
    tickers: tuple[str, ...] = ("AAPL",),
    watchlist_file: Path | None = None,
) -> Config:
    """Return a configuration with no notification channel and no watchlist.

    The watchlist path points at a file that does not exist, so these tests
    exercise the fallback to the configured tickers. A test that wants the file to
    win passes a path of its own.
    """
    return Config(
        environment=Environment.TEST,
        log_level=LogLevel.INFO,
        log_dir=Path("logs"),
        log_file_name="ais.log",
        tickers=tickers,
        analysis_interval_minutes=interval_minutes,
        watchlist_file=watchlist_file or Path("missing") / "watchlist.json",
    )


def _analysis_result(ticker: str = "AAPL") -> AnalysisResult:
    """Return a minimal analysis result for a cycle to report on."""
    asset = Asset(
        ticker=ticker,
        name=ticker,
        exchange="UNKNOWN",
        currency="USD",
        profile=AssetProfile.UNKNOWN,
    )
    score = CategoryScore(
        category=Category.VALUATION,
        score=1.0,
        confidence=1.0,
        coverage=Coverage(assessed=1, total=5),
        summary="summary",
        evidence_references=(f"{ticker}.ev-1",),
    )
    assessment = OverallAssessment(
        overall_score=1.0,
        confidence=1.0,
        grade="PLACEHOLDER",
        category_scores=(score,),
    )
    return AnalysisResult(
        asset=asset,
        assessment=assessment,
        recommendation=_recommendation(),
    )


class _PerTickerAnalyzer:
    """Analyzer stand-in answering per symbol, and counting the symbols seen."""

    def __init__(self, error: Exception | None = None) -> None:
        self.seen: list[str] = []
        self._error = error

    def analyze_result(self, asset: Asset) -> AnalysisResult:
        self.seen.append(asset.ticker)
        if self._error is not None:
            raise self._error
        return _analysis_result(asset.ticker)


class _FailingAnalyzer:
    """Analyzer stand-in that fails for one symbol and answers for the rest."""

    def __init__(self, failing: str) -> None:
        self._failing = failing
        self.seen: list[str] = []

    def analyze_result(self, asset: Asset) -> AnalysisResult:
        self.seen.append(asset.ticker)
        if asset.ticker == self._failing:
            raise RuntimeError("market data exploded")
        return _analysis_result(asset.ticker)


def _application(
    clock: _Clock,
    analyzer: object,
    monkeypatch: pytest.MonkeyPatch,
    config: Config | None = None,
) -> Application:
    """Return an application wired to stand-ins, with notification faked out."""
    application = Application(
        config=config if config is not None else _config(),
        market_clock=clock,  # type: ignore[arg-type]
        analyzer=analyzer,  # type: ignore[arg-type]
    )
    monkeypatch.setattr(application, "_notify", lambda result: None)
    return application


def test_cycle_reports_market_closed_without_evaluating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer = _Analyzer(result=_analysis_result())
    application = _application(_Clock(is_open=False), analyzer, monkeypatch)

    assert application._run_cycle() is CycleStatus.MARKET_CLOSED
    assert analyzer.calls == 0


def test_cycle_reports_notification_sent_for_a_new_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[object] = []
    analyzer = _Analyzer(result=_analysis_result())
    application = _application(_Clock(is_open=True), analyzer, monkeypatch)
    monkeypatch.setattr(application, "_notify", sent.append)

    assert application._run_cycle() is CycleStatus.NOTIFICATION_SENT
    assert len(sent) == 1


def test_cycle_reports_unchanged_without_notifying(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[object] = []
    analyzer = _Analyzer(result=_analysis_result())
    application = _application(_Clock(is_open=True), analyzer, monkeypatch)
    monkeypatch.setattr(application, "_notify", sent.append)

    assert application._run_cycle() is CycleStatus.NOTIFICATION_SENT
    assert application._run_cycle() is CycleStatus.RECOMMENDATION_UNCHANGED
    assert len(sent) == 1


def test_cycle_reports_evaluation_failed_when_analysis_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer = _Analyzer(error=RuntimeError("market data exploded"))
    application = _application(_Clock(is_open=True), analyzer, monkeypatch)

    assert application._run_cycle() is CycleStatus.EVALUATION_FAILED


def test_cycle_reports_evaluation_failed_when_notification_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer = _Analyzer(result=_analysis_result())
    application = _application(_Clock(is_open=True), analyzer, monkeypatch)

    def failing_notify(result: object) -> None:
        raise RuntimeError("bark unreachable")

    monkeypatch.setattr(application, "_notify", failing_notify)

    assert application._run_cycle() is CycleStatus.EVALUATION_FAILED


# --------------------------------------------------------------------------
# What the run watches
# --------------------------------------------------------------------------


def test_a_watchlist_supplies_the_assets_to_evaluate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The file wins when it can be used. The configured tickers name two symbols
    # the file does not, and neither of them is evaluated.
    path = tmp_path / "watchlist.json"
    path.write_text(
        json.dumps(
            {
                "members": [
                    {
                        "symbol": "NVDA",
                        "name": "NVIDIA Corporation",
                        "exchange": "NASDAQ",
                        "currency": "USD",
                        "profile": "high_growth",
                        "sets": ["growth"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    analyzer = _PerTickerAnalyzer()
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL", "BABA"), watchlist_file=path),
    )

    assert application._run_cycle() is CycleStatus.NOTIFICATION_SENT
    assert analyzer.seen == ["NVDA"]


def test_the_watchlist_supplies_the_asset_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # AssetProfile was declared, carried and never set: every asset was built as
    # unknown. The watchlist is what finally gives an asset its kind.
    path = tmp_path / "watchlist.json"
    path.write_text(
        json.dumps(
            {
                "members": [
                    {
                        "symbol": "CGDV",
                        "name": "Capital Group Dividend Value ETF",
                        "exchange": "NYSE Arca",
                        "currency": "USD",
                        "profile": "etf",
                        "sets": ["core"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    analyzer = _PerTickerAnalyzer()
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL",), watchlist_file=path),
    )

    application._run_cycle()

    asset = application._universe.assets[0]
    assert asset.ticker == "CGDV"
    assert asset.name == "Capital Group Dividend Value ETF"
    assert asset.exchange == "NYSE Arca"
    assert asset.profile is AssetProfile.ETF


def test_an_unusable_watchlist_leaves_the_configured_tickers_watching(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A file that cannot be trusted is not used, and nothing goes missing quietly
    # on the way back to the tickers.
    path = tmp_path / "watchlist.json"
    path.write_text("{not json", encoding="utf-8")
    analyzer = _PerTickerAnalyzer()
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL", "BABA"), watchlist_file=path),
    )

    assert application._run_cycle() is CycleStatus.NOTIFICATION_SENT
    assert analyzer.seen == ["AAPL", "BABA"]


def test_without_a_watchlist_the_configured_tickers_are_watched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer = _PerTickerAnalyzer()
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL", "RKLB")),
    )

    application._run_cycle()

    assert analyzer.seen == ["AAPL", "RKLB"]
    assert application._universe_loaded is False


def test_every_cycle_status_is_distinct() -> None:
    values = [status.value for status in CycleStatus]

    assert len(values) == len(set(values)) == 4


# --------------------------------------------------------------------------
# Several symbols per cycle
# --------------------------------------------------------------------------


def test_change_detector_keeps_one_fingerprint_per_symbol() -> None:
    detector = ChangeDetector()
    aapl = RecommendationFingerprint.of(_recommendation(), "AAPL")
    rklb = RecommendationFingerprint.of(_recommendation(), "RKLB")

    assert detector.observe(aapl) is True
    assert detector.observe(rklb) is True
    assert detector.observe(aapl) is False
    assert detector.observe(rklb) is False


def test_cycle_evaluates_every_configured_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer = _PerTickerAnalyzer()
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL", "BABA", "RKLB")),
    )

    assert application._run_cycle() is CycleStatus.NOTIFICATION_SENT
    assert analyzer.seen == ["AAPL", "BABA", "RKLB"]


def test_cycle_notifies_once_per_changed_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []
    analyzer = _PerTickerAnalyzer()
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL", "RKLB")),
    )
    monkeypatch.setattr(
        application, "_notify", lambda result: sent.append(result.asset.ticker)
    )

    assert application._run_cycle() is CycleStatus.NOTIFICATION_SENT
    assert sent == ["AAPL", "RKLB"]

    assert application._run_cycle() is CycleStatus.RECOMMENDATION_UNCHANGED
    assert sent == ["AAPL", "RKLB"]


def test_one_failing_symbol_does_not_stop_the_others(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []
    analyzer = _FailingAnalyzer(failing="BABA")
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL", "BABA", "RKLB")),
    )
    monkeypatch.setattr(
        application, "_notify", lambda result: sent.append(result.asset.ticker)
    )

    assert application._run_cycle() is CycleStatus.EVALUATION_FAILED
    assert analyzer.seen == ["AAPL", "BABA", "RKLB"]
    assert sent == ["AAPL", "RKLB"]


def test_cycle_is_unchanged_only_when_every_symbol_is_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer = _PerTickerAnalyzer()
    application = _application(
        _Clock(is_open=True),
        analyzer,
        monkeypatch,
        config=_config(tickers=("AAPL", "RKLB")),
    )

    application._run_cycle()

    assert application._run_cycle() is CycleStatus.RECOMMENDATION_UNCHANGED


# --------------------------------------------------------------------------
# T1 - default interval
# --------------------------------------------------------------------------


def test_default_interval_is_thirty_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIS_ANALYSIS_INTERVAL_MINUTES", raising=False)

    assert Config.from_environment().analysis_interval_minutes == 30
