"""What the price has been doing, and what that amounts to.

The measurements are where the price sits against its moving averages, what
momentum is doing, and whether participation is rising or falling. The sentences
say what those add up to: a structure intact, a structure broken, momentum fading
while the structure holds.

Nothing here says where the price will go. "Trend is intact" is a statement about
what the measurements show and not a view about tomorrow.

Every threshold in this module is a **band position**, not a number. Where the
bands fall is decided once, in the reading layer, and the grade beside these
sentences is read from the same bands.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_AVERAGES = (M.TREND_MA20_GAP, M.TREND_MA60_GAP, M.TREND_MA120_GAP)
# The band positions the sentences are keyed to. The best band is five.
_STRONGEST = 5
_STRONG = 4
_WEAK = 3
_WEAKEST = 2


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
    """Return where the price sits in its structure of moving averages.

    Read from the bands rather than from the sign of each gap. A gap of minus one
    per cent and a gap of minus twelve per cent are both "below the average", and
    only one of them is a broken structure; reading the sign made the two
    indistinguishable and let a sentence say the structure had broken while the
    trend still read well.
    """
    present = [metric for metric in _AVERAGES if context.has(metric)]
    if len(present) < 2:
        return None
    scores = [context.score(metric) for metric in present]
    ranked = [score for score in scores if score is not None]
    reference = context.reference(*present)
    if not ranked:
        return None
    if all(score >= _STRONG for score in ranked):
        return InsightLine("趋势结构完好，价格站稳全部均线。", reference)
    if all(score <= _WEAKEST for score in ranked):
        return InsightLine("趋势结构已经走坏，价格跌破全部均线。", reference)
    above = sum(1 for score in ranked if score >= _STRONG)
    if above * 2 > len(ranked):
        return InsightLine("趋势仍偏向上，价格位于多数均线上方。", reference)
    return InsightLine("趋势方向尚不明确，价格在多空均线之间。", reference)


def _momentum(context: InsightContext) -> InsightLine | None:
    """Return what momentum and strength read as."""
    macd = context.score(M.TREND_MACD)
    rsi = context.score(M.TREND_RSI)
    reference = context.reference(
        *[metric for metric in (M.TREND_MACD, M.TREND_RSI) if context.has(metric)]
    )
    if not reference:
        return None
    if macd == _STRONGEST:
        return InsightLine("动能仍在扩张，价格有持续推动力。", reference)
    if macd is not None and macd <= _WEAK:
        return InsightLine("动能已经转弱，价格缺少推动力。", reference)
    if rsi is not None and rsi >= _STRONGEST:
        return InsightLine("走势偏强，但动能并未加速。", reference)
    if rsi is not None and rsi <= _WEAK:
        return InsightLine("走势偏弱，动能也没有恢复。", reference)
    return InsightLine("动能中性，没有出现方向性信号。", reference)


def _participation(context: InsightContext) -> InsightLine | None:
    """Return whether trading activity is supporting the move or not."""
    volume = context.score(M.TREND_VOLUME_RATIO)
    if volume is None:
        return None
    reference = context.reference(M.TREND_VOLUME_RATIO)
    if volume == _STRONGEST:
        return InsightLine("成交量同步放大，参与度在提高。", reference)
    if volume <= _WEAKEST:
        return InsightLine("成交量萎缩，参与度在下降。", reference)
    return None


def _damage(context: InsightContext) -> InsightLine | None:
    """Return whether anything yet points to the trend turning.

    The clause that says nothing is stopping the fall is keyed to the bottom bands,
    so a trend that still reads well cannot produce it: a sentence denying the
    condition must not be reachable while the condition holds.
    """
    long_average = context.score(M.TREND_MA120_GAP)
    macd = context.score(M.TREND_MACD)
    if long_average is None or macd is None:
        return None
    reference = context.reference(M.TREND_MA120_GAP, M.TREND_MACD)
    if long_average <= _WEAKEST and macd <= _WEAKEST:
        return InsightLine("趋势转弱，目前尚未出现止跌信号。", reference)
    if long_average >= _STRONG and macd <= _WEAK:
        return InsightLine("短线动能放缓，但中长期结构尚未破坏。", reference)
    return None
