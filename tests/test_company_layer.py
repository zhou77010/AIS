"""Tests for the company layer: what the company itself reported, and what it did.

The requirement this file exists for is one sentence long: **evidence about the
company rather than about the market, and evidence that can change what the reader
looks at first.** So the tests below follow two chains end to end rather than testing
one end of each.

The first chain is the one every measurement travels: a source reports a number, the
pipeline files it as evidence under the category that measurement serves, and the
reading layer turns it into a band, a word and a score. The second is the one that
makes it matter: a reading that moved is a rating that changed, a rating that changed
is a reason a brief can lead with, and an asset that moved leads the message. Nothing
is judged here — no evaluator is asked anything new and no condition is added — which
is exactly what these tests have to prove rather than assume.

Two facts arrive in this round: the move price made before the session opened, and what
the last report did against what was expected of it. A third is recorded as absent and
is tested that way: guidance is not published by any source AIS reads, and what is
published in its place is somebody else's opinion about the company, so it is never
read and never stands in for guidance.
"""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from analysis.analysis_result import AnalysisResult
from analysis.brief import build_daily_brief
from analysis.insight.builder import build_insights, insight_for
from analysis.projection import is_a_change
from app.rating_tracker import RatingTracker
from config.logging_config import get_logger
from contracts.market_data_provider import (
    MARKET_EVIDENCE_ID,
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from data.yahoo_market_data_provider import YahooMarketDataProvider
from evaluation.reading.bands import band_for, scale_for, score_for
from evaluation.reading.category import read_category
from evaluation.reading.conditions import meets_condition
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation
from pipeline.evidence_builder import EvidenceBuilder
from utils.exceptions import DataError

_SYMBOL = "AAPL"
_FIRST = datetime(2026, 9, 17, 1, 0, tzinfo=UTC)
_LATER = datetime(2026, 9, 18, 1, 0, tzinfo=UTC)

# What the market measurements read in the fixtures, unless a test changes one.
_MARKET_VALUES: dict[MarketMetric, float] = {
    MarketMetric.MARKET_DIRECTION: 0.149,
    MarketMetric.EARNINGS_GROWTH: 0.20,
}


class _FakeTransport:
    """Stand-in transport that answers from a fixed table.

    An entry is matched against the requested URL by fragment, and an entry holding an
    exception is raised instead of returned. A request nobody answers is a failure of
    the test rather than of the provider, which is why it is raised as a data error the
    provider is contracted to survive.
    """

    def __init__(self, answers: dict[str, str | Exception]) -> None:
        self._answers = answers
        self.requested: list[str] = []

    def get(self, url: str) -> str:
        self.requested.append(url)
        for fragment, answer in self._answers.items():
            if fragment in url:
                if isinstance(answer, Exception):
                    raise answer
                return answer
        raise DataError(f"unexpected request to {url}")


class _Collector(logging.Handler):
    """Handler that keeps the messages a logger emitted, for one test."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _summary(**modules: dict[str, object]) -> str:
    """Return a quote summary payload built from the given modules."""
    return json.dumps({"quoteSummary": {"result": [modules]}})


def _quarter(
    when: str, *, actual: float | None, estimate: float | None, surprise: float | None
) -> dict[str, object]:
    """Return one reported quarter, nested the way the source nests it."""
    moment = datetime.fromisoformat(when).replace(tzinfo=UTC).timestamp()
    row: dict[str, object] = {"quarter": {"raw": moment}}
    if actual is not None:
        row["epsActual"] = {"raw": actual}
    if estimate is not None:
        row["epsEstimate"] = {"raw": estimate}
    if surprise is not None:
        row["surprisePercent"] = {"raw": surprise}
    return row


def _fetch(summary: str | Exception) -> MarketDataSnapshot:
    """Fetch a symbol through a transport answering with the given summary."""
    transport = _FakeTransport(
        {
            "fc.yahoo.com": DataError("HTTP 404 from fc.yahoo.com"),
            "getcrumb": "token-1",
            "quoteSummary": summary,
        }
    )
    return YahooMarketDataProvider(transport).fetch(_SYMBOL)


def _snapshot(values: dict[MarketMetric, float | None]) -> MarketDataSnapshot:
    """Return a snapshot holding the fixture measurements and one point per metric."""
    measured: dict[MarketMetric, float | None] = {**_MARKET_VALUES, **values}
    return MarketDataSnapshot(
        symbol=_SYMBOL,
        source="Test source",
        retrieved_at=_LATER,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=measured.get(metric),
                reason=f"Test source: {metric.value}",
            )
            for metric in MarketMetric
        ),
    )


def _result(
    ticker: str = _SYMBOL,
    *,
    ratings: tuple = (),
    values: dict[MarketMetric, float | None] | None = None,
) -> AnalysisResult:
    """Return a result carrying one snapshot, with nothing judged about it."""
    return AnalysisResult(
        asset=Asset(
            ticker=ticker,
            name=f"{ticker} Inc.",
            exchange="NASDAQ",
            currency="USD",
            profile=AssetProfile.UNKNOWN,
        ),
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
        market_data=_snapshot(values if values is not None else {}),
        ratings=ratings,
    )


# --------------------------------------------------------------------------
# What the source publishes, and what it does not
# --------------------------------------------------------------------------


def test_the_move_before_the_session_opened_is_read_from_the_source() -> None:
    snapshot = _fetch(
        _summary(
            price={
                "preMarketChangePercent": {"raw": -0.0238},
                "preMarketPrice": {"raw": 335.33},
                "regularMarketPreviousClose": {"raw": 343.5},
            }
        )
    )

    point = snapshot.point(MarketMetric.PREMARKET_GAP)

    assert point.value == pytest.approx(-0.0238)
    # Both legs are named, because the size of a move is not enough to check it.
    assert "335.33" in point.reason
    assert "343.5" in point.reason


def test_a_symbol_the_source_has_no_premarket_price_for_says_so() -> None:
    snapshot = _fetch(_summary(price={"regularMarketPrice": {"raw": 338.9}}))

    point = snapshot.point(MarketMetric.PREMARKET_GAP)

    assert point.value is None
    assert "premarket" in point.reason


def test_the_last_report_is_read_against_the_estimate_it_was_held_to() -> None:
    # The quarters arrive newest first, so reading the first entry would read the oldest
    # report on the list. What is wanted is the most recent one, whenever it arrived.
    snapshot = _fetch(
        _summary(
            earningsHistory={
                "history": [
                    _quarter("2026-06-27", actual=2.02, estimate=1.94, surprise=0.0412),
                    _quarter(
                        "2026-03-28", actual=2.01, estimate=2.03, surprise=-0.0099
                    ),
                    _quarter("2025-12-27", actual=2.84, estimate=2.67, surprise=0.0637),
                ]
            }
        )
    )

    point = snapshot.point(MarketMetric.EARNINGS_SURPRISE)

    assert point.value == pytest.approx(0.0412)
    assert "2026-06-27" in point.reason
    assert "2.02" in point.reason


def test_earlier_quarters_are_logged_and_not_read() -> None:
    # The history is worth keeping and is not worth judging on: one number fits a scale
    # and a run of them needs a trend rule nobody has approved.
    logger = get_logger("market_data")
    collector = _Collector()
    level = logger.level
    logger.addHandler(collector)
    logger.setLevel(logging.INFO)
    try:
        snapshot = _fetch(
            _summary(
                earningsHistory={
                    "history": [
                        _quarter(
                            "2026-06-27", actual=2.02, estimate=1.94, surprise=0.0412
                        ),
                        _quarter(
                            "2026-03-28", actual=2.01, estimate=2.03, surprise=-0.0099
                        ),
                    ]
                }
            )
        )
    finally:
        logger.removeHandler(collector)
        logger.setLevel(level)

    logged = "\n".join(collector.messages)

    assert "2026-03-28" in logged
    assert "2026-06-27" in logged
    assert snapshot.point(MarketMetric.EARNINGS_SURPRISE).value == pytest.approx(0.0412)


def test_a_quarter_without_a_surprise_is_recorded_as_absent() -> None:
    snapshot = _fetch(
        _summary(
            earningsHistory={
                "history": [
                    _quarter("2026-06-27", actual=2.02, estimate=1.94, surprise=None)
                ]
            }
        )
    )

    point = snapshot.point(MarketMetric.EARNINGS_SURPRISE)

    assert point.value is None
    assert "2026-06-27" in point.reason


def test_guidance_is_recorded_as_absent_and_says_why() -> None:
    # What the source does publish instead is what analysts expect, and it is a
    # different fact about a different author: reporting it under this name would state
    # that a company guided to a number it never mentioned.
    snapshot = _fetch(
        _summary(
            earningsTrend={"trend": [{"period": "+1q", "growth": {"raw": 0.0137}}]}
        )
    )

    point = snapshot.point(MarketMetric.EARNINGS_GUIDANCE)

    assert point.value is None
    assert "analyst" in point.reason
    assert "No value is invented" in point.reason


def test_guidance_is_still_absent_when_the_source_cannot_be_reached() -> None:
    # A connection failure is not why guidance is missing, so the reason must not become
    # one: the measurement is absent whatever the source does.
    snapshot = _fetch(DataError("connection refused"))

    point = snapshot.point(MarketMetric.EARNINGS_GUIDANCE)

    assert point.value is None
    assert "connection refused" not in point.reason


def test_the_source_that_could_not_be_reached_records_every_metric() -> None:
    snapshot = _fetch(DataError("connection refused"))

    assert {point.metric for point in snapshot.points} == set(MarketMetric)
    assert snapshot.available_points == ()


# --------------------------------------------------------------------------
# What the numbers mean, decided once in the reading layer
# --------------------------------------------------------------------------


def test_a_premarket_move_is_read_against_the_previous_close() -> None:
    assert band_for(MarketMetric.PREMARKET_GAP, 0.045).word == "盘前明显高开"
    assert band_for(MarketMetric.PREMARKET_GAP, -0.045).word == "盘前明显低开"
    assert band_for(MarketMetric.PREMARKET_GAP, 0.0).is_flat is True
    assert band_for(MarketMetric.PREMARKET_GAP, 0.008).word == "盘前基本持平"


def test_a_report_in_line_with_its_estimate_reads_as_no_surprise() -> None:
    assert band_for(MarketMetric.EARNINGS_SURPRISE, 0.14).word == "明显超预期"
    assert band_for(MarketMetric.EARNINGS_SURPRISE, -0.14).word == "明显不及预期"
    assert band_for(MarketMetric.EARNINGS_SURPRISE, 0.0).is_flat is True
    assert band_for(MarketMetric.EARNINGS_SURPRISE, -0.01).word == "符合预期"


def test_new_evidence_is_described_and_not_graded() -> None:
    # The Evidence Maturity Rule, as code. A scale that is not graded is read for its
    # word and carries no score, so the measurement reaches the sentence and cannot
    # reach a grade, a condition or the order of the brief. It is promoted only after
    # real runs have shown what it reads as, and that promotion is its own decision.
    for metric in (MarketMetric.PREMARKET_GAP, MarketMetric.EARNINGS_SURPRISE):
        scale = scale_for(metric)
        assert scale is not None
        assert scale.graded is False
        assert score_for(metric, 0.5) is None
        assert band_for(metric, 0.5).word


def test_both_facts_are_read_by_the_category_they_are_filed_under() -> None:
    snapshot = _snapshot(
        {
            MarketMetric.PREMARKET_GAP: -0.045,
            MarketMetric.EARNINGS_SURPRISE: 0.0412,
        }
    )

    market = read_category(snapshot, Category.MARKET)
    earnings = read_category(snapshot, Category.EARNINGS)

    assert MarketMetric.PREMARKET_GAP in {read.metric for read in market.reads}
    assert MarketMetric.EARNINGS_SURPRISE in {read.metric for read in earnings.reads}


def test_guidance_has_no_scale_because_no_number_ever_arrives() -> None:
    assert scale_for(MarketMetric.EARNINGS_GUIDANCE) is None


# --------------------------------------------------------------------------
# The same facts, in the stream every other measurement travels in
# --------------------------------------------------------------------------


def _evidence_item(result: AnalysisResult, metric: MarketMetric):
    """Return the evidence item the pipeline filed for one measurement."""
    identifier = MARKET_EVIDENCE_ID.format(ticker=result.asset.ticker, metric=metric)
    collection = EvidenceBuilder().build(result.asset, market_data=result.market_data)
    for item in collection.items:
        if item.id == identifier:
            return item
    raise AssertionError(f"no evidence item filed for {identifier}")


def test_the_premarket_move_enters_the_evidence_stream() -> None:
    result = _result(values={MarketMetric.PREMARKET_GAP: -0.045})

    item = _evidence_item(result, MarketMetric.PREMARKET_GAP)

    assert item.category is Category.MARKET
    assert "-0.045" in item.metadata["market_value"]


def test_the_surprise_enters_the_evidence_stream_under_earnings() -> None:
    result = _result(values={MarketMetric.EARNINGS_SURPRISE: 0.0412})

    item = _evidence_item(result, MarketMetric.EARNINGS_SURPRISE)

    assert item.category is Category.EARNINGS


# --------------------------------------------------------------------------
# And the chain that makes it matter: reading, rating, and the order of the brief
# --------------------------------------------------------------------------


def _market_reading(gap: float | None):
    """Return what the Market category reads, with the given premarket move."""
    values = {} if gap is None else {MarketMetric.PREMARKET_GAP: gap}
    return read_category(_snapshot(values), Category.MARKET)


def _earnings_reading(surprise: float | None):
    """Return what the Earnings category reads, with the given surprise."""
    values = {} if surprise is None else {MarketMetric.EARNINGS_SURPRISE: surprise}
    return read_category(_snapshot(values), Category.EARNINGS)


def test_the_new_measurements_are_read_but_change_no_grade() -> None:
    # Read, and worth nothing yet. Both halves matter: a reader is told what the
    # premarket did, and the category's grade is exactly what it was without the fact.
    # That is the state the Evidence Maturity Rule puts new evidence in.
    without = _market_reading(None)
    with_gap = _market_reading(-0.09)

    assert MarketMetric.PREMARKET_GAP in {read.metric for read in with_gap.reads}
    assert with_gap.word(MarketMetric.PREMARKET_GAP) == "盘前明显低开"
    assert with_gap.mean_score == without.mean_score
    assert with_gap.scored == without.scored


def test_a_surprise_is_read_but_changes_no_grade() -> None:
    without = _earnings_reading(None)
    with_surprise = _earnings_reading(0.30)

    assert with_surprise.word(MarketMetric.EARNINGS_SURPRISE) == "明显超预期"
    assert with_surprise.mean_score == without.mean_score


def test_a_gap_too_small_to_read_is_read_as_nothing_happened() -> None:
    # A move inside the flat band is not a fact about the company. The band is what
    # says so, and it says it once, for every consumer of the reading.
    reading = _market_reading(0.002)

    assert reading.scored == _market_reading(None).scored
    assert band_for(MarketMetric.PREMARKET_GAP, 0.002).is_flat is True


def test_new_evidence_does_not_reorder_the_brief() -> None:
    # The consequence of the rule, stated as a test so that nobody has to guess it: an
    # ungraded measurement leaves the grade where it was, a rating whose grade did not
    # move is not a change, and an asset that did not change does not lead.
    tracker = RatingTracker()
    before = tracker.update(
        symbol=_SYMBOL,
        category=Category.MARKET,
        grade=_market_reading(None).mean_score,
        score=4.0,
        reason="market reading",
        measurements={},
        moment=_FIRST,
    )
    after = tracker.update(
        symbol=_SYMBOL,
        category=Category.MARKET,
        grade=_market_reading(-0.09).mean_score,
        score=4.0,
        reason="market reading",
        measurements={},
        moment=_LATER,
    )

    assert before.grade == after.grade
    assert is_a_change(after) is False

    quiet = _result("CGDV", ratings=(before,))
    moved = _result(_SYMBOL, ratings=(after,))
    brief = build_daily_brief([quiet, moved], moment=_LATER)

    assert brief.entries[0].ticker == "CGDV"


# --------------------------------------------------------------------------
# And the step that makes it visible: the sentence the report is written from
# --------------------------------------------------------------------------


def _insight_lines(result: AnalysisResult, category: Category) -> list[str]:
    """Return the sentences the insight layer wrote for one category."""
    built = replace(result, insights=build_insights(result))
    insight = insight_for(built, category)
    return [] if insight is None else [line.text for line in insight.lines]


def test_the_premarket_move_is_said_in_the_report() -> None:
    lines = _insight_lines(
        _result(values={MarketMetric.PREMARKET_GAP: -0.0238}), Category.MARKET
    )

    assert any("盘前低开 2.4%" in line for line in lines), lines


def test_a_flat_premarket_move_is_said_without_a_number() -> None:
    # A number beside a band that means nothing happened invites a reader to read
    # something into it, so the sentence for a flat move carries none.
    lines = _insight_lines(
        _result(values={MarketMetric.PREMARKET_GAP: 0.002}), Category.MARKET
    )

    assert any(
        "盘前基本持平，开盘前没有新的价格信息。" in line for line in lines
    ), lines


def test_the_surprise_is_said_beside_what_guidance_would_have_added() -> None:
    # The sentence is where a reader finds out that guidance is missing, which is the
    # only honest thing to say about a fact no source AIS reads publishes.
    lines = _insight_lines(
        _result(values={MarketMetric.EARNINGS_SURPRISE: 0.0674}), Category.EARNINGS
    )

    assert any("超预期 6.7%" in line for line in lines), lines
    assert any("公司 Guidance 不可获得。" in line for line in lines), lines


def test_an_asset_with_no_surprise_is_told_nothing_about_one() -> None:
    lines = _insight_lines(_result(), Category.EARNINGS)

    assert not any("Guidance" in line for line in lines)
    assert not any("超预期" in line for line in lines)


def test_a_symbol_the_source_knows_no_premarket_price_for_is_told_nothing() -> None:
    lines = _insight_lines(_result(), Category.MARKET)

    assert not any("盘前" in line for line in lines), lines


def test_no_opportunity_condition_reads_either_new_category() -> None:
    # The conditions are unchanged: Market and Earnings were not among them before this
    # round and they are not among them now. A new fact changes what a category reads
    # as, and what that is worth is still decided by the conditions that already exist.
    snapshot = _snapshot(
        {
            MarketMetric.PREMARKET_GAP: -0.09,
            MarketMetric.EARNINGS_SURPRISE: -0.30,
        }
    )

    for category in (Category.MARKET, Category.EARNINGS):
        assert meets_condition(category, read_category(snapshot, category)) is None


def test_the_new_evidence_does_not_change_the_assets_own_reading_of_trend() -> None:
    # A premarket move is filed under Market, so it cannot move the Trend reading and
    # cannot deny the trend condition. Where a new fact is filed decides what it can
    # change, which is why the filing table is the only place that is decided.
    trend = read_category(
        _snapshot({MarketMetric.PREMARKET_GAP: -0.09}), Category.TREND
    )

    assert MarketMetric.PREMARKET_GAP not in {read.metric for read in trend.reads}
    assert Category.TREND not in MarketMetric.PREMARKET_GAP.categories
