"""What is being paid, and what that says about expectations.

A multiple is a price divided by something the business delivers, and on its own
it says nothing. What it means depends on what it is measured against: a low
multiple on a shrinking business is not cheap, and a high one on a business
growing into it is not expensive.

Nothing here says the price will rise or fall. It says what the current price
already assumes, which is the part a reader can act on.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_CHEAP = 5
_EXPENSIVE = 2
_HIGH_GROWTH = 0.20


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the valuation measurements mean, in reading order."""
    return tuple(
        line
        for line in (_level(context), _expectations(context), _cash(context))
        if line is not None
    )


def _level(context: InsightContext) -> InsightLine | None:
    """Return whether the multiples read cheap, fair or expensive together."""
    rankings = [
        grade
        for grade in (
            _cheapness(context.value(M.PE), 12.0, 18.0, 25.0, 35.0),
            _cheapness(context.value(M.PEG), 1.0, 1.5, 2.0, 3.0),
            _cheapness(context.value(M.EV_EBITDA), 8.0, 12.0, 18.0, 25.0),
        )
        if grade is not None
    ]
    metrics = [
        metric
        for metric in (M.PE, M.PEG, M.EV_EBITDA)
        if context.has(metric) and (context.value(metric) or 0) > 0
    ]
    reference = context.reference(*metrics)
    if not rankings or not reference:
        return None

    average = sum(rankings) / len(rankings)
    if average >= _CHEAP - 0.5:
        return InsightLine("估值处于偏低区间，价格没有反映太多乐观预期。", reference)
    if average <= _EXPENSIVE + 0.5:
        return InsightLine("估值偏高，市场已经给出明显溢价。", reference)
    return InsightLine("估值处于合理区间，市场尚未给予明显溢价。", reference)


def _cheapness(
    value: float | None, best: float, good: float, fair: float, poor: float
) -> int | None:
    """Return how cheap one multiple reads, five being cheapest.

    A multiple that is not positive is not a level to be read: a negative price
    to earnings means a loss rather than a bargain, and it is left out.
    """
    if value is None or value <= 0:
        return None
    if value <= best:
        return 5
    if value <= good:
        return 4
    if value <= fair:
        return 3
    if value <= poor:
        return 2
    return 1


def _expectations(context: InsightContext) -> InsightLine | None:
    """Return whether the price is already assuming the growth on offer."""
    pe = context.value(M.PE)
    growth = context.value(M.EARNINGS_GROWTH)
    expected = context.value(M.EXPECTED_EARNINGS_CHANGE)
    if pe is None or pe <= 0 or growth is None:
        return None
    reference = context.reference(M.PE, M.EARNINGS_GROWTH)
    if pe >= 25.0 and growth < _HIGH_GROWTH:
        return InsightLine("高估值缺少与之匹配的增长，价格依赖预期兑现。", reference)
    if pe <= 15.0 and growth >= _HIGH_GROWTH:
        return InsightLine("增长不低而倍数不高，价格尚未反映已实现的增长。", reference)
    if expected is not None and expected < 0 and pe >= 25.0:
        return InsightLine(
            "估值不低而预期转为回落，估值扩张的空间有限。",
            context.reference(M.PE, M.EXPECTED_EARNINGS_CHANGE),
        )
    return None


def _cash(context: InsightContext) -> InsightLine | None:
    """Return whether the price is supported by cash the business produces."""
    yield_ = context.value(M.FCF_YIELD)
    if yield_ is None:
        return None
    reference = context.reference(M.FCF_YIELD)
    if yield_ < 0:
        return InsightLine("自由现金流为负，估值缺少现金收益支撑。", reference)
    if yield_ < 0.02:
        return InsightLine("现金回报很薄，价格主要由预期而非现金流支撑。", reference)
    return InsightLine("现金流提供了实际的估值支撑。", reference)
