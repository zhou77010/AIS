"""Tests for the catalyst event layer.

Catalyst is not a calendar reminder. It answers what could change the investment
case, grouped by whether the event bears on the company, on its industry or on
the conditions everything is valued under, and each event carries why that sort
of event matters. These tests describe the layer, the sources that fill it, and
the rule that reads it, including the property that matters most: how many events
there are never changes the reading.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from contracts.catalyst_event_provider import (
    CONFIRMED_METADATA_KEY,
    DATE_METADATA_KEY,
    KIND_METADATA_KEY,
    SCOPE_METADATA_KEY,
)
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from data.curated_catalyst_calendar import CuratedCatalystEventProvider
from data.federal_reserve_event_provider import FederalReserveEventProvider
from data.yahoo_market_data_provider import _events_from
from evaluation.catalyst.catalyst_evaluator import CatalystEvaluator
from evaluation.catalyst.event_reading import read_events
from evaluation.catalyst.upcoming_rule import RULE
from evaluation.evaluation_rule import EvaluationRule
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.catalyst_event import (
    CATALYST_EVENT_SCOPE,
    CatalystEvent,
    CatalystEventKind,
    CatalystEventScope,
)
from models.category import Category
from models.category_score import CategoryScore
from pipeline.evidence_builder import EvidenceBuilder
from utils.exceptions import DataError

_RETRIEVED_AT = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)


def _asset() -> Asset:
    return Asset(
        ticker="RKLB",
        name="Rocket Lab",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.HIGH_GROWTH,
    )


def _event(
    kind: CatalystEventKind,
    days: int,
    *,
    description: str = "事件",
    confirmed: bool = True,
    symbol: str | None = "RKLB",
    source: str = "Test source",
) -> CatalystEvent:
    return CatalystEvent(
        kind=kind,
        occurs_on=date.today() + timedelta(days=days),
        source=source,
        confirmed=confirmed,
        description=description,
        symbol=symbol,
    )


def _evidence(*events: CatalystEvent) -> EvidenceCollection:
    """Return evidence carrying the given events and no market metrics."""
    return EvidenceBuilder().build(_asset(), None, events)


def _event_item(evidence: EvidenceCollection):
    """Return the evidence item carrying one catalyst event."""
    return next(item for item in evidence.items if DATE_METADATA_KEY in item.metadata)


# --------------------------------------------------------------------------
# The event itself
# --------------------------------------------------------------------------


def test_ais_classifies_every_kind_into_a_layer() -> None:
    # A provider states the kind and never the layer, so the mapping has to be
    # total: an event nothing can classify would be an event nothing can report.
    assert set(CATALYST_EVENT_SCOPE) == set(CatalystEventKind)


def test_a_company_event_bears_on_the_company() -> None:
    assert _event(CatalystEventKind.EARNINGS, 5).scope is CatalystEventScope.COMPANY


def test_a_policy_event_bears_on_the_industry() -> None:
    event = _event(CatalystEventKind.INDUSTRY_POLICY, 5)

    assert event.scope is CatalystEventScope.INDUSTRY


def test_a_central_bank_event_bears_on_everything() -> None:
    assert _event(CatalystEventKind.FOMC, 5).scope is CatalystEventScope.MACRO


def test_an_ex_dividend_event_is_mechanical_and_moves_nothing() -> None:
    # It changes the price by the dividend by construction; it does not change
    # what anyone expects.
    assert _event(CatalystEventKind.EX_DIVIDEND, 5).is_mechanical is True
    assert _event(CatalystEventKind.EARNINGS, 5).is_mechanical is False


def test_an_event_knows_how_far_away_it_is() -> None:
    moment = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
    event = CatalystEvent(
        kind=CatalystEventKind.FOMC,
        occurs_on=date(2026, 9, 26),
        source="Test source",
        confirmed=True,
        description="议息",
    )

    assert event.days_from(moment) == 10
    assert event.is_upcoming(moment) is True


def test_an_event_behind_us_is_not_upcoming() -> None:
    moment = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
    event = CatalystEvent(
        kind=CatalystEventKind.FOMC,
        occurs_on=date(2026, 9, 10),
        source="Test source",
        confirmed=True,
        description="议息",
    )

    assert event.is_upcoming(moment) is False


# --------------------------------------------------------------------------
# Reading events back out of the evidence
# --------------------------------------------------------------------------


def test_an_event_is_written_into_the_evidence() -> None:
    evidence = _evidence(_event(CatalystEventKind.EARNINGS, 20))

    item = _event_item(evidence)

    assert item.metadata[KIND_METADATA_KEY] == "earnings"
    assert item.metadata[SCOPE_METADATA_KEY] == "company"
    assert item.metadata[CONFIRMED_METADATA_KEY] == "true"


def test_events_survive_the_round_trip_through_evidence() -> None:
    event = _event(CatalystEventKind.LAUNCH_WINDOW, 12, description="Neutron 发射")

    assert read_events(_evidence(event)) == (event,)


def test_two_events_of_one_kind_on_one_date_are_both_kept() -> None:
    # Two sources reporting the same date are two events: AIS has no basis for
    # deciding they are the same thing.
    first = _event(CatalystEventKind.FOMC, 30, source="Federal Reserve")
    second = _event(CatalystEventKind.FOMC, 30, symbol=None, source="Curated calendar")

    assert len(read_events(_evidence(first, second))) == 2


def test_no_events_reads_as_no_events() -> None:
    assert read_events(_evidence()) == ()


# --------------------------------------------------------------------------
# The rule
# --------------------------------------------------------------------------


def test_the_rule_exists_as_an_enabled_evaluation_rule() -> None:
    assert isinstance(RULE, EvaluationRule)
    assert RULE.id == "catalyst.upcoming"
    assert RULE.enabled is True


def test_the_rule_reports_the_distance_to_the_nearest_event() -> None:
    result = RULE.execute(
        _evidence(
            _event(CatalystEventKind.EARNINGS, 43),
            _event(CatalystEventKind.FOMC, 6),
        )
    )

    assert result.score == pytest.approx(6.0)
    assert result.evidence_references == (
        f"RKLB.catalyst.fomc.{date.today() + timedelta(days=6)}",
    )


def test_the_rule_fails_when_nothing_is_coming() -> None:
    with pytest.raises(DataError):
        RULE.execute(_evidence())


def test_the_rule_ignores_events_that_move_no_view() -> None:
    # An ex-dividend date is coming sooner than anything else and still does not
    # set the reading.
    with pytest.raises(DataError):
        RULE.execute(_evidence(_event(CatalystEventKind.EX_DIVIDEND, 2)))


# --------------------------------------------------------------------------
# The evaluator
# --------------------------------------------------------------------------


def test_evaluator_produces_a_catalyst_category_score() -> None:
    score = CatalystEvaluator().evaluate(_evidence(_event(CatalystEventKind.FOMC, 9)))

    assert isinstance(score, CategoryScore)
    assert score.category is Category.CATALYST
    assert score.coverage.describe() == "1/3"


def test_how_many_events_there_are_never_changes_the_reading() -> None:
    # Four events in the window read exactly as one does, when the nearest of
    # them is the same distance away. A busy calendar is not a bigger
    # opportunity.
    one = CatalystEvaluator().evaluate(
        _evidence(_event(CatalystEventKind.EARNINGS, 20))
    )
    four = CatalystEvaluator().evaluate(
        _evidence(
            _event(CatalystEventKind.EARNINGS, 20),
            _event(CatalystEventKind.FOMC, 34),
            _event(CatalystEventKind.PRODUCT_LAUNCH, 46),
            _event(CatalystEventKind.INDUSTRY_POLICY, 71),
        )
    )

    assert one.score == pytest.approx(four.score)


def test_a_nearer_event_does_change_the_reading() -> None:
    # The count does not matter; the distance does.
    far = CatalystEvaluator().evaluate(
        _evidence(_event(CatalystEventKind.EARNINGS, 40))
    )
    near = CatalystEvaluator().evaluate(
        _evidence(
            _event(CatalystEventKind.EARNINGS, 40),
            _event(CatalystEventKind.FOMC, 8),
        )
    )

    assert near.score < far.score


def test_coverage_counts_the_layers_that_produced_an_event() -> None:
    score = CatalystEvaluator().evaluate(
        _evidence(
            _event(CatalystEventKind.EARNINGS, 20),
            _event(CatalystEventKind.FOMC, 12),
        )
    )

    assert score.coverage.describe() == "2/3"
    assert score.coverage.total == len(CatalystEventScope)
    assert score.coverage.is_complete is False


def test_evaluator_reports_no_coverage_when_nothing_could_be_read() -> None:
    score = CatalystEvaluator().evaluate(_evidence())

    assert score.coverage.describe() == "0/3"
    assert score.evidence_references == ()


def test_evaluator_is_deterministic() -> None:
    evaluator = CatalystEvaluator()
    evidence = _evidence(_event(CatalystEventKind.FOMC, 9))

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)


# --------------------------------------------------------------------------
# The market data source
# --------------------------------------------------------------------------

_EPOCH = datetime(2026, 10, 29, 20, 0, tzinfo=UTC).timestamp()


def _summary(**calendar: object) -> dict[str, object]:
    return {"calendarEvents": calendar}


def test_the_market_data_source_reports_the_results_date() -> None:
    summary = _summary(
        earnings={"earningsDate": [{"raw": _EPOCH}], "isEarningsDateEstimate": False}
    )

    events = _events_from(summary, "RKLB", datetime(2026, 9, 16, tzinfo=UTC))

    assert [event.kind for event in events] == [CatalystEventKind.EARNINGS]
    assert events[0].occurs_on == date(2026, 10, 29)
    assert events[0].confirmed is True


def test_an_estimated_results_date_is_reported_as_unconfirmed() -> None:
    summary = _summary(
        earnings={"earningsDate": [{"raw": _EPOCH}], "isEarningsDateEstimate": True}
    )

    events = _events_from(summary, "RKLB", datetime(2026, 9, 16, tzinfo=UTC))

    assert events[0].confirmed is False


def test_a_date_that_has_passed_is_not_an_event() -> None:
    summary = _summary(exDividendDate={"raw": _EPOCH})

    events = _events_from(summary, "RKLB", datetime(2026, 12, 1, tzinfo=UTC))

    assert events == ()


def test_a_calendar_with_nothing_in_it_produces_no_events() -> None:
    assert _events_from(_summary(), "RKLB", datetime(2026, 9, 16, tzinfo=UTC)) == ()


# --------------------------------------------------------------------------
# The central bank source
# --------------------------------------------------------------------------

_NEXT_YEAR = date.today().year + 1

_FOMC_PAGE = f"""
<h4><a id="42828">{_NEXT_YEAR} FOMC Meetings</a></h4>
<div class="row fomc-meeting">
  <div class="fomc-meeting__month col-xs-5"><strong>January</strong></div>
  <div class="fomc-meeting__date col-xs-4">27-28</div>
</div>
<div class="row fomc-meeting">
  <div class="fomc-meeting__month col-xs-5"><strong>March</strong></div>
  <div class="fomc-meeting__date col-xs-4">17-18</div>
</div>
<div class="row fomc-meeting">
  <div class="fomc-meeting__month col-xs-5"><strong>April</strong></div>
  <div class="fomc-meeting__date col-xs-4">28-29</div>
</div>
<div class="row fomc-meeting">
  <div class="fomc-meeting__month col-xs-5"><strong>June</strong></div>
  <div class="fomc-meeting__date col-xs-4">16-17</div>
</div>
"""


class _StubTransport:
    """Transport that answers one page, or raises."""

    def __init__(self, page: str) -> None:
        self._page = page

    def get(self, url: str) -> str:
        return self._page


class _FailingTransport:
    """Transport that cannot reach anything."""

    def get(self, url: str) -> str:
        raise OSError("unreachable")


def test_the_central_bank_source_reports_the_second_day_of_each_meeting() -> None:
    provider = FederalReserveEventProvider(_StubTransport(_FOMC_PAGE))

    events = provider.fetch_events("RKLB")

    assert [event.occurs_on for event in events] == [
        date(_NEXT_YEAR, 1, 28),
        date(_NEXT_YEAR, 3, 18),
        date(_NEXT_YEAR, 4, 29),
        date(_NEXT_YEAR, 6, 17),
    ]
    assert {event.kind for event in events} == {CatalystEventKind.FOMC}


def test_a_meeting_that_has_passed_is_not_coming() -> None:
    this_year = date.today().year
    page = f"""
    <h4><a id="1">{this_year} FOMC Meetings</a></h4>
    <div class="fomc-meeting__month"><strong>January</strong></div>
    <div class="fomc-meeting__date">27-28</div>
    <div class="fomc-meeting__month"><strong>March</strong></div>
    <div class="fomc-meeting__date">17-18</div>
    <div class="fomc-meeting__month"><strong>April</strong></div>
    <div class="fomc-meeting__date">28-29</div>
    <div class="fomc-meeting__month"><strong>June</strong></div>
    <div class="fomc-meeting__date">16-17</div>
    """
    provider = FederalReserveEventProvider(_StubTransport(page))

    events = provider.fetch_events("RKLB")

    assert all(event.occurs_on >= date.today() for event in events)


def test_an_unreadable_page_produces_no_events_rather_than_wrong_ones() -> None:
    provider = FederalReserveEventProvider(_StubTransport("<html>changed</html>"))

    assert provider.fetch_events("RKLB") == ()


def test_a_partly_read_year_is_discarded_rather_than_trusted() -> None:
    page = """
    <h4><a id="1">2026 FOMC Meetings</a></h4>
    <div class="fomc-meeting__month"><strong>January</strong></div>
    <div class="fomc-meeting__date">27-28</div>
    """
    provider = FederalReserveEventProvider(_StubTransport(page))

    assert provider.fetch_events("RKLB") == ()


def test_a_source_that_cannot_be_reached_reports_nothing() -> None:
    provider = FederalReserveEventProvider(_FailingTransport())

    assert provider.fetch_events("RKLB") == ()


# --------------------------------------------------------------------------
# The curated calendar
# --------------------------------------------------------------------------


def _calendar(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    path = tmp_path / "events.json"
    path.write_text(json.dumps({"events": entries}), encoding="utf-8")
    return path


def test_the_curated_calendar_is_read(tmp_path: Path) -> None:
    ahead = (date.today() + timedelta(days=20)).isoformat()
    path = _calendar(
        tmp_path,
        [
            {
                "kind": "launch_window",
                "date": ahead,
                "description": "Neutron 火箭发射窗口",
                "symbol": "RKLB",
                "source": "Company guidance",
                "confirmed": False,
            }
        ],
    )

    events = CuratedCatalystEventProvider(path).fetch_events("RKLB")

    assert len(events) == 1
    assert events[0].scope is CatalystEventScope.COMPANY
    assert events[0].confirmed is False
    assert events[0].source == "Company guidance"


def test_a_curated_event_for_another_asset_is_not_returned(tmp_path: Path) -> None:
    ahead = (date.today() + timedelta(days=20)).isoformat()
    path = _calendar(
        tmp_path,
        [
            {
                "kind": "fomc",
                "date": ahead,
                "description": "议息",
                "symbol": "AAPL",
            }
        ],
    )

    assert CuratedCatalystEventProvider(path).fetch_events("RKLB") == ()


def test_a_curated_event_with_no_symbol_applies_to_every_asset(
    tmp_path: Path,
) -> None:
    ahead = (date.today() + timedelta(days=20)).isoformat()
    path = _calendar(
        tmp_path,
        [{"kind": "inflation", "date": ahead, "description": "CPI"}],
    )

    events = CuratedCatalystEventProvider(path).fetch_events("RKLB")

    assert events[0].scope is CatalystEventScope.MACRO
    assert events[0].symbol is None


def test_an_unknown_kind_is_skipped_rather_than_guessed(tmp_path: Path) -> None:
    ahead = (date.today() + timedelta(days=20)).isoformat()
    path = _calendar(
        tmp_path,
        [{"kind": "earnings_call_vibes", "date": ahead, "description": "?"}],
    )

    assert CuratedCatalystEventProvider(path).fetch_events("RKLB") == ()


def test_an_unreadable_date_is_skipped(tmp_path: Path) -> None:
    path = _calendar(
        tmp_path, [{"kind": "fomc", "date": "next Tuesday", "description": "议息"}]
    )

    assert CuratedCatalystEventProvider(path).fetch_events("RKLB") == ()


def test_a_curated_event_in_the_past_is_not_coming(tmp_path: Path) -> None:
    past = (date.today() - timedelta(days=2)).isoformat()
    path = _calendar(tmp_path, [{"kind": "fomc", "date": past, "description": "议息"}])

    assert CuratedCatalystEventProvider(path).fetch_events("RKLB") == ()


def test_an_absent_calendar_is_an_absence_rather_than_an_error(tmp_path: Path) -> None:
    provider = CuratedCatalystEventProvider(tmp_path / "missing.json")

    assert provider.fetch_events("RKLB") == ()


def test_a_calendar_that_cannot_be_parsed_reports_nothing(tmp_path: Path) -> None:
    path = tmp_path / "events.json"
    path.write_text("{not json", encoding="utf-8")

    assert CuratedCatalystEventProvider(path).fetch_events("RKLB") == ()


# --------------------------------------------------------------------------
# Evidence carries no invented confidence for an unconfirmed date
# --------------------------------------------------------------------------


def test_an_unconfirmed_date_is_marked_in_the_evidence() -> None:
    evidence = _evidence(_event(CatalystEventKind.LAUNCH_WINDOW, 9, confirmed=False))

    item = _event_item(evidence)

    assert item.metadata[DATE_METADATA_KEY]
    assert item.confidence == 1.0
    assert "not confirmed" in item.description


def test_market_metrics_are_still_carried_alongside_events() -> None:
    snapshot = MarketDataSnapshot(
        symbol="RKLB",
        source="Test source",
        retrieved_at=_RETRIEVED_AT,
        points=tuple(
            MarketDataPoint(metric=metric, value=None, reason="test")
            for metric in MarketMetric
        ),
    )
    evidence = EvidenceBuilder().build(
        _asset(), snapshot, (_event(CatalystEventKind.FOMC, 9),)
    )

    assert read_events(evidence)
    assert len(evidence.items) > len(MarketMetric)
