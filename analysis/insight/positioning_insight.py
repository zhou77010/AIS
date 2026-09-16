"""Who holds the trade, and how crowded that makes it.

Holdings and short interest are facts about other people's positions. What they
mean is whether the trade is already crowded: a lot of the same holder, or a lot
of the float sold short, changes what happens when the story moves.

Nothing here says the price will move because of who holds it. It says what the
register looks like and where the pressure would come from.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_INSTITUTIONAL_HEAVY = 0.60
_INSTITUTIONAL_LIGHT = 0.20
_INSIDER_HIGH = 0.10
_SHORT_HEAVY = 0.10
_SHORT_NOTABLE = 0.05
_SHORT_LIGHT = 0.03
_COVER_HEAVY = 4.0


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the positioning measurements mean, in reading order."""
    return tuple(
        line
        for line in (_register(context), _crowding(context), _pressure(context))
        if line is not None
    )


def _register(context: InsightContext) -> InsightLine | None:
    """Return who is on the register and what that suggests about the holder base."""
    institutions = context.value(M.INSTITUTIONAL_OWNERSHIP)
    insiders = context.value(M.INSIDER_OWNERSHIP)
    metrics = [
        metric
        for metric in (M.INSTITUTIONAL_OWNERSHIP, M.INSIDER_OWNERSHIP)
        if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return None
    if institutions is not None and institutions >= _INSTITUTIONAL_HEAVY:
        if insiders is not None and insiders >= _INSIDER_HIGH:
            return InsightLine(
                "筹码以机构为主，管理层同时持有较重，结构相对稳定。", reference
            )
        return InsightLine("筹码以机构为主，持有结构相对稳定。", reference)
    if institutions is not None and institutions <= _INSTITUTIONAL_LIGHT:
        return InsightLine("机构参与度不高，持有结构以个人为主。", reference)
    return InsightLine("机构与个人共同持有，没有单一力量主导。", reference)


def _crowding(context: InsightContext) -> InsightLine | None:
    """Return whether the trade looks crowded on the short side."""
    share = context.value(M.SHORT_PERCENT_OF_FLOAT)
    cover = context.value(M.SHORT_RATIO)
    metrics = [
        metric
        for metric in (M.SHORT_PERCENT_OF_FLOAT, M.SHORT_RATIO)
        if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return None
    heavy = (share is not None and share >= _SHORT_HEAVY) or (
        cover is not None and cover >= _COVER_HEAVY
    )
    light = (share is None or share <= _SHORT_LIGHT) and (cover is None or cover < 2.0)
    if heavy:
        return InsightLine("空头持仓较重，出现回补时价格会被放大。", reference)
    if light:
        return InsightLine("暂未看到明显的拥挤交易。", reference)
    return InsightLine("空头力量处于中性水平。", reference)


def _pressure(context: InsightContext) -> InsightLine | None:
    """Return whether the short side is large enough to matter at all."""
    share = context.value(M.SHORT_PERCENT_OF_FLOAT)
    if share is None or share < _SHORT_NOTABLE:
        return None
    return InsightLine(
        "仍需关注空头是否继续增加，那会改变筹码结构。",
        context.reference(M.SHORT_PERCENT_OF_FLOAT),
    )
