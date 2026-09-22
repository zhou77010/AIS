"""Tests for the pre-market brief, and for the independence of the two reports.

Two requirements are exercised here, and they are different in kind.

The first is that the pre-market report is a report of its own: sent at its own hour,
over
its own evidence, stating which layers of that evidence answered, and saying the one
thing
the morning report cannot say — what price is doing before the open.

The second is that the two reports are independent: separate names, separate state,
separate attempts, separate delivery. That is tested by driving both schedules through
the
same state file and showing that one of them being owed, delivered or abandoned leaves
the
other exactly where it was.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from analysis.brief import build_daily_brief
from analysis.premarket_report import PREMARKET_LINE_BUDGET, render_premarket_brief
from analysis.projection import display_width
from app.application import MORNING_BRIEF_MOMENT, PREMARKET_BRIEF_MOMENT
from app.morning_brief import MAX_BRIEF_ATTEMPTS, MorningBrief
from app.premarket_brief import NAME as PREMARKET_NAME
from app.premarket_brief import PreMarketBrief
from app.runtime_state import (
    BaselineName,
    ReportDelivery,
    ReportName,
    ReportRecord,
    RuntimeState,
)
from app.scheduled_report import ReportOutcome
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from models.asset import Asset
from models.asset_profile import AssetProfile
from utils.constants import CycleStatus

_SYMBOL = "AAPL"
_NOON = datetime(2026, 9, 22, 4, 0, tzinfo=UTC)


def _snapshot(**values: float | None) -> MarketDataSnapshot:
    """Return a snapshot holding the given measurements and one point per metric."""
    return MarketDataSnapshot(
        symbol=_SYMBOL,
        source="Test source",
        retrieved_at=_NOON,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=values.get(metric.value),
                reason=f"Test source: {metric.value}",
            )
            for metric in MarketMetric
        ),
    )


def _asset(ticker: str = _SYMBOL) -> Asset:
    return Asset(
        ticker=ticker,
        name=f"{ticker} Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.UNKNOWN,
    )


def _result(ticker: str = _SYMBOL, *, gap: float | None = None):
    """Return a result carrying one snapshot, with nothing judged about it."""
    from analysis.analysis_result import AnalysisResult
    from models.decision_state import DecisionState
    from models.overall_assessment import OverallAssessment
    from models.recommendation import Recommendation

    return AnalysisResult(
        asset=_asset(ticker),
        assessment=OverallAssessment(
            overall_score=0.0,
            confidence=0.0,
            grade="PLACEHOLDER",
            category_scores=(),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=0.0,
            investment_thesis="Placeholder decision.",
            evidence_references=(),
        ),
        market_data=_snapshot(premarket_gap=gap),
    )


def _render(results, *, moment=datetime(2026, 9, 22, 13, 0, tzinfo=UTC)):
    brief = build_daily_brief(results, moment=moment)
    return render_premarket_brief(brief).splitlines()


def _outcome(*, delivered: bool) -> ReportOutcome:
    return ReportOutcome(
        status=(
            CycleStatus.NOTIFICATION_SENT
            if delivered
            else CycleStatus.EVALUATION_FAILED
        ),
        delivered=delivered,
    )


# --------------------------------------------------------------------------
# What the pre-market report says
# --------------------------------------------------------------------------


def test_it_is_named_as_the_pre_market_report_and_dated() -> None:
    lines = _render([_result(gap=-0.0238)])

    assert lines[0].startswith("AIS 盘前简报")
    assert "2026-09-22" in lines[0]


def test_it_states_which_layers_of_evidence_answered() -> None:
    # Three layers arrive at different speeds, and the report exists before all three
    # do.
    # Saying which of them answered is what keeps a thin message from reading like a
    # quiet
    # market.
    lines = _render([_result(gap=-0.0238), _result("CGDV", gap=None)])
    layer = next(line for line in lines if line.startswith("层次"))

    assert "环境 不可得" in layer
    assert "公司 1/2" in layer
    assert "新闻 未接" in layer


def test_it_says_what_price_did_before_the_open() -> None:
    lines = _render([_result(gap=-0.0238)])

    assert any("盘前低开 2.4%" in line for line in lines), lines


def test_a_move_that_means_nothing_gets_no_number() -> None:
    # The reading layer decided the move reads as nothing happened, and a number beside
    # that word invites a reader to read something into it.
    lines = _render([_result(gap=0.002)])

    assert any("盘前基本持平" in line for line in lines), lines
    assert not any("盘前基本持平 0.2%" in line for line in lines), lines


def test_an_asset_the_source_answered_nothing_for_gets_no_line() -> None:
    lines = _render([_result("CGDV", gap=None)])

    assert not any("盘前" in line and "CGDV" in line for line in lines), lines


def test_the_message_stays_inside_its_budget_and_width() -> None:
    results = [_result(ticker, gap=-0.02) for ticker in ("AAPL", "CGDV", "APP")]

    lines = _render(results)

    assert len(lines) <= PREMARKET_LINE_BUDGET, lines
    for line in lines:
        assert display_width(line) <= 42, line


# --------------------------------------------------------------------------
# The two reports are independent
# --------------------------------------------------------------------------


def _briefs(tmp_path: Path, clock=None):
    """Return both reports sharing one state file, as the runtime builds them."""
    state = RuntimeState(path=tmp_path / "runtime.json")
    morning = MorningBrief(
        MORNING_BRIEF_MOMENT, state, lambda: _outcome(delivered=True), clock=clock
    )
    premarket = PreMarketBrief(
        PREMARKET_BRIEF_MOMENT, state, lambda: _outcome(delivered=True), clock=clock
    )
    return state, morning, premarket


def test_the_two_reports_have_their_own_names_and_their_own_state() -> None:
    state = RuntimeState(path=Path("unused.json"))
    morning = MorningBrief(
        MORNING_BRIEF_MOMENT, state, lambda: _outcome(delivered=True)
    )
    premarket = PreMarketBrief(
        PREMARKET_BRIEF_MOMENT, state, lambda: _outcome(delivered=True)
    )

    assert premarket.name == PREMARKET_NAME == "premarket-brief"
    assert morning.name != premarket.name
    assert morning.key is ReportName.MORNING_BRIEF
    assert premarket.key is ReportName.PREMARKET_BRIEF


def test_one_report_delivering_says_nothing_about_the_other(tmp_path: Path) -> None:
    # This is the failure the independence exists to prevent: a morning brief delivered
    # must not mark the pre-market report as sent, or the reader is skipped at 21:00.
    state, morning, premarket = _briefs(tmp_path)

    morning.work()

    assert state.report(ReportName.MORNING_BRIEF).delivery is ReportDelivery.SENT
    assert state.report(ReportName.PREMARKET_BRIEF) is None


def test_each_report_counts_its_own_attempts(tmp_path: Path) -> None:
    state = RuntimeState(path=tmp_path / "runtime.json")
    morning = MorningBrief(
        MORNING_BRIEF_MOMENT, state, lambda: _outcome(delivered=False)
    )
    premarket = PreMarketBrief(
        PREMARKET_BRIEF_MOMENT, state, lambda: _outcome(delivered=False)
    )

    morning.work()
    morning.work()
    premarket.work()

    assert state.report(ReportName.MORNING_BRIEF).attempts == 2
    assert state.report(ReportName.PREMARKET_BRIEF).attempts == 1


def test_an_abandoned_report_leaves_the_other_still_owed(tmp_path: Path) -> None:
    state = RuntimeState(path=tmp_path / "runtime.json")
    morning = MorningBrief(
        MORNING_BRIEF_MOMENT, state, lambda: _outcome(delivered=False)
    )
    premarket = PreMarketBrief(
        PREMARKET_BRIEF_MOMENT, state, lambda: _outcome(delivered=False)
    )

    for _ in range(MAX_BRIEF_ATTEMPTS):
        morning.work()

    assert state.report(ReportName.MORNING_BRIEF).delivery is ReportDelivery.ABANDONED
    assert state.report(ReportName.PREMARKET_BRIEF) is None
    # And the pre-market report is still owed today, at its own hour.
    assert premarket.next_due(_NOON) == PREMARKET_BRIEF_MOMENT.at(_NOON)


def test_the_two_reports_are_owed_at_their_own_hours() -> None:
    morning_due = MORNING_BRIEF_MOMENT.at(_NOON)
    premarket_due = PREMARKET_BRIEF_MOMENT.at(_NOON)

    assert morning_due.hour == 9
    assert premarket_due.hour == 21
    assert premarket_due - morning_due == timedelta(hours=12)


def test_a_restored_baseline_is_not_a_first_reading(tmp_path: Path) -> None:
    # The observation baseline has to survive a restart: a process that came back
    # and read
    # every comparison as new would break the statistics it is being observed for.
    path = tmp_path / "runtime.json"
    record = ReportRecord(
        day=_NOON.date(),
        delivery=ReportDelivery.SENT,
        attempts=1,
        attempted_at=_NOON,
    )
    RuntimeState(path=path).record_report(ReportName.PREMARKET_BRIEF, record)

    state = RuntimeState(path=path)

    assert state.report(ReportName.PREMARKET_BRIEF).delivery is ReportDelivery.SENT
    assert state.report(ReportName.MORNING_BRIEF) is None


def test_a_baseline_is_kept_apart_from_a_report_record(tmp_path: Path) -> None:
    # A baseline says where something stood; a record says what has been delivered. They
    # are written to one file and they never read each other's.
    state = RuntimeState(path=tmp_path / "runtime.json")

    state.record_baseline(BaselineName.RATINGS, {"AAPL|market": {"grade": 4}})
    state.record_report(ReportName.MORNING_BRIEF, ReportRecord(day=_NOON.date()))

    assert state.baseline(BaselineName.RATINGS) == {"AAPL|market": {"grade": 4}}
    assert state.baseline(BaselineName.RECOMMENDATIONS) == {}
    assert state.report(ReportName.MORNING_BRIEF).day == _NOON.date()


def test_writing_one_baseline_leaves_the_other_and_the_reports_alone(
    tmp_path: Path,
) -> None:
    state = RuntimeState(path=tmp_path / "runtime.json")
    state.record_baseline(BaselineName.RATINGS, {"a": 1})
    state.record_report(ReportName.PREMARKET_BRIEF, ReportRecord(day=_NOON.date()))

    state.record_baseline(BaselineName.RECOMMENDATIONS, {"AAPL": {"confidence": 1.0}})

    assert state.baseline(BaselineName.RATINGS) == {"a": 1}
    assert state.report(ReportName.PREMARKET_BRIEF).day == _NOON.date()


def test_an_unreadable_baseline_is_treated_as_absent(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    path.write_text('{"baselines": "not a mapping"}', encoding="utf-8")

    assert RuntimeState(path=path).baseline(BaselineName.RATINGS) == {}
