"""The environment the asset is being judged in.

Market answers a question about context, and the honest answer today is narrow:
the only measurement connected is how the broad market has moved over a year.
The insight says what that means and says nothing about sectors, styles or rates,
because none of them are connected and an interpretation of a measurement AIS
does not have would be an invention.

When industry and macro data arrive, this builder grows. It does not need to be
replaced.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_RISING = 0.10
_FALLING = -0.10


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the environment measurements mean."""
    direction = context.value(M.MARKET_DIRECTION)
    if direction is None:
        return ()
    reference = context.reference(M.MARKET_DIRECTION)
    if direction >= _RISING:
        return (InsightLine("大盘整体上行，环境对风险资产偏友好。", reference),)
    if direction <= _FALLING:
        return (InsightLine("大盘整体下行，环境对新增仓位不利。", reference),)
    return (InsightLine("大盘整体横盘，环境没有提供方向。", reference),)
