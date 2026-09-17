"""What the business does, and whether the numbers agree with each other.

Profitability, cash conversion and the balance sheet are read together because
they can disagree, and the disagreement is the interesting part: a business
reporting profit it does not collect in cash is telling two different stories at
once, and a reader is owed that.

Nothing here says the business will keep doing this. It says what the reported
figures show, and where they do not line up.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_STRONG_MARGIN = 0.15
_GOOD_MARGIN = 0.07
_STRONG_RETURN = 0.15
_WEAK_CASH = 0.02
_STRONG_CASH = 0.08
_HEAVY_DEBT = 150.0
_THIN_LIQUIDITY = 1.0


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the fundamental measurements mean, in reading order."""
    return tuple(
        line
        for line in (
            _profitability(context),
            _quality(context),
            _balance_sheet(context),
        )
        if line is not None
    )


def _profitability(context: InsightContext) -> InsightLine | None:
    """Return how the business earns on what it sells and on what it owns."""
    margin = context.value(M.PROFIT_MARGIN)
    return_on_equity = context.value(M.RETURN_ON_EQUITY)
    metrics = [
        metric
        for metric in (M.PROFIT_MARGIN, M.RETURN_ON_EQUITY)
        if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return None
    if margin is not None and margin >= _STRONG_MARGIN:
        return InsightLine("盈利能力较强，净利转化效率高。", reference)
    if margin is not None and margin < 0:
        return InsightLine("目前仍处于亏损状态，盈利尚未形成。", reference)
    if return_on_equity is not None and return_on_equity >= _STRONG_RETURN:
        return InsightLine("资本回报率较高，自有资本的产出效率好。", reference)
    if margin is not None and margin < _GOOD_MARGIN:
        return InsightLine("利润率偏薄，对成本变化比较敏感。", reference)
    return InsightLine("盈利能力处于中等水平，没有明显优势。", reference)


def _quality(context: InsightContext) -> InsightLine | None:
    """Return whether reported profit is being collected in cash.

    This is the clause that earns its place: when profitability looks fine and
    the cash does not follow it, the evidence itself is inconsistent, and a
    reader who is not told will read the margin as though it were settled.
    """
    margin = context.value(M.PROFIT_MARGIN)
    cash = context.value(M.FREE_CASH_FLOW_MARGIN)
    if margin is None or cash is None:
        return None
    reference = context.reference(M.PROFIT_MARGIN, M.FREE_CASH_FLOW_MARGIN)
    if margin >= _GOOD_MARGIN and cash < _WEAK_CASH:
        return InsightLine("利润质量存疑：有利润，但没有现金流。", reference)
    if margin >= _GOOD_MARGIN and cash >= _STRONG_CASH:
        return InsightLine("利润有现金流支撑，盈利质量较好。", reference)
    if margin < 0 and cash < 0:
        return InsightLine("亏损与现金流出同时出现。", reference)
    return None


def _balance_sheet(context: InsightContext) -> InsightLine | None:
    """Return whether the financial structure can absorb a bad year."""
    debt = context.value(M.DEBT_TO_EQUITY)
    ratio = context.value(M.CURRENT_RATIO)
    metrics = [
        metric for metric in (M.DEBT_TO_EQUITY, M.CURRENT_RATIO) if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return None
    if debt is not None and debt >= _HEAVY_DEBT:
        return InsightLine("负债水平偏高，财务结构对利率敏感。", reference)
    if ratio is not None and ratio < _THIN_LIQUIDITY:
        return InsightLine("流动比率偏低，短期资金安排需要留意。", reference)
    return InsightLine("资产负债结构稳健，短期偿付没有压力。", reference)
