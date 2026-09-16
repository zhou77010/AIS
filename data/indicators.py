"""Technical indicators computed from price history.

Indicators are computed, not retrieved: a moving average is a fact about prices
that were retrieved, and this module is the one place that turns bars into them.

Every function answers with ``None`` when the history is too short to carry the
indicator. A moving average over sixty days cannot be computed from thirty bars,
and a number produced anyway would be a number about a different window wearing
the wrong name. Nothing here guesses, fills forward or falls back to a shorter
window than it was asked for.

The indicators are the conventional ones, computed the conventional way, so that
a reader comparing them with any other tool sees the same figure:

* simple and exponential moving averages,
* MACD and its signal line,
* relative strength index,
* Bollinger bands,
* average true range,
* annualised volatility and maximum drawdown.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from contracts.market_data_provider import PriceBar

TRADING_DAYS_PER_YEAR = 252

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9


def simple_moving_average(values: Sequence[float], window: int) -> float | None:
    """Return the mean of the most recent values over a window.

    Args:
        values: Observations, oldest first.
        window: Number of observations to average.

    Returns:
        The average, or None when there are fewer observations than the window.
    """
    if window < 1 or len(values) < window:
        return None
    recent = values[-window:]
    return sum(recent) / window


def exponential_moving_average(values: Sequence[float], window: int) -> float | None:
    """Return the exponentially weighted mean of the values.

    Args:
        values: Observations, oldest first.
        window: Number of observations the weighting is based on.

    Returns:
        The average, or None when there are fewer observations than the window.
    """
    if window < 1 or len(values) < window:
        return None
    multiplier = 2.0 / (window + 1)
    average = sum(values[:window]) / window
    for value in values[window:]:
        average = (value - average) * multiplier + average
    return average


def macd(
    values: Sequence[float],
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> tuple[float, float, float] | None:
    """Return the MACD line, its signal line and the gap between them.

    Args:
        values: Closing prices, oldest first.
        fast: Window of the faster moving average.
        slow: Window of the slower moving average.
        signal: Window of the signal line.

    Returns:
        The three figures, or None when there is not enough history to compute
        them.
    """
    if len(values) < slow + signal:
        return None

    line: list[float] = []
    for end in range(slow, len(values) + 1):
        window = values[:end]
        fast_average = exponential_moving_average(window, fast)
        slow_average = exponential_moving_average(window, slow)
        if fast_average is None or slow_average is None:
            return None
        line.append(fast_average - slow_average)

    signal_line = exponential_moving_average(line, signal)
    if signal_line is None:
        return None
    latest = line[-1]
    return latest, signal_line, latest - signal_line


def relative_strength_index(values: Sequence[float], window: int = 14) -> float | None:
    """Return the relative strength index of the values.

    Args:
        values: Closing prices, oldest first.
        window: Number of periods the average gain and loss cover.

    Returns:
        The index from 0 to 100, or None when there is not enough history. A
        window with no losses reads as 100 and one with no gains reads as 0,
        which is what the index conventionally does.
    """
    if len(values) < window + 1:
        return None

    changes = [
        later - earlier for earlier, later in zip(values, values[1:], strict=False)
    ]
    recent = changes[-window:]
    average_gain = sum(change for change in recent if change > 0) / window
    average_loss = -sum(change for change in recent if change < 0) / window

    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0
    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def bollinger_bands(
    values: Sequence[float], window: int = 20, deviations: float = 2.0
) -> tuple[float, float, float] | None:
    """Return the lower, middle and upper Bollinger bands.

    Args:
        values: Closing prices, oldest first.
        window: Number of observations the bands are built from.
        deviations: How many standard deviations the outer bands sit at.

    Returns:
        The three bands, or None when there is not enough history.
    """
    middle = simple_moving_average(values, window)
    if middle is None:
        return None
    recent = values[-window:]
    variance = sum((value - middle) ** 2 for value in recent) / window
    spread = math.sqrt(variance) * deviations
    return middle - spread, middle, middle + spread


def average_true_range(bars: Sequence[PriceBar], window: int = 14) -> float | None:
    """Return the average true range of the bars.

    The true range of a bar is the largest of its own span and the two gaps from
    the previous close, which is what makes the measure account for gaps rather
    than only for intraday movement.

    Args:
        bars: Bars, oldest first.
        window: Number of bars to average over.

    Returns:
        The average, or None when there are not enough bars. The figure is in
        the same units as price, so it is only comparable within one asset.
    """
    if len(bars) < window + 1:
        return None

    ranges: list[float] = []
    for previous, current in zip(bars, bars[1:], strict=False):
        ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    return sum(ranges[-window:]) / window


def annualised_volatility(values: Sequence[float], window: int = 20) -> float | None:
    """Return the annualised volatility of the daily returns.

    Args:
        values: Closing prices, oldest first.
        window: Number of daily returns to measure over.

    Returns:
        The standard deviation of returns, scaled to a year, or None when there
        is not enough history.
    """
    if len(values) < window + 1:
        return None

    returns: list[float] = []
    for earlier, later in zip(values, values[1:], strict=False):
        if earlier <= 0:
            return None
        returns.append(later / earlier - 1.0)
    recent = returns[-window:]
    mean = sum(recent) / window
    variance = sum((value - mean) ** 2 for value in recent) / window
    return math.sqrt(variance) * math.sqrt(TRADING_DAYS_PER_YEAR)


def maximum_drawdown(values: Sequence[float]) -> float | None:
    """Return the largest fall from a peak to a later trough.

    Args:
        values: Closing prices, oldest first.

    Returns:
        The drawdown as a negative share of the peak, or None when there are no
        values. A price that never fell below an earlier peak reads as zero.
    """
    if not values:
        return None

    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def relative_change(latest: float | None, earlier: float | None) -> float | None:
    """Return how far one figure has moved from another, as a share of it.

    Args:
        latest: The more recent figure.
        earlier: The figure it is compared against.

    Returns:
        The change, or None when either figure is missing or the earlier one is
        not positive, in which case the comparison has no meaning.
    """
    if latest is None or earlier is None or earlier <= 0:
        return None
    return latest / earlier - 1.0
