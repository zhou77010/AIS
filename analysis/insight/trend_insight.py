"""What the price has been doing, and what that amounts to.

The measurements are where the price sits against its moving averages, what
momentum is doing, and whether participation is rising or falling. The sentences
say what those add up to: a structure intact, a structure broken, momentum
fading while the structure holds.

Nothing here says where the price will go. "Trend is intact" is a statement
about what the measurements show and not a view about tomorrow.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_AVERAGES = (M.TREND_MA20_GAP, M.TREND_MA60_GAP, M.TREND_MA120_GAP)
_STRONG_MOMENTUM = 0.010
_WEAK_MOMENTUM = -0.010
_STRONG_RSI = 60.0
_WEAK_RSI = 40.0
_BUSY_VOLUME = 0.30
_QUIET_VOLUME = -0.30


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the trend measurements mean, in reading order."""
    return tuple(
        line
        for line in (
            _structure(context),
            _momentum(context),
            _participation(context),
            _damage(context),
        )
        if line is not None
    )


def _structure(context: InsightContext) -> InsightLine | None:
    """Return where the price sits in its structure of moving averages."""
    present = [metric for metric in _AVERAGES if context.has(metric)]
    if len(present) < 2:
        return None
    above = sum(1 for metric in present if (context.value(metric) or 0) > 0)
    reference = context.reference(*present)
    if above == len(present):
        return InsightLine("趋势结构完好，价格站稳全部均线。", reference)
    if above == 0:
        return InsightLine("趋势结构已经走坏，价格跌破全部均线。", reference)
    if above * 2 > len(present):
        return InsightLine("趋势仍偏向上，价格位于多数均线上方。", reference)
    return InsightLine("趋势方向尚不明确，价格在多空均线之间。", reference)


def _momentum(context: InsightContext) -> InsightLine | None:
    """Return what momentum and strength read as."""
    macd = context.value(M.TREND_MACD)
    rsi = context.value(M.TREND_RSI)
    reference = context.reference(
        *[metric for metric in (M.TREND_MACD, M.TREND_RSI) if context.has(metric)]
    )
    if not reference:
        return None
    if macd is not None and macd >= _STRONG_MOMENTUM:
        return InsightLine("动能仍在扩张，价格有持续推动力。", reference)
    if macd is not None and macd <= _WEAK_MOMENTUM:
        return InsightLine("动能已经转弱，价格缺少推动力。", reference)
    if rsi is not None and rsi >= _STRONG_RSI:
        return InsightLine("走势偏强，但动能并未加速。", reference)
    if rsi is not None and rsi <= _WEAK_RSI:
        return InsightLine("走势偏弱，动能也没有恢复。", reference)
    return InsightLine("动能中性，没有出现方向性信号。", reference)


def _participation(context: InsightContext) -> InsightLine | None:
    """Return whether trading activity is supporting the move or not."""
    ratio = context.value(M.TREND_VOLUME_RATIO)
    if ratio is None:
        return None
    reference = context.reference(M.TREND_VOLUME_RATIO)
    if ratio >= _BUSY_VOLUME:
        return InsightLine("成交量同步放大，参与度在提高。", reference)
    if ratio <= _QUIET_VOLUME:
        return InsightLine("成交量萎缩，参与度在下降。", reference)
    return None


def _damage(context: InsightContext) -> InsightLine | None:
    """Return whether anything yet points to the trend turning."""
    long_average = context.value(M.TREND_MA120_GAP)
    macd = context.value(M.TREND_MACD)
    if long_average is None or macd is None:
        return None
    reference = context.reference(M.TREND_MA120_GAP, M.TREND_MACD)
    if long_average < 0 and macd <= _WEAK_MOMENTUM:
        return InsightLine("趋势转弱，目前尚未出现止跌信号。", reference)
    if long_average > 0 and macd <= _WEAK_MOMENTUM:
        return InsightLine("短线动能放缓，但中长期结构尚未破坏。", reference)
    return None
