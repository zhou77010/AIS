"""Tests for the technical indicators.

Indicators are computed from price history, so these tests describe what each
one computes and, most importantly, that a history too short to carry an
indicator produces nothing rather than a number about a different window than
the one that was asked for.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from contracts.market_data_provider import PriceBar
from data import indicators


def _bars(closes: list[float], volume: float = 1_000.0) -> tuple[PriceBar, ...]:
    """Return one bar per close, with a flat intraday range."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        PriceBar(
            timestamp=start + timedelta(days=index),
            open=close,
            high=close * 1.01,
            low=close * 0.99,
            close=close,
            volume=volume,
        )
        for index, close in enumerate(closes)
    )


# --------------------------------------------------------------------------
# Moving averages
# --------------------------------------------------------------------------


def test_simple_moving_average_is_the_mean_of_the_window() -> None:
    assert indicators.simple_moving_average([1.0, 2.0, 3.0, 4.0], 2) == 3.5
    assert indicators.simple_moving_average([1.0, 2.0, 3.0, 4.0], 4) == 2.5


def test_simple_moving_average_is_absent_when_the_history_is_too_short() -> None:
    assert indicators.simple_moving_average([1.0, 2.0], 20) is None


def test_exponential_moving_average_reacts_faster_to_a_recent_change() -> None:
    # A flat series with a jump at the end. The exponential average carries more
    # of the recent jump, so it sits above the simple average.
    jumped = [1.0, 1.0, 1.0, 1.0, 1.0, 10.0]

    exponential = indicators.exponential_moving_average(jumped, 3)
    simple = indicators.simple_moving_average(jumped, 3)

    assert exponential is not None
    assert simple is not None
    assert exponential > simple


def test_exponential_moving_average_is_absent_when_the_history_is_too_short() -> None:
    assert indicators.exponential_moving_average([1.0, 2.0], 20) is None


# --------------------------------------------------------------------------
# Oscillators
# --------------------------------------------------------------------------


def test_relative_strength_index_reads_one_hundred_when_nothing_fell() -> None:
    rising = [float(value) for value in range(1, 30)]

    assert indicators.relative_strength_index(rising) == pytest.approx(100.0)


def test_relative_strength_index_reads_fifty_when_nothing_moved() -> None:
    flat = [10.0] * 30

    assert indicators.relative_strength_index(flat) == pytest.approx(50.0)


def test_relative_strength_index_reads_low_when_everything_fell() -> None:
    falling = [float(value) for value in range(30, 1, -1)]

    assert indicators.relative_strength_index(falling) == pytest.approx(0.0)


def test_relative_strength_index_is_absent_when_the_history_is_too_short() -> None:
    assert indicators.relative_strength_index([1.0, 2.0, 3.0]) is None


def test_macd_is_positive_when_the_fast_average_leads() -> None:
    rising = [float(value) for value in range(1, 80)]

    result = indicators.macd(rising)

    assert result is not None
    line, signal, histogram = result
    assert line > 0
    assert histogram == pytest.approx(line - signal)


def test_macd_is_absent_when_the_history_is_too_short() -> None:
    assert indicators.macd([float(value) for value in range(1, 20)]) is None


def test_bollinger_bands_straddle_the_average() -> None:
    values = [10.0 + (index % 5) for index in range(40)]

    result = indicators.bollinger_bands(values)

    assert result is not None
    lower, middle, upper = result
    assert lower < middle < upper
    assert middle == pytest.approx(indicators.simple_moving_average(values, 20))


def test_bollinger_bands_are_absent_when_the_history_is_too_short() -> None:
    assert indicators.bollinger_bands([1.0, 2.0]) is None


# --------------------------------------------------------------------------
# Range and risk
# --------------------------------------------------------------------------


def test_average_true_range_accounts_for_the_span_of_a_bar() -> None:
    bars = _bars([10.0] * 20)  # each bar spans 2% of its close

    result = indicators.average_true_range(bars, 14)

    assert result is not None
    assert result == pytest.approx(10.0 * 0.02, rel=0.01)


def test_average_true_range_is_absent_when_the_history_is_too_short() -> None:
    assert indicators.average_true_range(_bars([10.0] * 5), 14) is None


def test_annualised_volatility_is_zero_for_a_price_that_never_moved() -> None:
    assert indicators.annualised_volatility([10.0] * 30) == pytest.approx(0.0)


def test_annualised_volatility_rises_with_larger_moves() -> None:
    calm = [10.0 + (index % 2) * 0.01 for index in range(40)]
    wild = [10.0 + (index % 2) * 1.0 for index in range(40)]

    calm_reading = indicators.annualised_volatility(calm)
    wild_reading = indicators.annualised_volatility(wild)

    assert calm_reading is not None
    assert wild_reading is not None
    assert wild_reading > calm_reading


def test_annualised_volatility_is_absent_when_the_history_is_too_short() -> None:
    assert indicators.annualised_volatility([1.0, 2.0, 3.0]) is None


def test_maximum_drawdown_measures_the_largest_fall_from_a_peak() -> None:
    values = [100.0, 120.0, 90.0, 110.0, 60.0, 80.0]

    assert indicators.maximum_drawdown(values) == pytest.approx(-0.5)


def test_maximum_drawdown_is_zero_for_a_price_that_only_rose() -> None:
    assert indicators.maximum_drawdown([1.0, 2.0, 3.0]) == pytest.approx(0.0)


def test_maximum_drawdown_is_absent_without_any_price() -> None:
    assert indicators.maximum_drawdown([]) is None


# --------------------------------------------------------------------------
# Comparisons
# --------------------------------------------------------------------------


def test_relative_change_measures_the_move_against_the_earlier_figure() -> None:
    assert indicators.relative_change(110.0, 100.0) == pytest.approx(0.10)
    assert indicators.relative_change(90.0, 100.0) == pytest.approx(-0.10)


def test_relative_change_is_absent_when_the_comparison_has_no_meaning() -> None:
    # Dividing by a figure that is not positive says nothing about the change.
    assert indicators.relative_change(10.0, 0.0) is None
    assert indicators.relative_change(10.0, -5.0) is None
    assert indicators.relative_change(None, 10.0) is None
    assert indicators.relative_change(10.0, None) is None
