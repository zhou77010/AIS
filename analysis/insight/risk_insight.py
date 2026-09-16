"""Where the risk is coming from, and what that means for taking a position.

A list of volatility, beta and drawdown tells a reader that the asset moves. It
does not tell them whether the movement comes from the price or from the
business, and that difference decides how a position should be built.

Nothing here says the asset will fall. It says where the uncertainty sits and
what kind of exposure a buyer is taking on.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_HIGH_VOLATILITY = 0.45
_ELEVATED_VOLATILITY = 0.30
_HIGH_BETA = 1.30
_DEEP_DRAWDOWN = -0.35
_NOTABLE_DRAWDOWN = -0.20
_HEAVY_DEBT = 100.0
_THIN_LIQUIDITY = 1.0


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

    volatility = context.value(M.RISK_VOLATILITY)
    beta = context.value(M.BETA)
    debt = context.value(M.DEBT_TO_EQUITY)
    ratio = context.value(M.CURRENT_RATIO)

    price_high = (volatility is not None and volatility >= _HIGH_VOLATILITY) or (
        beta is not None and abs(beta) >= _HIGH_BETA
    )
    finances_sound = (debt is None or debt <= _HEAVY_DEBT) and (
        ratio is None or ratio >= _THIN_LIQUIDITY
    )
    reference = context.reference(*price, *financial)
    if price_high and finances_sound:
        return InsightLine("风险主要来自价格波动，而非财务质量。", reference)
    return None


def _price_risk(context: InsightContext) -> InsightLine | None:
    """Return how much the price moves compared with the market."""
    volatility = context.value(M.RISK_VOLATILITY)
    beta = context.value(M.BETA)
    reference = context.reference(
        *[metric for metric in (M.BETA, M.RISK_VOLATILITY) if context.has(metric)]
    )
    if not reference:
        return None
    if volatility is not None and volatility >= _HIGH_VOLATILITY:
        return InsightLine("波动明显偏高，适合分批建仓而非一次性重仓。", reference)
    if beta is not None and abs(beta) >= _HIGH_BETA:
        return InsightLine("波动高于市场平均，仓位需要相应控制。", reference)
    if volatility is not None and volatility >= _ELEVATED_VOLATILITY:
        return InsightLine("波动高于多数标的，但不属于极端水平。", reference)
    if volatility is not None:
        return InsightLine("波动相对温和，价格层面的风险有限。", reference)
    return None


def _drawdown(context: InsightContext) -> InsightLine | None:
    """Return how far the asset has fallen from a peak, and what that says."""
    drawdown = context.value(M.RISK_DRAWDOWN)
    if drawdown is None:
        return None
    reference = context.reference(M.RISK_DRAWDOWN)
    if drawdown <= _DEEP_DRAWDOWN:
        return InsightLine("历史回撤幅度较大，说明下跌具有方向性。", reference)
    if drawdown <= _NOTABLE_DRAWDOWN:
        return InsightLine("回撤幅度不算小，价格有明显的下行段。", reference)
    return InsightLine("回撤控制得较好，尚未出现深度下跌。", reference)


def _financial_risk(context: InsightContext) -> InsightLine | None:
    """Return whether the balance sheet adds uncertainty of its own."""
    debt = context.value(M.DEBT_TO_EQUITY)
    ratio = context.value(M.CURRENT_RATIO)
    reference = context.reference(
        *[
            metric
            for metric in (M.DEBT_TO_EQUITY, M.CURRENT_RATIO)
            if context.has(metric)
        ]
    )
    if not reference:
        return None
    if debt is not None and debt >= _HEAVY_DEBT:
        return InsightLine("负债水平偏高，财务质量本身构成风险。", reference)
    if ratio is not None and ratio < _THIN_LIQUIDITY:
        return InsightLine("短期偿债能力偏紧，需要关注流动性。", reference)
    return InsightLine("资产负债表本身没有构成额外风险。", reference)
