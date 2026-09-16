"""Turning measurements into the sentences an investor reads.

A report is not a table of numbers. A reader wants to be told what the numbers
amount to, in their own language: "整体趋势向上" rather than a range position of
0.717 beside a change of +24.6%.

Everything here is a translation, never a new judgement. Each sentence restates
measurements that were retrieved and says nothing that those measurements do not
already say. Where a measurement is missing, the sentence is not written at all;
nothing is inferred to fill it.

The bands below are the same kind of provisional presentation as the category
grade: conventional readings, not methodology and not Constitution semantics,
and to be replaced once the standard score is defined. See
:mod:`analysis.category_grade`.
"""

from __future__ import annotations

from collections.abc import Mapping

from analysis.analysis_result import AnalysisResult
from contracts.market_data_provider import MarketDataPoint, MarketMetric
from models.category import Category

# Which moving averages the price is measured against, nearest first.
_MOVING_AVERAGES = (
    MarketMetric.TREND_MA20_GAP,
    MarketMetric.TREND_MA60_GAP,
    MarketMetric.TREND_MA120_GAP,
)

_MACD_STRONG = 0.010
_MACD_WEAK = -0.010
_RSI_STRONG = 60.0
_RSI_WEAK = 40.0
_VOLUME_BUSY = 0.30
_VOLUME_QUIET = -0.30

# Older readings, used only when no indicator could be computed. Where the
# price sits within the range it has traded in.
_POSITION_BANDS: tuple[tuple[float, str], ...] = (
    (0.80, "接近一年高位"),
    (0.60, "位于一年高位区间"),
    (0.40, "位于一年中段"),
    (0.20, "位于一年低位区间"),
    (float("-inf"), "接近一年低位"),
)

# Which way the price has moved over the window.
_DIRECTION_BANDS: tuple[tuple[float, str], ...] = (
    (0.20, "整体趋势向上"),
    (0.05, "整体小幅上行"),
    (-0.05, "整体横盘"),
    (-0.20, "整体小幅下行"),
    (float("-inf"), "整体趋势向下"),
)


def measurements_of(
    result: AnalysisResult, category: Category
) -> list[MarketDataPoint]:
    """Return the retrieved measurements that bear on one category.

    A measurement may support more than one category, so a category's readings
    are the ones whose categories include it, not only the ones filed under it.
    """
    snapshot = result.market_data
    if snapshot is None:
        return []
    return [
        point
        for point in snapshot.available_points
        if category in point.metric.categories
    ]


def sentence_for(result: AnalysisResult, category: Category) -> str | None:
    """Return the plain language sentence for a category, when one is written.

    Only categories whose measurements read better as a sentence have one. The
    rest report their measurements, and this returns None for them.
    """
    if category is not Category.TREND:
        return None
    values = {
        point.metric: point.value
        for point in measurements_of(result, category)
        if point.value is not None
    }
    return trend_sentence(values)


def trend_sentence(values: Mapping[MarketMetric, float]) -> str | None:
    """Return what the price has been doing, in plain language.

    The sentence restates the measurements that were retrieved and says nothing
    they do not already say. A measurement that is missing removes its clause
    rather than being inferred.

    Args:
        values: Retrieved trend measurements, keyed by metric.

    Returns:
        A sentence, or None when none of the measurements were retrieved.
    """
    clauses: list[str] = []

    alignment = _alignment_clause(values)
    if alignment is not None:
        clauses.append(alignment)

    momentum = _momentum_clause(values)
    if momentum is not None:
        clauses.append(momentum)

    volume = _volume_clause(values)
    if volume is not None:
        clauses.append(volume)

    if not clauses:
        return _fallback_sentence(values)
    return "，".join(clauses) + "。"


def _alignment_clause(values: Mapping[MarketMetric, float]) -> str | None:
    """Return where the price sits against its moving averages."""
    gaps = [values[metric] for metric in _MOVING_AVERAGES if metric in values]
    if not gaps:
        return None
    above = sum(1 for gap in gaps if gap > 0)
    if above == len(gaps):
        return "价格站上全部均线"
    if above * 2 > len(gaps):
        return "价格位于多数均线上方"
    if above == 0:
        return "价格跌破全部均线"
    return "价格在多空均线之间"


def _momentum_clause(values: Mapping[MarketMetric, float]) -> str | None:
    """Return what momentum and strength read as."""
    macd = values.get(MarketMetric.TREND_MACD)
    rsi = values.get(MarketMetric.TREND_RSI)

    if macd is not None and macd >= _MACD_STRONG:
        return "动能明显转强"
    if macd is not None and macd <= _MACD_WEAK:
        return "动能转弱"
    if rsi is not None and rsi >= _RSI_STRONG:
        return "走势偏强"
    if rsi is not None and rsi <= _RSI_WEAK:
        return "走势偏弱"
    if macd is not None or rsi is not None:
        return "动能中性"
    return None


def _volume_clause(values: Mapping[MarketMetric, float]) -> str | None:
    """Return what trading activity reads as."""
    ratio = values.get(MarketMetric.TREND_VOLUME_RATIO)
    if ratio is None:
        return None
    if ratio >= _VOLUME_BUSY:
        return "成交量明显放大"
    if ratio <= _VOLUME_QUIET:
        return "成交量明显萎缩"
    return None


def _fallback_sentence(values: Mapping[MarketMetric, float]) -> str | None:
    """Return a sentence from the older readings, when no indicator was computed."""
    position = values.get(MarketMetric.TREND_RANGE_POSITION)
    direction = values.get(MarketMetric.TREND_DIRECTION)
    parts: list[str] = []
    if direction is not None:
        parts.append(_band(direction, _DIRECTION_BANDS))
    if position is not None:
        parts.append(_band(position, _POSITION_BANDS))
    if not parts:
        return None
    return "，".join(parts) + "。"


def _band(value: float, bands: tuple[tuple[float, str], ...]) -> str:
    """Return the phrase a value reads at, first matching band winning."""
    for threshold, phrase in bands:
        if value >= threshold:
            return phrase
    return bands[-1][1]
