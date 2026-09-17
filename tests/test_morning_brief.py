"""Tests for the daily morning brief and the runtime that owes it.

The brief is the one piece of work AIS does at a stated hour rather than on an
interval. These tests describe the five things it has to be: sent once a day, not
gated by the market, not gated by whether anything changed, computed when it is
sent, and not repeated after a restart.

The clock is supplied to the scheduler and to the moment in every test that cares
about an hour, because a test that waits for 09:00 is a test nobody runs.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from analysis.analysis_result import AnalysisResult
from app.application import MORNING_BRIEF_MOMENT, Application
from app.morning_brief import MorningBrief
from app.runtime_state import RuntimeState
from app.scheduler import IntervalSchedule, Scheduler
from config.config import Config
from contracts.market_data_provider import MarketDataSnapshot
from models.asset import Asset
from models.category import Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation
from utils.constants import CycleStatus, Environment, LogLevel
from utils.daily_moment import DailyMoment
from utils.market_clock import MarketClock, MarketStatus

# 09:00 Beijing is 01:00 UTC, and the moment the brief is owed at.
_NINE_BEIJING_UTC = datetime(2026, 9, 18, 1, 0, tzinfo=UTC)
_BEFORE = _NINE_BEIJING_UTC - timedelta(minutes=30)


def _brief(
    work, state: RuntimeState, moment: DailyMoment | None = None
) -> MorningBrief:
    return MorningBrief(moment or MORNING_BRIEF_MOMENT, state, work)


# --------------------------------------------------------------------------
# A moment of the day
# --------------------------------------------------------------------------


def test_a_moment_is_a_time_of_day_in_an_offset() -> None:
    moment = DailyMoment.beijing(hour=9, minute=0)

    assert moment.describe() == "09:00 UTC+08:00"
    assert moment.at(_BEFORE) == _NINE_BEIJING_UTC


def test_the_local_day_is_the_readers_day_not_the_servers() -> None:
    # 01:00 UTC on the eighteenth is already the eighteenth in Beijing, but 17:00
    # UTC on the eighteenth is the nineteenth there.
    late = datetime(2026, 9, 18, 17, 0, tzinfo=UTC)

    assert MORNING_BRIEF_MOMENT.local_day(_BEFORE) == date(2026, 9, 18)
    assert MORNING_BRIEF_MOMENT.local_day(late) == date(2026, 9, 19)


def test_a_moment_that_is_not_a_time_of_day_is_refused() -> None:
    with pytest.raises(ValueError):
        DailyMoment.beijing(hour=24, minute=0)
    with pytest.raises(ValueError):
        DailyMoment.beijing(hour=9, minute=60)


def test_an_hour_already_behind_is_owed_now_rather_than_skipped() -> None:
    # A brief missed because the process was not running is sent late, not dropped.
    after = _NINE_BEIJING_UTC + timedelta(hours=4)

    assert MORNING_BRIEF_MOMENT.next_due(
        after, sent_on=None
    ) == MORNING_BRIEF_MOMENT.at(after)
    assert MORNING_BRIEF_MOMENT.next_due(after, sent_on=None) <= after


# --------------------------------------------------------------------------
# What the runtime remembers
# --------------------------------------------------------------------------


def test_nothing_has_been_sent_when_nothing_is_written(tmp_path: Path) -> None:
    assert RuntimeState(path=tmp_path / "runtime.json").brief_sent_on() is None


def test_the_day_is_remembered_across_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    RuntimeState(path=path).record_brief_sent(date(2026, 9, 18))

    # A different object reading the same file is what a restart looks like.
    assert RuntimeState(path=path).brief_sent_on() == date(2026, 9, 18)


def test_an_unreadable_state_file_is_treated_as_an_empty_one(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    path.write_text("{not json", encoding="utf-8")

    assert RuntimeState(path=path).brief_sent_on() is None


def test_a_state_file_that_cannot_be_written_does_not_raise(tmp_path: Path) -> None:
    # Losing the state file costs a repeated brief at worst, and a crash costs the
    # brief entirely.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    RuntimeState(path=blocker / "runtime.json").record_brief_sent(date(2026, 9, 18))


def test_the_state_file_holds_the_day_and_nothing_else(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    RuntimeState(path=path).record_brief_sent(date(2026, 9, 18))

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "morning_brief_sent_on": "2026-09-18"
    }


# --------------------------------------------------------------------------
# The brief is owed once a local day
# --------------------------------------------------------------------------


def _counting_work(status: CycleStatus = CycleStatus.NOTIFICATION_SENT):
    calls: list[int] = []

    def work() -> CycleStatus:
        calls.append(1)
        return status

    return work, calls


def test_the_brief_is_owed_at_the_hour_it_is_stated(tmp_path: Path) -> None:
    brief = _brief(
        lambda: CycleStatus.NOTIFICATION_SENT, RuntimeState(tmp_path / "s.json")
    )

    assert brief.next_due(_BEFORE) == _NINE_BEIJING_UTC


def test_the_brief_is_not_owed_again_once_today_is_done(tmp_path: Path) -> None:
    state = RuntimeState(path=tmp_path / "s.json")
    brief = _brief(lambda: CycleStatus.NOTIFICATION_SENT, state)
    brief.work()

    assert brief.next_due(_NINE_BEIJING_UTC) == _NINE_BEIJING_UTC + timedelta(days=1)


def test_a_restarted_brief_does_not_send_a_second_copy(tmp_path: Path) -> None:
    # The whole point of writing the day down: the process that sends the brief is
    # not the process that remembers sending it.
    path = tmp_path / "s.json"
    work, calls = _counting_work()
    _brief(work, RuntimeState(path=path)).work()

    restarted = _brief(work, RuntimeState(path=path))

    assert restarted.next_due(
        _NINE_BEIJING_UTC + timedelta(hours=1)
    ) > _NINE_BEIJING_UTC + timedelta(hours=1)
    assert len(calls) == 1


def test_a_brief_that_was_missed_is_still_owed(tmp_path: Path) -> None:
    # Yesterday's brief says nothing about today's.
    path = tmp_path / "s.json"
    RuntimeState(path=path).record_brief_sent(date(2026, 9, 17))

    brief = _brief(lambda: CycleStatus.NOTIFICATION_SENT, RuntimeState(path=path))

    assert brief.next_due(_NINE_BEIJING_UTC) == _NINE_BEIJING_UTC


def test_the_brief_records_the_day_it_ran(tmp_path: Path) -> None:
    state = RuntimeState(path=tmp_path / "s.json")

    _brief(lambda: CycleStatus.NOTIFICATION_SENT, state).work()

    assert state.brief_sent_on() == date(2026, 9, 18)


def test_a_failed_brief_is_not_retried_all_day(tmp_path: Path) -> None:
    # A failure is reported as a failure. Retrying would send a second copy to
    # whoever the first attempt reached, and would repeat the whole evaluation on
    # every wake until the failure stopped.
    state = RuntimeState(path=tmp_path / "s.json")
    brief = _brief(lambda: CycleStatus.EVALUATION_FAILED, state)

    assert brief.work() is CycleStatus.EVALUATION_FAILED
    assert state.brief_sent_on() == date(2026, 9, 18)


def test_a_state_file_that_cannot_be_written_does_not_turn_the_brief_into_a_loop(
    tmp_path: Path,
) -> None:
    # The remembered day is what keeps a broken state file from making the brief
    # permanently due.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    brief = _brief(
        lambda: CycleStatus.NOTIFICATION_SENT, RuntimeState(path=blocker / "s.json")
    )

    brief.work()

    assert brief.next_due(_NINE_BEIJING_UTC) == _NINE_BEIJING_UTC + timedelta(days=1)


# --------------------------------------------------------------------------
# The scheduler lands on the hour
# --------------------------------------------------------------------------


def _clock_and_sleep(
    monkeypatch: pytest.MonkeyPatch, start: datetime, *, interrupt_on: int = 2
):
    moment = [start]
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        moment[0] += timedelta(seconds=seconds)
        if len(slept) == interrupt_on:
            raise KeyboardInterrupt

    monkeypatch.setattr("app.scheduler.time.sleep", fake_sleep)
    return moment, slept


def test_the_scheduler_waits_until_the_hour_and_then_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    moment, slept = _clock_and_sleep(monkeypatch, _BEFORE)
    work, calls = _counting_work()

    with pytest.raises(KeyboardInterrupt):
        Scheduler(lambda: moment[0]).run(
            _brief(work, RuntimeState(path=tmp_path / "s.json"))
        )

    # It waited exactly the half hour to the hour, ran once, then waited until
    # tomorrow's — not on an interval, and not from when the process started.
    assert slept == [1800, 86400]
    assert len(calls) == 1


def test_the_scheduler_runs_the_brief_even_though_the_market_is_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The hour the brief is owed at falls outside the United States session by
    # definition. A report that waits for a market to open never arrives at the hour
    # it was asked for.
    closed = MarketClock().status(_NINE_BEIJING_UTC)
    assert closed.is_open is False

    moment, _ = _clock_and_sleep(monkeypatch, _BEFORE)
    work, calls = _counting_work()

    with pytest.raises(KeyboardInterrupt):
        Scheduler(lambda: moment[0]).run(
            _brief(work, RuntimeState(path=tmp_path / "s.json"))
        )

    assert len(calls) == 1


def test_the_scheduler_runs_whichever_schedule_is_owed_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The cycle is owed every ten minutes and the brief at the hour, so the brief
    # waits for the cycle rather than the cycle drifting onto the brief.
    moment, slept = _clock_and_sleep(monkeypatch, _BEFORE, interrupt_on=4)
    statuses: list[str] = []

    def cycle() -> CycleStatus:
        statuses.append("cycle")
        return CycleStatus.MARKET_CLOSED

    brief_work, briefs = _counting_work()
    with pytest.raises(KeyboardInterrupt):
        Scheduler(lambda: moment[0]).run(
            IntervalSchedule(10, cycle),
            _brief(brief_work, RuntimeState(path=tmp_path / "s.json")),
        )

    # Every wait is the cycle's interval, and the brief runs once — on the hour,
    # alongside the cycle rather than instead of it.
    assert slept == [600, 600, 600, 600]
    assert len(statuses) == 4
    assert len(briefs) == 1


# --------------------------------------------------------------------------
# The brief through the application
# --------------------------------------------------------------------------


class _ClosedMarket:
    """Clock reporting a closed market, whatever the moment."""

    def status(self, moment: datetime) -> MarketStatus:
        return MarketStatus(is_open=False, reason="closed for the test")


class _OpenMarket:
    """Clock reporting an open market, whatever the moment."""

    def status(self, moment: datetime) -> MarketStatus:
        return MarketStatus(is_open=True, reason="open for the test")


class _Analyzer:
    """Analyzer stand-in counting the assets it was asked about."""

    def __init__(self) -> None:
        self.seen: list[str] = []

    def analyze_result(self, asset: Asset) -> AnalysisResult:
        self.seen.append(asset.ticker)
        return _result(asset)


def _result(asset: Asset) -> AnalysisResult:
    return AnalysisResult(
        asset=asset,
        assessment=OverallAssessment(
            overall_score=1.0,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=(
                CategoryScore(
                    category=Category.VALUATION,
                    score=1.0,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=(f"{asset.ticker}.ev-1",),
                ),
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder.",
            evidence_references=(f"{asset.ticker}.ev-1",),
        ),
        market_data=_snapshot(),
    )


def _snapshot() -> MarketDataSnapshot:
    from contracts.market_data_provider import MarketDataPoint, MarketMetric

    return MarketDataSnapshot(
        symbol="AAPL",
        source="test",
        retrieved_at=_BEFORE,
        points=tuple(
            MarketDataPoint(metric=metric, value=None, reason="test")
            for metric in MarketMetric
        ),
    )


def _application(
    tmp_path: Path, analyzer: _Analyzer, market_clock: object | None = None
) -> Application:
    return Application(
        config=Config(
            environment=Environment.TEST,
            log_level=LogLevel.INFO,
            log_dir=tmp_path,
            log_file_name="ais.log",
            tickers=("AAPL", "RKLB"),
            watchlist_file=tmp_path / "no-watchlist.json",
            state_file=tmp_path / "runtime.json",
        ),
        market_clock=market_clock or _ClosedMarket(),  # type: ignore[arg-type]
        analyzer=analyzer,  # type: ignore[arg-type]
    )


def test_the_brief_is_produced_while_the_market_is_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    sent: list[str] = []
    monkeypatch.setattr(
        application, "_notify", lambda result: sent.append(result.asset.ticker)
    )

    status = application._run_brief()

    assert status is CycleStatus.NOTIFICATION_SENT
    assert sent == ["AAPL", "RKLB"]


def test_the_brief_sends_even_when_nothing_changed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The cycle says nothing when nothing changed, because it exists to report
    # change. The brief is expected, and most days look like this one.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    sent: list[str] = []
    monkeypatch.setattr(
        application, "_notify", lambda result: sent.append(result.asset.ticker)
    )

    application._run_brief()
    application._run_brief()

    assert sent == ["AAPL", "RKLB", "AAPL", "RKLB"]


def test_the_cycle_still_says_nothing_when_nothing_changed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer, _OpenMarket())
    sent: list[str] = []
    monkeypatch.setattr(
        application, "_notify", lambda result: sent.append(result.asset.ticker)
    )

    first = application._run_brief()
    second = application._run_cycle()

    assert first is CycleStatus.NOTIFICATION_SENT
    assert second is CycleStatus.RECOMMENDATION_UNCHANGED
    assert sent == ["AAPL", "RKLB"]


def test_the_brief_is_computed_when_it_is_sent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Nothing is analysed until the brief runs, so there is no earlier result to
    # deliver late.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    monkeypatch.setattr(application, "_notify", lambda result: None)

    assert analyzer.seen == []
    application._run_brief()
    assert analyzer.seen == ["AAPL", "RKLB"]


def test_the_application_schedules_both_things(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    ran: list[str] = []
    monkeypatch.setattr(
        "app.application.Scheduler.run",
        lambda self, *schedules: ran.extend(schedule.name for schedule in schedules),
    )

    application.run()

    assert ran == ["cycle", "morning-brief"]


def test_the_brief_is_owed_once_a_day_at_nine_beijing() -> None:
    assert MORNING_BRIEF_MOMENT.describe() == "09:00 UTC+08:00"
    assert MORNING_BRIEF_MOMENT.at(_BEFORE) == _NINE_BEIJING_UTC
