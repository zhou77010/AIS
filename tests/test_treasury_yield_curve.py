"""Tests for the Treasury yield curve provider.

Rates have one authority. These tests are about the file being read correctly — the two
most recent sessions, in the right order, with the right two legs — and about the
provider saying so plainly when it cannot be read at all.
"""

from __future__ import annotations

from datetime import date

import pytest

from contracts.market_environment import EnvironmentMetric
from data.treasury_yield_curve import TreasuryYieldCurveProvider

_METRICS = (
    EnvironmentMetric.TEN_YEAR_YIELD_CHANGE,
    EnvironmentMetric.CURVE_STEEPNESS,
    EnvironmentMetric.CURVE_CHANGE,
)

_HEADER = (
    'Date,"1 Mo","1.5 Month","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr",'
    '"5 Yr","7 Yr","10 Yr","20 Yr","30 Yr"'
)


def _row(day: str, *, two_year: float, ten_year: float) -> str:
    """Return one published row, shaped the way the file shapes it."""
    columns = [
        day,
        "3.97",
        "3.98",
        "4.10",
        "4.14",
        "4.24",
        "4.24",
        "4.44",
        str(two_year),
        "4.83",
        "4.86",
        "4.93",
        str(ten_year),
        "5.38",
        "5.34",
    ]
    return ",".join(columns)


def _file(*rows: str) -> str:
    return "\n".join((_HEADER, *rows))


class _Transport:
    """Transport stand-in answering one curve file per year."""

    def __init__(self, years: dict[int, str]) -> None:
        self.urls: list[str] = []
        self._years = years

    def get(self, url: str) -> str:
        self.urls.append(url)
        for year, payload in self._years.items():
            if f"/{year}/all" in url:
                return payload
        return _HEADER


def _fetch(
    payload: str,
    *,
    day: date = date(2026, 9, 21),
    extra: dict[int, str] | None = None,
):
    years = {2026: payload}
    if extra:
        years.update(extra)
    transport = _Transport(years)
    provider = TreasuryYieldCurveProvider(transport=transport, today=lambda: day)
    return provider.fetch(), transport


def _value(snapshot, metric: EnvironmentMetric) -> float | None:
    return snapshot.point(metric).value


def test_the_provider_answers_with_the_rates_it_owns() -> None:
    snapshot, _ = _fetch(_file(_row("09/18/2026", two_year=4.76, ten_year=5.01)))

    assert {point.metric for point in snapshot.points} == set(_METRICS)
    assert snapshot.source == "US Treasury"


def test_the_change_is_the_last_two_sessions_not_the_last_two_rows() -> None:
    # The file is published newest first from the top. A provider that read the rows in
    # the order they arrived would report the move of an older day, or of the wrong
    # direction.
    payload = _file(
        _row("09/16/2026", two_year=4.74, ten_year=5.01),
        _row("09/17/2026", two_year=4.67, ten_year=4.94),
        _row("09/18/2026", two_year=4.76, ten_year=5.01),
    )

    snapshot, _ = _fetch(payload)

    assert _value(snapshot, EnvironmentMetric.TEN_YEAR_YIELD_CHANGE) == pytest.approx(
        7.0
    )


def test_the_same_days_are_used_however_the_rows_are_ordered() -> None:
    rows = (
        _row("09/16/2026", two_year=4.74, ten_year=5.01),
        _row("09/17/2026", two_year=4.67, ten_year=4.94),
        _row("09/18/2026", two_year=4.76, ten_year=5.01),
    )

    newest_first, _ = _fetch(_file(*rows))
    shuffled, _ = _fetch(_file(rows[1], rows[2], rows[0]))

    assert _value(newest_first, EnvironmentMetric.CURVE_CHANGE) == pytest.approx(
        _value(shuffled, EnvironmentMetric.CURVE_CHANGE)
    )


def test_the_curve_is_the_ten_year_less_the_two_year() -> None:
    # The level needs one session, and one session is enough for it.
    snapshot, _ = _fetch(_file(_row("09/18/2026", two_year=4.76, ten_year=5.01)))

    assert _value(snapshot, EnvironmentMetric.CURVE_STEEPNESS) == pytest.approx(25.0)
    assert _value(snapshot, EnvironmentMetric.TEN_YEAR_YIELD_CHANGE) is None


def test_a_row_missing_a_leg_is_dropped_rather_than_repaired() -> None:
    # A spread computed from one yield and one guess is not a spread, so a row that is
    # missing a leg is skipped and the pair used is the two sessions that are whole.
    payload = _file(
        "09/18/2026,3.97,3.98,4.10,4.14,4.24,4.24,4.44,4.76,4.83,4.86,4.93,,5.38,5.34",
        _row("09/17/2026", two_year=4.67, ten_year=4.94),
        _row("09/16/2026", two_year=4.74, ten_year=5.01),
    )

    snapshot, _ = _fetch(payload)
    reason = snapshot.point(EnvironmentMetric.TEN_YEAR_YIELD_CHANGE).reason

    assert _value(snapshot, EnvironmentMetric.TEN_YEAR_YIELD_CHANGE) == pytest.approx(
        -7.0
    )
    assert "2026-09-17" in reason and "2026-09-16" in reason, reason


def test_the_curve_change_is_the_spread_today_against_yesterday() -> None:
    payload = _file(
        _row("09/17/2026", two_year=4.67, ten_year=4.94),
        _row("09/18/2026", two_year=4.76, ten_year=5.01),
    )

    snapshot, _ = _fetch(payload)

    assert _value(snapshot, EnvironmentMetric.CURVE_CHANGE) == pytest.approx(-2.0)


def test_every_reason_states_which_days_it_was_measured_between() -> None:
    payload = _file(
        _row("09/17/2026", two_year=4.67, ten_year=4.94),
        _row("09/18/2026", two_year=4.76, ten_year=5.01),
    )

    snapshot, _ = _fetch(payload)

    for metric in _METRICS:
        reason = snapshot.point(metric).reason
        assert "US Treasury" in reason, reason
        assert "2026-09-18" in reason, reason


def test_a_file_with_a_single_session_answers_the_level_and_no_move() -> None:
    snapshot, _ = _fetch(_file(_row("09/18/2026", two_year=4.76, ten_year=5.01)))

    assert _value(snapshot, EnvironmentMetric.CURVE_STEEPNESS) is not None
    assert snapshot.point(EnvironmentMetric.CURVE_CHANGE).value is None
    assert (
        "one usable curve session"
        in snapshot.point(EnvironmentMetric.CURVE_CHANGE).reason
    )


def test_a_year_that_has_not_been_published_yet_reads_the_previous_one() -> None:
    # Early in January the current file is empty, and the session before the new year
    # is in the previous one.
    payload = _file(
        _row("12/31/2025", two_year=4.60, ten_year=4.90),
        _row("12/30/2025", two_year=4.55, ten_year=4.88),
    )

    snapshot, transport = _fetch(
        _HEADER,
        day=date(2026, 1, 2),
        extra={2025: payload},
    )

    assert _value(snapshot, EnvironmentMetric.CURVE_CHANGE) == pytest.approx(-3.0)
    assert any("/2025/all" in url for url in transport.urls)


def test_an_unreadable_file_leaves_every_rate_missing_with_a_reason() -> None:
    snapshot, _ = _fetch("<html>we are down for maintenance</html>")

    for metric in _METRICS:
        point = snapshot.point(metric)
        assert point.value is None
        assert "No other source is read for rates" in point.reason


def test_the_provider_never_raises() -> None:
    class _Broken:
        def get(self, url: str) -> str:
            raise OSError("the network is not there")

    snapshot = TreasuryYieldCurveProvider(transport=_Broken()).fetch()

    assert snapshot.is_live is False
