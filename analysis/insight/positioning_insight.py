"""Who holds the trade, and how crowded that makes it.

Holdings and short interest are facts about other people's positions. What they mean
is whether the trade is already crowded: a lot of the same holder, or a lot of the
float sold short, changes what happens when the story moves.

Nothing here says the price will move because of who holds it. It says what the
register looks like and where the pressure would come from.

Holdings are **described and not judged** — a large institutional position is not a
better one — so those measurements carry words and no score, and the sentences below
read the words rather than a grade.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_STRONGEST = 5
_WEAK = 3
_WEAKEST = 2

_INSTITUTIONAL_FOCUSED = "机构为主"
_INSIDER_HIGH = "管理层持股较重"


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the positioning measurements mean, in reading order.

    One sentence about the register and one about crowding. There used to be a
    third saying short interest was worth watching, which said the same thing as
    the crowding sentence in weaker words and could contradict it: an asset could
    be told its short side was neutral and, in the next line, that it was worth
    watching.
    """
    return tuple(
        line for line in (_register(context), _crowding(context)) if line is not None
    )


def _register(context: InsightContext) -> InsightLine | None:
    """Return who is on the register and what that suggests about the holder base."""
    metrics = [
        metric
        for metric in (M.INSTITUTIONAL_OWNERSHIP, M.INSIDER_OWNERSHIP)
        if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return None
    institutions = context.word(M.INSTITUTIONAL_OWNERSHIP)
    insiders = context.word(M.INSIDER_OWNERSHIP)
    if institutions == _INSTITUTIONAL_FOCUSED:
        if insiders == _INSIDER_HIGH:
            return InsightLine("筹码以机构为主，管理层持有较重。", reference)
        return InsightLine("筹码以机构为主，持有结构相对稳定。", reference)
    if institutions is None:
        return None
    return InsightLine(f"{institutions}，持有结构以个人为主。", reference)


def _crowding(context: InsightContext) -> InsightLine | None:
    """Return whether the trade looks crowded on the short side.

    The words follow the bands: a short side described as middling is never called
    heavy, because the two statements would be about the same reading.
    """
    share = context.score(M.SHORT_PERCENT_OF_FLOAT)
    cover = context.score(M.SHORT_RATIO)
    metrics = [
        metric
        for metric in (M.SHORT_PERCENT_OF_FLOAT, M.SHORT_RATIO)
        if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return None
    heavy = (share is not None and share <= _WEAKEST) or (
        cover is not None and cover <= _WEAKEST
    )
    light = (share is None or share == _STRONGEST) and (cover is None or cover >= _WEAK)
    if heavy:
        return InsightLine("空头持仓较重，出现回补时价格会被放大。", reference)
    if light:
        return InsightLine("暂未看到明显的拥挤交易。", reference)
    return InsightLine("空头力量处于中性水平。", reference)
