"""What is being paid, and what that says about expectations.

A multiple is a price divided by something the business delivers, and on its own it
says nothing. What it means depends on what it is measured against: a low multiple
on a shrinking business is not cheap, and a high one on a business growing into it
is not expensive.

Nothing here says the price will rise or fall. It says what the current price
already assumes, which is the part a reader can act on.

What is being paid is the category read as a whole, so the sentence about the level
is the category's own reading — the same number the grade beside it is drawn from.
Where the bands fall is decided once, in the reading layer, and not here.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_MULTIPLES = (M.PE, M.PEG, M.EV_EBITDA)
_STRONGEST = 5
_STRONG = 4
_WEAK = 3
_WEAKEST = 2
_ABSENT = 1


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the valuation measurements mean, in reading order."""
    return tuple(
        line
        for line in (_level(context), _expectations(context), _cash(context))
        if line is not None
    )


def _level(context: InsightContext) -> InsightLine | None:
    """Return what the category reads as a whole.

    The reading is the category's own, which is what the grade is drawn from. When
    the sentence and the grade were computed separately they could disagree, and
    they did: a report could show four stars beside a sentence about how expensive
    the asset was.
    """
    mean = context.reading.mean_score
    reference = context.reference(
        *[
            metric
            for metric in _MULTIPLES
            if context.has(metric) and not context.is_absent(metric)
        ]
    )
    if mean is None or not reference:
        return None
    if mean >= _STRONG:
        return InsightLine("估值偏低，价格未反映太多乐观预期。", reference)
    if mean <= _WEAKEST:
        return InsightLine("估值偏高，市场已经给出明显溢价。", reference)
    return InsightLine("估值处于合理区间，市场尚未给予明显溢价。", reference)


def _expectations(context: InsightContext) -> InsightLine | None:
    """Return whether the price is already assuming the growth on offer."""
    pe = context.score(M.PE)
    growth = context.score(M.EARNINGS_GROWTH)
    expected = context.score(M.EXPECTED_EARNINGS_CHANGE)
    if pe is None or growth is None or context.is_absent(M.PE):
        return None
    reference = context.reference(M.PE, M.EARNINGS_GROWTH)
    if pe <= _WEAK and growth <= _STRONG:
        return InsightLine("高估值缺少增长匹配，价格依赖预期。", reference)
    if pe >= _STRONG and growth == _STRONGEST:
        return InsightLine("增长不低而倍数不高，价格尚未反映。", reference)
    if expected == _ABSENT and pe <= _WEAK:
        return InsightLine(
            "预期转为回落，估值扩张空间有限。",
            context.reference(M.PE, M.EXPECTED_EARNINGS_CHANGE),
        )
    return None


def _cash(context: InsightContext) -> InsightLine | None:
    """Return whether the price is supported by cash the business produces.

    This is the clause that earns its place beside a cheap multiple: a valuation can
    read well on multiples and still be unsupported, and a reader who is not told
    will take the level as settling the question.
    """
    cash = context.score(M.FCF_YIELD)
    if cash is None:
        return None
    reference = context.reference(M.FCF_YIELD)
    if cash == _ABSENT:
        return InsightLine("自由现金流为负，估值缺少现金收益支撑。", reference)
    if cash == _WEAKEST:
        return InsightLine("现金回报很薄，价格由预期支撑。", reference)
    return InsightLine("现金流提供了实际的估值支撑。", reference)
