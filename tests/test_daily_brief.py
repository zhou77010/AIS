"""Tests for the morning brief: what it selects, what it shows, and what it hides.

The brief is the one report AIS sends that is not about a single asset. Three
things have to hold for it to be a brief rather than a feed: it is one message
whatever the size of the watch universe, only a few assets are written into it
while every one of them is analysed, and the full report of each asset is still
produced and does not reach the phone.

The ordering is asserted here because it is a decision rather than an accident:
which reason outranks which is stated in one table, and a reader is entitled to
find it argued with in a test rather than in a comment.
"""

from __future__ import annotations

import unicodedata
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from analysis.analysis_result import AnalysisResult
from analysis.brief import (
    BRIEF_REASON_SLOTS,
    MAX_FOCUS,
    BriefEntry,
    BriefReason,
    DailyBrief,
    build_daily_brief,
)
from analysis.brief_report import BRIEF_LINE_BUDGET, render_daily_brief
from analysis.insight.builder import build_insights
from analysis.projection import LINE_WIDTH
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from evaluation.hpo.opportunity_assessor import OpportunityAssessor
from evaluation.reading.category import read_category
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.catalyst_event import CatalystEvent, CatalystEventKind
from models.category import CATEGORY_ORDER, Category
from models.category_rating import CategoryRating
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.opportunity_assessment import OpportunityCondition
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation
from models.watch_universe import WatchEntry, WatchSet, WatchUniverse

# 09:00 Beijing, which is the hour the brief is owed at.
_MORNING = datetime(2026, 9, 18, 9, 0, tzinfo=timezone(timedelta(hours=8)))

_VALUES: dict[str, float] = {
    "pe": 38.2,
    "peg": 2.67,
    "ev_ebitda": 28.9,
    "fcf_yield": 0.022,
    "beta": 1.08,
    "debt_to_equity": 78.4,
    "current_ratio": 1.0,
    "average_volume": 53_800_000.0,
    "float_shares": 14_600_000_000.0,
    "profit_margin": 0.276,
    "return_on_equity": 1.488,
    "free_cash_flow_margin": 0.231,
    "market_direction": 0.149,
    "trend_range_position": 0.717,
    "trend_direction": 0.246,
    "earnings_growth": 0.271,
    "expected_earnings_change": 0.100,
    "trend_ma20_gap": 0.03,
    "trend_ma60_gap": 0.02,
    "trend_ma120_gap": 0.01,
    "trend_macd": 0.004,
    "trend_rsi": 58.0,
    "trend_volume_ratio": 0.05,
    "risk_volatility": 0.231,
    "risk_drawdown": -0.138,
    "short_percent_of_float": 0.0096,
    "short_ratio": 2.97,
    "institutional_ownership": 0.663,
    "insider_ownership": 0.0165,
}

# How far away the nearest company event is in the fixtures.
_OWN_EVENT_DAYS = 12


def _width(line: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in {"W", "F"} else 1 for c in line)


def _asset(ticker: str) -> Asset:
    return Asset(
        ticker=ticker,
        name=f"{ticker} Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def _snapshot(ticker: str, **values: float) -> MarketDataSnapshot:
    return MarketDataSnapshot(
        symbol=ticker,
        source="Yahoo Finance",
        retrieved_at=_MORNING.astimezone(UTC) - timedelta(hours=5),
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=values.get(metric.value),
                reason="test reason",
            )
            for metric in MarketMetric
        ),
    )


def _event(
    kind: CatalystEventKind, days: int, *, symbol: str | None = None
) -> CatalystEvent:
    return CatalystEvent(
        kind=kind,
        occurs_on=_MORNING.date() + timedelta(days=days),
        source="Test source",
        confirmed=True,
        description="",
        symbol=symbol,
    )


def _macro_event(days: int = 40) -> CatalystEvent:
    """Return a central bank meeting, which is not any one asset's event."""
    return _event(CatalystEventKind.FOMC, days)


def _result(
    ticker: str,
    *,
    values: dict[str, float] | None = None,
    events: tuple[CatalystEvent, ...] = (),
    ratings: tuple[CategoryRating, ...] = (),
) -> AnalysisResult:
    """Return a result with its insights and opportunity built, as a run produces."""
    market_data = None if values is None else _snapshot(ticker, **values)
    result = AnalysisResult(
        asset=_asset(ticker),
        assessment=OverallAssessment(
            overall_score=11.99,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=tuple(
                CategoryScore(
                    category=category,
                    score=4.0,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=(f"{ticker}.market_data.{category.value}",),
                )
                for category in CATEGORY_ORDER
                if category is not Category.HPO
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder decision.",
            evidence_references=(f"{ticker}.market_data.pe",),
        ),
        market_data=market_data,
        events=events,
        ratings=ratings,
    )
    readings = {
        category_score.category: read_category(market_data, category_score.category)
        for category_score in result.assessment.category_scores
    }
    opportunity = OpportunityAssessor().assess(readings, _catalyst_days(result))
    result = replace(result, opportunity=opportunity)
    return replace(result, insights=build_insights(result))


def _catalyst_days(result: AnalysisResult) -> int | None:
    from analysis.category_grade import catalyst_days

    return catalyst_days(result)


def _moved_rating(category: Category = Category.TREND) -> CategoryRating:
    """Return a rating whose grade moved, which is a change in the asset."""
    return CategoryRating(
        category=category,
        grade=4,
        momentum=0.0,
        changed_at=_MORNING,
        changed=True,
        previous_grade=3,
        reason="reason",
        since=_MORNING,
    )


def _accumulating_rating(momentum: float = 0.081) -> CategoryRating:
    """Return a rating moving inside its grade, which is also a change."""
    return CategoryRating(
        category=Category.VALUATION,
        grade=3,
        momentum=momentum,
        changed_at=_MORNING - timedelta(days=30),
        changed=False,
        previous_grade=None,
        reason="reason",
        since=_MORNING - timedelta(days=12),
    )


def _first_rating() -> CategoryRating:
    """Return a rating read for the first time, which is not a change."""
    return CategoryRating(
        category=Category.TREND,
        grade=4,
        momentum=0.0,
        changed_at=_MORNING,
        changed=True,
        previous_grade=None,
        reason="reason",
        since=_MORNING,
    )


def _rich(ticker: str, **kwargs) -> AnalysisResult:
    """Return an asset everything is measured for, with a company event ahead."""
    events = kwargs.pop(
        "events",
        (_event(CatalystEventKind.PRODUCT_LAUNCH, _OWN_EVENT_DAYS, symbol=ticker),),
    )
    return _result(ticker, values=_VALUES, events=events, **kwargs)


def _thin(ticker: str) -> AnalysisResult:
    """Return an asset almost nothing is known about."""
    return _result(ticker, values={"market_direction": 0.149})


def _universe(*held: str) -> WatchUniverse:
    """Return a universe with the same assets, some of them held."""
    entries = tuple(
        WatchEntry(
            asset=_asset(ticker),
            sets=frozenset({WatchSet.PORTFOLIO}) if ticker in held else frozenset(),
        )
        for ticker in ("AAPL", "CGDV", "APP", "BABA", "HSBC", "MNST", "RKLB")
    )
    return WatchUniverse(entries=entries)


def _brief(results, **kwargs):
    return build_daily_brief(results, moment=_MORNING, **kwargs)


def _render(results, **kwargs) -> list[str]:
    return _render_brief(_brief(results, **kwargs))


def _with_grade(result: AnalysisResult, grade: int) -> AnalysisResult:
    """Return the same result with its opportunity grade set.

    The grade is how many named conditions hold, so a test that needs two assets to
    differ in standing sets the count rather than moving measurements until the
    bands happen to disagree.
    """
    assert result.opportunity is not None
    return replace(result, opportunity=replace(result.opportunity, grade=grade))


def _render_brief(brief: DailyBrief) -> list[str]:
    """Render one brief, for the cases a fixture cannot build through the builder."""
    return render_daily_brief(brief).splitlines()


def _with_risk(result: AnalysisResult, *, satisfied: bool) -> AnalysisResult:
    """Return the same result with its risk condition decided a particular way.

    The condition is a judgement AIS already made, so a test that needs the other
    answer changes the judgement rather than moving the measurements around until
    the bands happen to agree.
    """
    opportunity = result.opportunity
    assert opportunity is not None
    return replace(
        result,
        opportunity=replace(
            opportunity,
            conditions=tuple(
                (
                    replace(condition, satisfied=satisfied)
                    if condition.condition is OpportunityCondition.RISK
                    else condition
                )
                for condition in opportunity.conditions
            ),
        ),
    )


# --------------------------------------------------------------------------
# What the brief is
# --------------------------------------------------------------------------


def test_the_brief_is_one_message_whatever_the_universe_holds() -> None:
    # Seven assets are analysed; one message is produced. This is the whole point
    # of the model: the watch universe and the message are no longer the same size.
    results = [
        _rich(ticker)
        for ticker in ("AAPL", "CGDV", "APP", "BABA", "HSBC", "MNST", "RKLB")
    ]

    brief = _brief(results)

    assert len(brief.analysed) == 7
    assert len(brief.entries) == MAX_FOCUS
    assert isinstance(render_daily_brief(brief), str)


def test_the_brief_names_the_day_and_the_hour_it_was_built() -> None:
    lines = _render([_rich("AAPL")])

    assert lines[0].startswith("AIS 晨报")
    assert "2026-09-18" in lines[0]
    assert "09:00" in lines[0]
    assert "北京时间" in lines[0]


def test_the_brief_says_how_much_it_looked_at_and_how_much_it_shows() -> None:
    # Coverage and projection are two different numbers, and a reader who is told
    # only the second cannot tell a quiet universe from a narrow one.
    results = [_rich(ticker) for ticker in ("AAPL", "CGDV", "APP", "BABA", "HSBC")]

    lines = _render(results)

    assert any("分析 5 个标的" in line for line in lines), lines
    assert any(f"今日优先 {MAX_FOCUS} 个" in line for line in lines), lines


def test_the_assets_left_out_are_named_rather_than_dropped() -> None:
    results = [_rich(ticker) for ticker in ("AAPL", "CGDV", "APP", "BABA", "HSBC")]

    lines = _render(results)
    tail = next(line for line in lines if line.startswith("其余 2 个："))

    assert "BABA" in tail
    assert "HSBC" in tail


def test_an_asset_that_could_not_be_analysed_is_named_separately() -> None:
    # A failed run and a quiet asset are different things, and a reader who is not
    # told which is which cannot act on either.
    lines = _render([_rich("AAPL")], without_data=["BABA"])

    assert any(line.startswith("未分析  BABA") for line in lines), lines


# --------------------------------------------------------------------------
# What earns a line
# --------------------------------------------------------------------------


def test_only_the_strongest_assets_reach_the_message() -> None:
    results = [_rich(ticker) for ticker in ("AAPL", "CGDV", "APP", "BABA", "HSBC")]

    brief = _brief(results)

    assert [entry.ticker for entry in brief.entries] == ["AAPL", "CGDV", "APP"]


def test_what_moved_outranks_what_merely_reads_well() -> None:
    # The brief is about today. An asset whose grade moved today is the first
    # thing a reader should look at, whatever the others read like.
    quiet = [_rich(f"Q{index}") for index in range(3)]
    moved = _rich("RKLB", ratings=(_moved_rating(),))

    brief = _brief([*quiet, moved])

    assert brief.entries[0].ticker == "RKLB"
    assert brief.entries[0].reason is BriefReason.MOVED


def test_a_movement_inside_a_grade_is_a_change_too() -> None:
    # The per-asset report writes a change line for it, so the brief has to count
    # it as one: two reports disagreeing about the same reading is worse than
    # either of them being wrong.
    brief = _brief([_rich("AAPL", ratings=(_accumulating_rating(),))])

    assert brief.entries[0].reason is BriefReason.MOVED


def test_a_first_rating_is_not_a_change() -> None:
    # Being rated for the first time is a fact about the tracker, not about the
    # asset, and the per-asset report does not report it either.
    brief = _brief([_rich("AAPL", ratings=(_first_rating(),))])

    assert brief.entries[0].reason is not BriefReason.MOVED


def test_a_movement_too_small_to_read_is_not_a_change() -> None:
    brief = _brief([_rich("AAPL", ratings=(_accumulating_rating(momentum=0.001),))])

    assert brief.entries[0].reason is not BriefReason.MOVED


def test_the_reason_is_recorded_so_the_line_can_state_it() -> None:
    lines = _render([_rich("AAPL", ratings=(_moved_rating(),))])

    assert any(line.startswith("AAPL") and "变化" in line for line in lines), lines


def test_an_asset_nothing_moved_for_carries_no_reason() -> None:
    # Two of the reasons say only that the asset was read at all, which a reader
    # already assumes of everything in their own brief. A tag that says nothing is
    # noise on a line that has one job.
    result = _rich("AAPL")

    for reason in (BriefReason.OPPORTUNITY, BriefReason.WATCHED):
        lines = _render_brief(
            DailyBrief(
                moment=_MORNING,
                entries=(BriefEntry(result=result, reason=reason),),
                analysed=(result,),
            )
        )
        heading = next(line for line in lines if line.startswith("AAPL"))

        assert "·" not in heading, heading


def test_the_reasons_that_state_something_do_carry_a_tag() -> None:
    result = _rich("AAPL")

    for reason, label in (
        (BriefReason.MOVED, "变化"),
        (BriefReason.RISK, "风险"),
        (BriefReason.PORTFOLIO, "持仓"),
        (BriefReason.PORTFOLIO_CHANGE, "持仓变化"),
    ):
        lines = _render_brief(
            DailyBrief(
                moment=_MORNING,
                entries=(BriefEntry(result=result, reason=reason),),
                analysed=(result,),
            )
        )
        heading = next(line for line in lines if line.startswith("AAPL"))

        assert label in heading, heading


def test_a_held_asset_outranks_a_watched_one() -> None:
    # The portfolio comes first because a position is what a reader is exposed to.
    quiet = [_rich(ticker) for ticker in ("AAPL", "CGDV", "APP")]
    held = _rich("BABA")

    brief = _brief([*quiet, held], universe=_universe("BABA"))

    assert brief.entries[0].ticker == "BABA"
    assert brief.entries[0].reason is BriefReason.PORTFOLIO


def test_a_held_asset_that_moved_outranks_a_held_asset_that_did_not() -> None:
    held_quiet = _rich("BABA")
    held_moved = _rich("HSBC", ratings=(_moved_rating(),))

    brief = _brief([held_quiet, held_moved], universe=_universe("BABA", "HSBC"))

    assert brief.entries[0].ticker == "HSBC"
    assert brief.entries[0].reason is BriefReason.PORTFOLIO_CHANGE


def test_a_judged_risk_and_a_judged_opportunity_compete_in_one_slot() -> None:
    # They answer the same question — where does this asset stand — so what
    # separates two assets inside that slot is how many conditions hold, and not
    # which of the two reasons applied. Ranking every warning above every case
    # filled the message with the same warning three times.
    slots = [index for index, reasons in enumerate(BRIEF_REASON_SLOTS) if reasons]

    assert slots == sorted(slots)
    for index, reasons in enumerate(BRIEF_REASON_SLOTS):
        if BriefReason.RISK in reasons:
            assert BriefReason.OPPORTUNITY in reasons
            assert index == slots.index(index)


def test_every_reason_competes_in_exactly_one_slot() -> None:
    placed = [reason for slot in BRIEF_REASON_SLOTS for reason in slot]

    assert sorted(placed, key=str) == sorted(BriefReason, key=str)


def test_the_strongest_standing_leads_the_slot() -> None:
    # Six assets share one warning and one asset has a case, so the brief leads with
    # the asset whose own judgement reads best rather than with the first warning in
    # watchlist order.
    warned = [
        _with_grade(_with_risk(_rich(ticker), satisfied=False), 1)
        for ticker in ("AAPL", "CGDV", "APP")
    ]
    best = _with_grade(_with_risk(_rich("HSBC"), satisfied=True), 4)

    brief = _brief([*warned, best])

    assert brief.entries[0].ticker == "HSBC"
    assert brief.entries[0].reason is BriefReason.OPPORTUNITY
    assert brief.entries[1].reason is BriefReason.RISK


def test_the_order_is_stated_once_and_read_from_one_table() -> None:
    assert BRIEF_REASON_SLOTS[0] == (BriefReason.PORTFOLIO_CHANGE,)
    assert BRIEF_REASON_SLOTS[-1] == (BriefReason.WATCHED,)


def test_two_assets_nothing_distinguishes_keep_the_universe_order() -> None:
    # Stability is what makes a brief comparable from one day to the next: the
    # same assets in the same order must not be shuffled by a dict or a set.
    results = [_rich(ticker) for ticker in ("AAPL", "CGDV", "APP")]

    first = [entry.ticker for entry in _brief(results).entries]
    second = [entry.ticker for entry in _brief(list(results)).entries]

    assert first == second == ["AAPL", "CGDV", "APP"]


# --------------------------------------------------------------------------
# Why the first asset is first
# --------------------------------------------------------------------------


def test_the_asset_that_leads_on_conditions_says_so() -> None:
    # The order is decided by one table, and this only puts that decision into words
    # a reader can check against what is already on the screen: the leader holds more
    # opportunity conditions than the others shown, which the stars beside each
    # heading count.
    warned = [
        _with_grade(_with_risk(_rich(ticker), satisfied=False), 1)
        for ticker in ("AAPL", "CGDV", "APP")
    ]
    best = _with_grade(_with_risk(_rich("HSBC"), satisfied=True), 4)

    lines = _render([*warned, best])
    start = next(index for index, line in enumerate(lines) if line.startswith("HSBC"))

    assert lines[start + 1] == "今日优先  机会条件最多", lines


def test_an_asset_that_leads_because_it_moved_says_so() -> None:
    # Where the assets hold the same number of conditions, the order is decided by
    # what moved, and that is what the line says instead.
    lines = _render(
        [
            _with_grade(_rich("AAPL", ratings=(_moved_rating(),)), 1),
            *_alike("CGDV", "APP"),
        ]
    )
    start = next(index for index, line in enumerate(lines) if line.startswith("AAPL"))

    assert lines[start + 1] == "今日优先  今日有变化", lines


def test_the_order_between_alike_assets_claims_no_reason() -> None:
    # Nothing separates them, so nothing is claimed. A line here would invent a reason
    # for an order that carries none.
    lines = _render(_alike("AAPL", "CGDV", "APP"))

    assert not any(line.startswith("今日优先") for line in lines), lines


def test_only_the_asset_that_leads_is_told_why_it_leads() -> None:
    lines = _render([_with_grade(_rich("HSBC"), 4), _with_grade(_rich("AAPL"), 1)])

    assert sum(line.startswith("今日优先") for line in lines) == 1, lines


# --------------------------------------------------------------------------
# The same conclusion is said once
# --------------------------------------------------------------------------


def _alike(*tickers: str, grade: int = 1) -> list[AnalysisResult]:
    """Return assets that reached the same conclusion, each with an event ahead."""
    return [_with_grade(_rich(ticker), grade) for ticker in tickers]


def test_a_conclusion_several_assets_share_is_written_once() -> None:
    # Three assets reading alike are one thing to say. Writing it three times costs
    # the reader the lines that could have differed, and tells them nothing the first
    # one did not.
    lines = _render(_alike("AAPL", "CGDV", "APP"))

    assert sum("目前不是优先配置的时点" in line for line in lines) == 1, lines
    assert any(line.startswith("共同结论") for line in lines), lines


def test_the_assets_a_shared_conclusion_covers_are_named_under_it() -> None:
    report = render_daily_brief(_brief(_alike("AAPL", "CGDV", "APP")))
    shared = report.index("共同结论")

    assert report.index("AAPL") > shared
    assert report.index("AAPL") < report.index("CGDV") < report.index("APP")


def test_an_asset_with_its_own_conclusion_keeps_its_own_line() -> None:
    results = [_with_grade(_rich("HSBC"), 4), *_alike("AAPL", "CGDV")]

    lines = _render(results)
    own = next(index for index, line in enumerate(lines) if line.startswith("HSBC"))
    shared = next(
        index for index, line in enumerate(lines) if line.startswith("共同结论")
    )

    assert "值得优先配置" in "".join(lines[own:shared]), lines
    assert sum("目前不是优先配置的时点" in line for line in lines) == 1, lines
    assert lines[shared] == "共同结论（AAPL、CGDV）", lines


def test_assets_that_reached_different_conclusions_are_not_grouped() -> None:
    lines = _render([_with_grade(_rich("AAPL"), 4), _with_grade(_rich("CGDV"), 1)])

    assert not any(line.startswith("共同结论") for line in lines), lines


def test_a_shared_conclusion_keeps_each_assets_own_standing_and_reason() -> None:
    # What is shared is the conclusion. What is not shared is where each asset
    # stands, and why it is in the brief at all.
    warned = _with_grade(_with_risk(_rich("AAPL"), satisfied=False), 1)
    calm = _with_grade(_with_risk(_rich("CGDV"), satisfied=True), 1)
    moved = _with_grade(_rich("APP", ratings=(_moved_rating(),)), 1)

    lines = _render([warned, calm, moved])

    assert sum("目前不是优先配置的时点" in line for line in lines) == 1, lines
    assert any(line.startswith("AAPL") and "风险" in line for line in lines), lines
    assert any(line.startswith("APP") and "变化" in line for line in lines), lines
    assert any(line.startswith("CGDV") and "·" not in line for line in lines), lines


def test_each_asset_keeps_its_own_event_under_a_shared_conclusion() -> None:
    results = [
        _with_grade(
            _rich(
                "AAPL", events=(_event(CatalystEventKind.EARNINGS, 5, symbol="AAPL"),)
            ),
            1,
        ),
        _with_grade(
            _rich(
                "CGDV",
                events=(_event(CatalystEventKind.INVESTOR_DAY, 9, symbol="CGDV"),),
            ),
            1,
        ),
    ]

    lines = _render(results)

    assert sum(line.strip().startswith("关注") for line in lines) == 2, lines
    assert any("5 天后" in line for line in lines), lines
    assert any("9 天后" in line for line in lines), lines


def test_a_shared_conclusion_that_does_not_fit_is_broken_not_overflowed() -> None:
    # The roster goes on the line above the sentence rather than in front of it, so
    # the sentence starts at full width and is broken only by its own length. Nothing
    # here reads aloud as one sentence, so an overflow would only be visible as a line
    # running off the screen.
    lines = _render([_thin("AAPL"), _thin("CGDV")])
    label = next(
        index for index, line in enumerate(lines) if line.startswith("共同结论")
    )

    assert "尚无可用的类别判断" in lines[label + 1], lines
    for line in lines:
        assert _width(line) <= LINE_WIDTH, line


def test_the_brief_groups_the_assets_that_share_a_conclusion() -> None:
    # The groups come in the order their assets reached the brief, so the asset that
    # stands best leads whether or not it shares its conclusion with anybody.
    brief = _brief(
        [
            _with_grade(_rich("AAPL"), 1),
            _with_grade(_rich("CGDV"), 1),
            _with_grade(_rich("APP"), 4),
        ]
    )

    assert [[entry.ticker for entry in group.entries] for group in brief.groups] == [
        ["APP"],
        ["AAPL", "CGDV"],
    ]
    assert brief.groups[0].is_shared is False
    assert brief.groups[1].is_shared is True
    assert brief.groups[1].concluded_grade == 1


def test_a_group_sits_where_its_most_important_member_sat() -> None:
    # Two assets sharing a conclusion are written together, at the place the more
    # important of them reached. An asset whose own standing is lower can therefore
    # appear above one that outranks it: saying the conclusion once is worth more than
    # a one-place gap, and every heading still states its own standing.
    moved = _with_grade(_rich("AAPL", ratings=(_moved_rating(),)), 1)
    best = _with_grade(_rich("HSBC"), 4)
    alike = _with_grade(_rich("CGDV"), 1)

    brief = _brief([moved, best, alike])
    report = render_daily_brief(brief)

    assert [entry.ticker for entry in brief.entries] == ["AAPL", "HSBC", "CGDV"]
    assert [[entry.ticker for entry in group.entries] for group in brief.groups] == [
        ["AAPL", "CGDV"],
        ["HSBC"],
    ]
    assert report.index("AAPL") < report.index("CGDV") < report.index("HSBC")


# --------------------------------------------------------------------------
# What bears on everything
# --------------------------------------------------------------------------


def test_a_shared_event_is_reported_once_rather_than_once_per_asset() -> None:
    # The central bank meets on the same date whichever symbol is asked about, so
    # seven calendars carry one meeting.
    results = [
        _rich(ticker, events=(_macro_event(),))
        for ticker in ("AAPL", "CGDV", "APP", "BABA", "HSBC", "MNST", "RKLB")
    ]

    brief = _brief(results)

    assert len(brief.external_events) == 1


def test_the_shared_events_that_matter_most_are_shown_first() -> None:
    # Importance before distance, which is the rule the per-asset report already
    # uses for the events it shows: a central bank meeting in twenty days outranks
    # a currency event in three.
    results = [
        _rich(
            "AAPL",
            events=(
                _event(CatalystEventKind.CURRENCY, 3),
                _event(CatalystEventKind.INFLATION, 20),
            ),
        )
    ]

    brief = _brief(results)

    assert [event.kind for event in brief.external_events] == [
        CatalystEventKind.INFLATION,
        CatalystEventKind.CURRENCY,
    ]


def test_a_shared_event_is_not_repeated_beside_each_asset() -> None:
    # The macro line states it once. Repeating it under an asset would report the
    # same meeting as though it were that asset's own story.
    lines = _render([_rich("AAPL", events=(_macro_event(),))])

    assert sum("美联储议息" in line for line in lines) == 1, lines


def test_an_asset_shows_the_event_that_is_its_own() -> None:
    lines = _render([_rich("RKLB")])

    assert any("关注" in line and "产品发布" in line for line in lines), lines


def test_an_empty_external_calendar_is_an_answer_rather_than_a_gap() -> None:
    lines = _render([_rich("AAPL", events=())])

    assert any(line.startswith("外部事件  暂无") for line in lines), lines


# --------------------------------------------------------------------------
# The budgets
# --------------------------------------------------------------------------


_SHAPES = {
    "rich": lambda: [_rich(ticker) for ticker in ("AAPL", "CGDV", "APP", "BABA")],
    "moved": lambda: [
        _rich("AAPL", ratings=(_moved_rating(),)),
        _rich("CGDV", ratings=(_accumulating_rating(),)),
        _rich("APP"),
    ],
    "macro": lambda: [
        _rich(ticker, events=(_macro_event(),))
        for ticker in ("AAPL", "CGDV", "APP", "BABA")
    ],
    "thin": lambda: [_thin(ticker) for ticker in ("AAPL", "CGDV", "APP")],
    "one": lambda: [_rich("AAPL")],
}


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_no_line_is_wider_than_the_projection_width(shape: str) -> None:
    for line in _render(_SHAPES[shape]()):
        assert _width(line) <= LINE_WIDTH, f"{_width(line)} columns: {line}"


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_the_brief_stays_inside_its_line_budget(shape: str) -> None:
    lines = _render(_SHAPES[shape]())

    assert len(lines) <= BRIEF_LINE_BUDGET, "\n".join(lines)


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_the_brief_is_a_shorter_read_than_the_report_it_summarises(shape: str) -> None:
    # A brief as long as the report it summarises has not summarised anything.
    assert BRIEF_LINE_BUDGET < 32


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_nothing_is_written_past_the_last_line(shape: str) -> None:
    report = render_daily_brief(_brief(_SHAPES[shape]()))

    assert not report.endswith("\n")
    assert "\n\n" not in report


# --------------------------------------------------------------------------
# What the brief leaves out, and where it went
# --------------------------------------------------------------------------


def test_the_full_report_of_an_asset_is_not_in_the_message() -> None:
    # The expanded report is still produced for every asset; it goes to the log,
    # and it does not interrupt the reader.
    report = render_daily_brief(_brief([_rich("AAPL")]))

    assert "AIS analysis report" not in report
    assert "Category scores" not in report
    assert "Evidence references" not in report
    assert "Insights:" not in report
    assert "Overall score" not in report


def test_the_opportunity_conditions_are_left_to_the_full_report() -> None:
    report = render_daily_brief(_brief([_rich("AAPL")]))

    assert "估值具备吸引力" not in report
    assert "趋势向好" not in report


def test_each_asset_is_given_a_name_a_standing_and_a_conclusion() -> None:
    lines = _render([_rich("AAPL", ratings=(_moved_rating(),))])
    start = next(index for index, line in enumerate(lines) if line.startswith("AAPL"))
    block = "".join(lines[start:])

    assert "★" in lines[start]
    assert "观望" in lines[start]
    assert "当前机会一般，优先级不高。" in block, lines


def test_the_brief_names_the_source_and_the_state_of_the_data() -> None:
    report = render_daily_brief(_brief([_rich("AAPL")]))

    assert "Yahoo Finance" in report
    assert "实时" in report
    assert "不构成投资建议" in report


def test_a_degraded_asset_is_named_rather_than_averaged_away() -> None:
    # The brief is written from seven runs and shows three. A run that was not
    # live has to be visible even when the asset it belongs to was not shown.
    results = [_rich("AAPL"), _result("BABA")]

    lines = _render(results)

    assert any(line.startswith("无实时数据  BABA") for line in lines), lines


def test_a_universe_that_could_not_be_read_at_all_says_so() -> None:
    # A run with no market data source behind it is described as one, in the same
    # words the per-asset report uses for the same state.
    lines = _render([_result("AAPL")])

    assert any("占位数据" in line for line in lines), lines
    assert any(line.startswith("无实时数据  AAPL") for line in lines), lines
