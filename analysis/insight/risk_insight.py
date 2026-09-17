"""Where the risk is coming from, and what that means for taking a position.

A list of volatility, beta and drawdown tells a reader that the asset moves. It does
not tell them whether the movement comes from the price or from the business, and
that difference decides how a position should be built.

Nothing here says the asset will fall. It says where the uncertainty sits and what
kind of exposure a buyer is taking on.

**Every sentence is drawn from the band the reading fell in.** A sentence that fired
at a different threshold from the band beside it was a sentence that could deny the
grade: volatility reading "middling" could be described as clearly high, and a
balance sheet reading "middling" could be called heavily indebted. The thresholds
are band positions now, so the words and the numbers say the same thing.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_STRONGEST = 5
_STRONG = 4
_WEAK = 3
_WEAKEST = 2


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the risk measurements mean, in reading order."""
    return tuple(
        line
        for line in (
            _source(context),
            _price_risk(context),
            _drawdown(context),
            _financial_risk(context),
        )
        if line is not None
    )


def _source(context: InsightContext) -> InsightLine | None:
    """Return whether the uncertainty is in the price or in the business."""
    price = [metric for metric in (M.BETA, M.RISK_VOLATILITY) if context.has(metric)]
    financial = [
        metric for metric in (M.DEBT_TO_EQUITY, M.CURRENT_RATIO) if context.has(metric)
    ]
    if not price or not financial:
        return None

    volatility = context.score(M.RISK_VOLATILITY)
    beta = context.score(M.BETA)
    debt = context.score(M.DEBT_TO_EQUITY)
    ratio = context.score(M.CURRENT_RATIO)

    price_high = (volatility is not None and volatility <= _WEAK) or (
        beta is not None and beta <= _WEAK
    )
    finances_sound = (debt is None or debt >= _WEAK) and (
        ratio is None or ratio >= _WEAK
    )
    reference = context.reference(*price, *financial)
    if price_high and finances_sound:
        return InsightLine("风险主要来自价格波动，而非财务质量。", reference)
    return None


def _price_risk(context: InsightContext) -> InsightLine | None:
    """Return how much the price moves, in the words of the band it read in."""
    score = context.score(M.RISK_VOLATILITY)
    word = context.word(M.RISK_VOLATILITY)
    if score is None or word is None:
        return None
    reference = context.reference(M.RISK_VOLATILITY)
    if score <= _WEAKEST:
        return InsightLine(f"波动{word}，不宜一次性重仓。", reference)
    if score == _WEAK:
        return InsightLine(f"波动{word}，仓位需要相应控制。", reference)
    if score == _STRONG:
        return InsightLine(f"波动{word}，尚不属于极端水平。", reference)
    return InsightLine(f"波动{word}，价格层面的风险有限。", reference)


def _drawdown(context: InsightContext) -> InsightLine | None:
    """Return how far the asset has fallen from a peak, and what that says."""
    score = context.score(M.RISK_DRAWDOWN)
    word = context.word(M.RISK_DRAWDOWN)
    if score is None or word is None:
        return None
    reference = context.reference(M.RISK_DRAWDOWN)
    if score <= _WEAKEST:
        return InsightLine(f"历史回撤{word}，说明下跌具有方向性。", reference)
    if score == _WEAK:
        return InsightLine("回撤幅度中等，价格有过明显的下行段。", reference)
    return InsightLine(f"历史回撤{word}，尚未出现深度下跌。", reference)


def _financial_risk(context: InsightContext) -> InsightLine | None:
    """Return whether the balance sheet adds uncertainty of its own."""
    debt = context.score(M.DEBT_TO_EQUITY)
    ratio = context.score(M.CURRENT_RATIO)
    metrics = [
        metric for metric in (M.DEBT_TO_EQUITY, M.CURRENT_RATIO) if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return None
    if debt is not None and debt <= _WEAKEST:
        return InsightLine("负债水平偏高，财务质量本身构成风险。", reference)
    if ratio is not None and ratio <= _WEAKEST:
        return InsightLine("短期偿债能力偏紧，需要留意流动性。", reference)
    return InsightLine("资产负债表本身没有构成额外风险。", reference)
