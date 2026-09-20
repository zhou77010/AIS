"""Tests for the environment provider and the contract it answers with.

What arrives here is the market's own measurements, retrieved once for a whole pass.
The tests that matter are about the derivation: the vendor publishes two candidate
"previous closes", one of which is the close before the requested range, and reading
that one as the previous session would report a week's move as an overnight one.
"""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

from contracts.market_environment import EnvironmentMetric
from data.market_environment import YahooEnvironmentProvider


class _Transport:
    """Transport stand-in answering a canned series per symbol."""

    def __init__(self, series: dict[str, list[float | None]]) -> None:
        self.urls: list[str] = []
        self._series = series

    def get(self, url: str) -> str:
        self.urls.append(url)
        for symbol, closes in self._series.items():
            if f"/chart/{quote(symbol, safe='')}" in url:
                return json.dumps(_payload(closes))
        raise OSError(f"no series for {url}")


def _payload(closes: list[float | None]) -> dict:
    """Return a chart response shaped the way the vendor shapes it.

    The two closes the vendor offers are deliberately different: `chartPreviousClose`
    is the close before the range asked for, and the series holds one close per
    session.
    """
    return {
        "chart": {
            "result": [
                {
                    "meta": {"chartPreviousClose": closes[0]},
                    "indicators": {"quote": [{"close": closes}]},
                }
            ]
        }
    }


def _series(
    *,
    equity: list[float | None] = (100.0, 110.0),
    growth: list[float | None] = (200.0, 200.0),
    volatility: list[float | None] = (17.1, 15.4),
    yield_: list[float | None] = (4.90, 4.95),
) -> dict[str, list[float | None]]:
    return {
        "ES=F": list(equity),
        "NQ=F": list(growth),
        "^VIX": list(volatility),
        "^TNX": list(yield_),
    }


def _fetch(series: dict[str, list[float | None]] | None = None):
    transport = _Transport(series if series is not None else _series())
    return YahooEnvironmentProvider(transport=transport).fetch(), transport


def _value(snapshot, metric: EnvironmentMetric) -> float | None:
    return snapshot.point(metric).value


def test_a_snapshot_holds_one_point_per_measurement() -> None:
    snapshot, _ = _fetch()

    assert len(snapshot.points) == len(EnvironmentMetric)
    assert {point.metric for point in snapshot.points} == set(EnvironmentMetric)
    assert snapshot.is_live is True


def test_the_change_is_the_last_two_sessions_not_the_range_start() -> None:
    # The trap: the vendor's chartPreviousClose is the close before the range began.
    # Read as "the previous close" it would report three sessions of movement as one.
    snapshot, _ = _fetch(_series(equity=[100.0, 105.0, 110.0]))

    move = _value(snapshot, EnvironmentMetric.OVERNIGHT_EQUITY)
    assert move == pytest.approx(0.0476, abs=1e-4)
    assert move != pytest.approx(0.10, abs=1e-4)


def test_the_move_is_stated_with_how_it_was_derived() -> None:
    snapshot, _ = _fetch(_series(equity=[100.0, 110.0]))

    reason = snapshot.point(EnvironmentMetric.OVERNIGHT_EQUITY).reason

    assert "+10.00%" in reason
    assert "100.00" in reason and "110.00" in reason


def test_the_yield_move_is_reported_in_basis_points() -> None:
    snapshot, _ = _fetch(_series(yield_=[4.90, 4.95]))

    move = _value(snapshot, EnvironmentMetric.TEN_YEAR_YIELD_CHANGE)
    assert move == pytest.approx(5.0)


def test_the_volatility_level_and_its_change_come_from_one_series() -> None:
    # Two measurements, one fact, one request: asking twice would be asking the same
    # question twice and could answer it with two different numbers.
    snapshot, transport = _fetch(_series(volatility=[17.1, 16.0, 15.4]))

    assert _value(snapshot, EnvironmentMetric.VOLATILITY) == pytest.approx(15.4)
    assert _value(snapshot, EnvironmentMetric.VOLATILITY_CHANGE) == pytest.approx(-0.6)
    assert len(transport.urls) == 4
    assert sum("/chart/%5EVIX" in url for url in transport.urls) == 1


def test_a_session_with_no_close_is_dropped_rather_than_carried_forward() -> None:
    # Carrying the previous close forward would turn a gap into a flat session and
    # report a move nobody made.
    snapshot, _ = _fetch(_series(equity=[100.0, None, 110.0]))

    assert _value(snapshot, EnvironmentMetric.OVERNIGHT_EQUITY) == pytest.approx(0.10)


def test_one_session_cannot_produce_a_change() -> None:
    snapshot, _ = _fetch(_series(equity=[110.0]))

    point = snapshot.point(EnvironmentMetric.OVERNIGHT_EQUITY)
    assert point.value is None
    assert "two" in point.reason


def test_a_symbol_that_cannot_be_read_leaves_its_measurements_missing() -> None:
    # One unreachable symbol degrades one part of the environment, and says which.
    snapshot, _ = _fetch({"^VIX": [17.1, 15.4], "^TNX": [4.90, 4.95]})

    assert _value(snapshot, EnvironmentMetric.OVERNIGHT_EQUITY) is None
    assert _value(snapshot, EnvironmentMetric.OVERNIGHT_GROWTH) is None
    assert "ES=F" in snapshot.point(EnvironmentMetric.OVERNIGHT_EQUITY).reason
    assert _value(snapshot, EnvironmentMetric.VOLATILITY) == pytest.approx(15.4)


def test_a_source_that_answers_with_nonsense_is_not_believed() -> None:
    class _Nonsense:
        def get(self, url: str) -> str:
            return json.dumps({"chart": {"result": []}})

    snapshot = YahooEnvironmentProvider(transport=_Nonsense()).fetch()

    assert snapshot.is_live is False
    assert all(point.value is None for point in snapshot.points)
    assert all(point.reason for point in snapshot.points)


def test_the_provider_never_raises() -> None:
    class _Broken:
        def get(self, url: str) -> str:
            raise OSError("the network is not there")

    snapshot = YahooEnvironmentProvider(transport=_Broken()).fetch()

    assert snapshot.is_live is False
