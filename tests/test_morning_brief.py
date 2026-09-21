"""Tests for the daily morning brief and the runtime that owes it.

The brief is the one piece of work AIS does at a stated hour rather than on an
interval. These tests describe the six things it has to be: sent once a day, not
gated by the market, not gated by whether anything changed, computed when it is sent,
not repeated after a restart, and — when it reaches nobody — still owed rather than
recorded as done.

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
from app.morning_brief import (
    BRIEF_RETRY_INTERVAL,
    MAX_BRIEF_ATTEMPTS,
    BriefOutcome,
    MorningBrief,
)
from app.runtime_state import ReportDelivery, ReportName, ReportRecord, RuntimeState
from app.scheduler import IntervalSchedule, Scheduler
from config.config import Config
from contracts.market_data_provider import MarketDataSnapshot
from contracts.market_environment import (
    WIDE_METRICS,
    EnvironmentPoint,
    EnvironmentSnapshot,
)
from models.asset import Asset
from models.category import Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation
from utils.constants import CycleStatus, Environment, LogLevel
from utils.daily_moment import DailyMoment
from utils.exceptions import AISException
from utils.market_clock import MarketClock, MarketStatus

# 09:00 Beijing is 01:00 UTC, and the moment the brief is owed at.
_NINE_BEIJING_UTC = datetime(2026, 9, 18, 1, 0, tzinfo=UTC)
_BEFORE = _NINE_BEIJING_UTC - timedelta(minutes=30)


def _brief(
    work,
    state: RuntimeState,
    moment: DailyMoment | None = None,
    clock=None,
) -> MorningBrief:
    """Return a brief that reads the moment it is run at from a supplied clock.

    The day recorded is the day the brief ran, so a test that asserted a particular
    day against the system clock would pass on the day it was written and start
    failing later. Every test here supplies the moment instead.
    """
    return MorningBrief(
        moment or MORNING_BRIEF_MOMENT,
        state,
        work,
        clock if clock is not None else lambda: _NINE_BEIJING_UTC,
    )


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


def test_nothing_is_recorded_when_nothing_is_written(tmp_path: Path) -> None:
    assert (
        RuntimeState(path=tmp_path / "runtime.json").report(ReportName.MORNING_BRIEF)
        is None
    )


def test_the_state_of_the_day_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    record = ReportRecord(
        day=date(2026, 9, 18),
        delivery=ReportDelivery.OWED,
        attempts=2,
        attempted_at=_NINE_BEIJING_UTC,
    )
    RuntimeState(path=path).record_report(ReportName.MORNING_BRIEF, record)

    # A different object reading the same file is what a restart looks like.
    assert RuntimeState(path=path).report(ReportName.MORNING_BRIEF) == record


def test_the_state_file_holds_the_day_the_state_and_the_attempts(
    tmp_path: Path,
) -> None:
    # Not a flag: a day that reached nobody is owed, and "a brief was sent at some
    # point" cannot say that.
    path = tmp_path / "runtime.json"
    RuntimeState(path=path).record_report(
        ReportName.MORNING_BRIEF,
        ReportRecord(
            day=date(2026, 9, 18),
            delivery=ReportDelivery.SENT,
            attempts=1,
            attempted_at=_NINE_BEIJING_UTC,
        ),
    )

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "reports": {
            "morning_brief": {
                "day": "2026-09-18",
                "delivery": "sent",
                "attempts": 1,
                "attempted_at": _NINE_BEIJING_UTC.isoformat(),
            }
        }
    }


def test_the_record_written_today_is_still_read(tmp_path: Path) -> None:
    # The state on disk was written before a report had a bucket of its own. The day it
    # names is a fact the runtime recorded, so the upgrade reads it rather than treating
    # the day as owed and sending the reader a second copy.
    path = tmp_path / "runtime.json"
    path.write_text(
        json.dumps(
            {
                "morning_brief": {
                    "day": "2026-09-18",
                    "delivery": "sent",
                    "attempts": 1,
                    "attempted_at": _NINE_BEIJING_UTC.isoformat(),
                }
            }
        ),
        encoding="utf-8",
    )

    record = RuntimeState(path=path).report(ReportName.MORNING_BRIEF)

    assert record == ReportRecord(
        day=date(2026, 9, 18),
        delivery=ReportDelivery.SENT,
        attempts=1,
        attempted_at=_NINE_BEIJING_UTC,
    )


def test_one_reports_state_is_not_another_reports(tmp_path: Path) -> None:
    # The point of a bucket per report: two reports that shared one would each read the
    # other's day as their own, and would then either send a second copy or stay silent.
    path = tmp_path / "runtime.json"
    path.write_text(
        json.dumps(
            {
                "reports": {
                    "premarket_brief": {
                        "day": "2026-09-18",
                        "delivery": "sent",
                        "attempts": 1,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    state = RuntimeState(path=path)

    assert state.report(ReportName.MORNING_BRIEF) is None


def test_writing_one_report_leaves_the_others_as_they_were(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    path.write_text(
        json.dumps(
            {
                "reports": {
                    "premarket_brief": {
                        "day": "2026-09-17",
                        "delivery": "abandoned",
                        "attempts": 3,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    RuntimeState(path=path).record_report(
        ReportName.MORNING_BRIEF,
        ReportRecord(day=date(2026, 9, 18), delivery=ReportDelivery.SENT, attempts=1),
    )

    written = json.loads(path.read_text(encoding="utf-8"))
    assert set(written["reports"]) == {"premarket_brief", "morning_brief"}
    assert written["reports"]["premarket_brief"]["delivery"] == "abandoned"


def test_the_earlier_shapes_are_not_written_again(tmp_path: Path) -> None:
    # Once the record is in its own bucket the older keys are dropped, so the file
    # cannot hold two records for one report that disagree about the day.
    path = tmp_path / "runtime.json"
    path.write_text('{"morning_brief_sent_on": "2026-09-17"}', encoding="utf-8")

    RuntimeState(path=path).record_report(
        ReportName.MORNING_BRIEF, ReportRecord(day=date(2026, 9, 18))
    )

    written = json.loads(path.read_text(encoding="utf-8"))
    assert "morning_brief_sent_on" not in written
    assert "morning_brief" not in written


def test_a_state_file_from_the_older_format_is_still_read(tmp_path: Path) -> None:
    # The day the older format recorded is a fact the runtime wrote down. Forgetting
    # it would make a day that was already reported look owed, and the reader would
    # get a second copy the moment the process restarted.
    path = tmp_path / "runtime.json"
    path.write_text('{"morning_brief_sent_on": "2026-09-18"}', encoding="utf-8")

    record = RuntimeState(path=path).report(ReportName.MORNING_BRIEF)

    assert record is not None
    assert record.day == date(2026, 9, 18)
    assert record.delivery is ReportDelivery.SENT


def test_a_record_that_cannot_be_read_is_treated_as_no_record(tmp_path: Path) -> None:
    # Half a record would be a claim about a day that the runtime did not make.
    path = tmp_path / "runtime.json"
    path.write_text(
        '{"morning_brief": {"day": "not a day", "delivery": "sent"}}', encoding="utf-8"
    )

    assert RuntimeState(path=path).report(ReportName.MORNING_BRIEF) is None


def test_an_unknown_state_is_treated_as_no_record(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    path.write_text(
        '{"morning_brief": {"day": "2026-09-18", "delivery": "probably"}}',
        encoding="utf-8",
    )

    assert RuntimeState(path=path).report(ReportName.MORNING_BRIEF) is None


def test_an_unreadable_state_file_is_treated_as_an_empty_one(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    path.write_text("{not json", encoding="utf-8")

    assert RuntimeState(path=path).report(ReportName.MORNING_BRIEF) is None


def test_a_state_file_that_cannot_be_written_does_not_raise(tmp_path: Path) -> None:
    # Losing the state file costs a repeated brief at worst, and a crash costs the
    # brief entirely.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    RuntimeState(path=blocker / "runtime.json").record_report(
        ReportName.MORNING_BRIEF, ReportRecord(day=date(2026, 9, 18))
    )


# --------------------------------------------------------------------------
# The brief is owed once a local day
# --------------------------------------------------------------------------


def _delivered(status: CycleStatus = CycleStatus.NOTIFICATION_SENT) -> BriefOutcome:
    """Return an outcome where the message reached at least one reader."""
    return BriefOutcome(status=status, delivered=True)


def _undelivered() -> BriefOutcome:
    """Return an outcome where the message reached nobody."""
    return BriefOutcome(status=CycleStatus.EVALUATION_FAILED, delivered=False)


def _counting_work(delivered: bool = True):
    calls: list[int] = []

    def work() -> BriefOutcome:
        calls.append(1)
        return _delivered() if delivered else _undelivered()

    return work, calls


def test_the_brief_is_owed_at_the_hour_it_is_stated(tmp_path: Path) -> None:
    brief = _brief(lambda: _delivered(), RuntimeState(tmp_path / "s.json"))

    assert brief.next_due(_BEFORE) == _NINE_BEIJING_UTC


def test_the_brief_is_not_owed_again_once_today_is_delivered(tmp_path: Path) -> None:
    state = RuntimeState(path=tmp_path / "s.json")
    brief = _brief(lambda: _delivered(), state)
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
    RuntimeState(path=path).record_report(
        ReportName.MORNING_BRIEF,
        ReportRecord(day=date(2026, 9, 17), delivery=ReportDelivery.SENT, attempts=1),
    )

    brief = _brief(lambda: _delivered(), RuntimeState(path=path))

    assert brief.next_due(_NINE_BEIJING_UTC) == _NINE_BEIJING_UTC


def test_a_delivered_brief_settles_the_day(tmp_path: Path) -> None:
    state = RuntimeState(path=tmp_path / "s.json")

    _brief(lambda: _delivered(), state).work()

    record = state.report(ReportName.MORNING_BRIEF)
    assert record is not None
    assert record.day == date(2026, 9, 18)
    assert record.delivery is ReportDelivery.SENT
    assert record.attempts == 1


def test_a_partial_failure_still_counts_as_delivered(tmp_path: Path) -> None:
    # An asset that could not be analysed is a run that failed; a message that one of
    # several channels carried is a message that arrived. Only the second is about
    # delivery, and resending on the first would send a second copy to whoever the
    # first attempt reached.
    state = RuntimeState(path=tmp_path / "s.json")

    _brief(lambda: _delivered(CycleStatus.EVALUATION_FAILED), state).work()

    record = state.report(ReportName.MORNING_BRIEF)
    assert record is not None
    assert record.delivery is ReportDelivery.SENT


# --------------------------------------------------------------------------
# A brief that reached nobody is still owed
# --------------------------------------------------------------------------


def test_a_brief_that_reached_nobody_is_not_recorded_as_sent(tmp_path: Path) -> None:
    state = RuntimeState(path=tmp_path / "s.json")

    status = _brief(lambda: _undelivered(), state).work()

    record = state.report(ReportName.MORNING_BRIEF)
    assert status is CycleStatus.EVALUATION_FAILED
    assert record is not None
    assert record.delivery is ReportDelivery.OWED
    assert record.attempts == 1


def test_a_brief_that_reached_nobody_is_not_tried_again_immediately(
    tmp_path: Path,
) -> None:
    # The hour it is owed at is already behind, so without the spacing a failed brief
    # would be due the moment it failed — a loop that costs a full analysis each time.
    state = RuntimeState(path=tmp_path / "s.json")
    brief = _brief(lambda: _undelivered(), state)
    brief.work()

    assert brief.next_due(_NINE_BEIJING_UTC) == _NINE_BEIJING_UTC + BRIEF_RETRY_INTERVAL


def test_a_brief_that_reached_nobody_is_retried_after_the_interval(
    tmp_path: Path,
) -> None:
    state = RuntimeState(path=tmp_path / "s.json")
    brief = _brief(lambda: _undelivered(), state)
    brief.work()

    assert brief.next_due(_NINE_BEIJING_UTC + BRIEF_RETRY_INTERVAL) <= (
        _NINE_BEIJING_UTC + BRIEF_RETRY_INTERVAL
    )


def test_a_brief_is_attempted_at_most_the_stated_number_of_times(
    tmp_path: Path,
) -> None:
    # Capped, because a report the reader opened the morning for stops being that
    # report if it arrives at noon, and because an outage that does not end must not
    # keep the runtime busy until midnight.
    state = RuntimeState(path=tmp_path / "s.json")
    brief = _brief(lambda: _undelivered(), state)

    for _ in range(MAX_BRIEF_ATTEMPTS):
        brief.work()

    record = state.report(ReportName.MORNING_BRIEF)
    assert record is not None
    assert record.attempts == MAX_BRIEF_ATTEMPTS
    assert record.delivery is ReportDelivery.ABANDONED


def test_a_brief_that_ran_out_of_attempts_is_not_tried_again_that_day(
    tmp_path: Path,
) -> None:
    state = RuntimeState(path=tmp_path / "s.json")
    brief = _brief(lambda: _undelivered(), state)
    for _ in range(MAX_BRIEF_ATTEMPTS):
        brief.work()

    assert brief.next_due(_NINE_BEIJING_UTC + timedelta(hours=6)) == (
        _NINE_BEIJING_UTC + timedelta(days=1)
    )


def test_a_delivery_after_a_failure_settles_the_day(tmp_path: Path) -> None:
    # An outage that ends is the case the retry exists for.
    state = RuntimeState(path=tmp_path / "s.json")
    outcomes = [_undelivered(), _delivered()]
    brief = _brief(lambda: outcomes.pop(0), state)

    brief.work()
    brief.work()

    record = state.report(ReportName.MORNING_BRIEF)
    assert record is not None
    assert record.delivery is ReportDelivery.SENT
    assert record.attempts == 2
    assert brief.next_due(_NINE_BEIJING_UTC) == _NINE_BEIJING_UTC + timedelta(days=1)


def test_the_attempts_survive_a_restart(tmp_path: Path) -> None:
    # A process that restarts after a failed brief must not start the count again,
    # or a persistent outage would be retried for ever by a process that keeps
    # coming back.
    path = tmp_path / "s.json"
    RuntimeState(path=path).record_report(
        ReportName.MORNING_BRIEF,
        ReportRecord(
            day=date(2026, 9, 18),
            delivery=ReportDelivery.OWED,
            attempts=MAX_BRIEF_ATTEMPTS,
            attempted_at=_NINE_BEIJING_UTC,
        ),
    )
    work, calls = _counting_work(delivered=False)

    restarted = _brief(work, RuntimeState(path=path))
    restarted.work()

    record = RuntimeState(path=path).report(ReportName.MORNING_BRIEF)
    assert record is not None
    assert record.delivery is ReportDelivery.ABANDONED
    assert calls == [1]


def test_a_state_file_that_cannot_be_written_still_caps_the_attempts(
    tmp_path: Path,
) -> None:
    # The process keeps its own copy of what it has done, so a broken state file
    # cannot make the brief permanently due.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    brief = _brief(lambda: _undelivered(), RuntimeState(path=blocker / "s.json"))
    for _ in range(MAX_BRIEF_ATTEMPTS):
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

    def __init__(self, failing: tuple[str, ...] = ()) -> None:
        self.seen: list[str] = []
        self.environments: list[object] = []
        self._failing = failing

    def analyze_result(
        self, asset: Asset, *, environment: object = None
    ) -> AnalysisResult:
        self.seen.append(asset.ticker)
        self.environments.append(environment)
        if asset.ticker in self._failing:
            raise RuntimeError(f"{asset.ticker} could not be analysed")
        return _result(asset)


class _Environment:
    """Environment stand-in, counting how often the runtime asks for it.

    The real one reaches the network, and a source that could not be reached is a
    different test from one that could. It answers with no values, which is what the
    brief does without an environment: it says nothing about the market.
    """

    def __init__(self) -> None:
        self.calls = 0

    def fetch(self) -> EnvironmentSnapshot:
        self.calls += 1
        return EnvironmentSnapshot(
            source="Test environment",
            retrieved_at=_BEFORE,
            points=tuple(
                EnvironmentPoint(metric=metric, value=None, reason="test reason")
                for metric in WIDE_METRICS
            ),
        )


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
    tmp_path: Path,
    analyzer: _Analyzer,
    market_clock: object | None = None,
    environment: object | None = None,
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
        environment_provider=(  # type: ignore[arg-type]
            environment if environment is not None else _Environment()
        ),
    )


def _deliveries(monkeypatch: pytest.MonkeyPatch, application: Application) -> list:
    """Capture what the brief sends, as the (title, message) each channel carries."""
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        application,
        "_deliver",
        lambda title, message: sent.append((title, message)),
    )
    return sent


def test_the_brief_is_one_message_however_many_assets_are_watched(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Two assets are analysed and one message is sent. This is the change of shape:
    # the watch universe and the message are no longer the same size.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    sent = _deliveries(monkeypatch, application)

    outcome = application._run_brief()

    assert outcome.status is CycleStatus.NOTIFICATION_SENT
    assert outcome.delivered is True
    assert len(sent) == 1
    title, message = sent[0]
    assert title.startswith("AIS 晨报")
    assert message.startswith("AIS 晨报")
    assert "AAPL" in message and "RKLB" in message


def test_the_brief_is_produced_while_the_market_is_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The hour the brief is owed at falls outside the United States session by
    # definition, so the market clock must not be consulted at all.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    sent = _deliveries(monkeypatch, application)

    outcome = application._run_brief()

    assert outcome.status is CycleStatus.NOTIFICATION_SENT
    assert outcome.delivered is True
    assert len(sent) == 1


def test_the_brief_sends_even_when_nothing_changed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The cycle says nothing when nothing changed, because it exists to report
    # change. The brief is expected, and most days look like this one.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    sent = _deliveries(monkeypatch, application)

    application._run_brief()
    application._run_brief()

    assert len(sent) == 2


def test_the_brief_covers_every_asset_it_does_not_write_out(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Coverage and projection are different sets, and the brief states both: a
    # reader who is told only what is shown cannot tell a quiet universe from a
    # narrow one.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    sent = _deliveries(monkeypatch, application)

    application._run_brief()

    assert analyzer.seen == ["AAPL", "RKLB"]
    assert "分析 2 个标的" in sent[0][1]


def test_the_cycle_still_sends_one_message_per_changed_asset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The cycle reports change about an asset and is not a brief: one asset
    # changed, so a message about that asset is its own report.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer, _OpenMarket())
    sent = _deliveries(monkeypatch, application)

    first = application._run_brief()
    second = application._run_cycle()
    third = application._run_cycle()

    assert first.status is CycleStatus.NOTIFICATION_SENT
    assert first.delivered is True
    assert second is CycleStatus.RECOMMENDATION_UNCHANGED
    assert third is CycleStatus.RECOMMENDATION_UNCHANGED
    assert len(sent) == 1


def test_a_cycle_message_is_about_one_asset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer, _OpenMarket())
    sent = _deliveries(monkeypatch, application)

    application._run_cycle()

    title, message = sent[0]
    assert "AIS Recommendation" in title
    assert "AIS 日报" in message


def test_the_brief_is_computed_when_it_is_sent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Nothing is analysed until the brief runs, so there is no earlier result to
    # deliver late.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    _deliveries(monkeypatch, application)

    assert analyzer.seen == []
    application._run_brief()
    assert analyzer.seen == ["AAPL", "RKLB"]


def test_a_brief_with_nothing_analysed_is_not_sent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A brief with nothing behind it is not a report, it is a failure message. It is
    # reported in the log and the status, and the reader is not sent a message that
    # says nothing.
    analyzer = _Analyzer(failing=("AAPL", "RKLB"))
    application = _application(tmp_path, analyzer)
    sent = _deliveries(monkeypatch, application)

    outcome = application._run_brief()

    assert outcome.status is CycleStatus.EVALUATION_FAILED
    assert outcome.delivered is False
    assert sent == []


def test_an_asset_that_could_not_be_analysed_does_not_stop_the_brief(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # One asset must not cost the reader the whole report, and the brief names what
    # it could not look at rather than leaving the gap invisible.
    analyzer = _Analyzer(failing=("RKLB",))
    application = _application(tmp_path, analyzer)
    sent = _deliveries(monkeypatch, application)

    outcome = application._run_brief()

    # An asset that could not be analysed fails the run and does not fail the
    # delivery: the message went out, so nobody is owed another copy of it.
    assert outcome.status is CycleStatus.EVALUATION_FAILED
    assert outcome.delivered is True
    assert len(sent) == 1
    assert "未分析  RKLB" in sent[0][1]
    assert "分析 1 个标的" in sent[0][1]


def test_a_brief_that_reached_nobody_is_reported_as_not_delivered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The failure that actually happened three mornings running: the machine had no
    # network, so the send failed. What the runtime is told is not "the run failed"
    # but "nobody was told", which is what decides whether the day is still owed.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)

    def refuse(title: str, message: str) -> None:
        raise AISException("every notification channel failed: bark: refused")

    monkeypatch.setattr(application, "_deliver", refuse)

    first = application._run_brief()
    second = application._run_brief()

    assert first.status is CycleStatus.EVALUATION_FAILED
    assert first.delivered is False
    assert second.delivered is False


def test_the_expanded_report_of_every_asset_is_still_produced(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Nothing is dropped by being left out of the message: the full report of every
    # asset is written to the log, which is where a reader looks a fact up.
    analyzer = _Analyzer()
    application = _application(tmp_path, analyzer)
    _deliveries(monkeypatch, application)

    with caplog.at_level("INFO", logger="ais.application"):
        application._run_brief()

    for ticker in ("AAPL", "RKLB"):
        assert f"Asset: {ticker}" in caplog.text


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
