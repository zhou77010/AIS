"""What the reported results said and what is expected next, read together.

The two halves of the Earnings question can point the same way or in opposite
directions. When they point in opposite directions, the disagreement is the
finding: the market is expecting something the results have not shown yet.

Nothing here says the next report will be good. It says what the last one showed
and what the expectation already contains.

Every threshold is a band position owned by the reading layer, so a sentence about
earnings and the grade beside it are reading the same scale.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_STRONGEST = 5
_STRONG = 4
_WEAKEST = 2
_ABSENT = 1


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the earnings measurements mean, in reading order.

    The first sentence is the one about direction, read from the two halves of the
    question. The second, where the last report has one, is what that report did
    against what was expected of it: a different fact from either half, and the only
    one of the three that is over rather than expected.
    """
    lines = _direction_line(context)
    surprise = _surprise_line(context)
    return lines if surprise is None else lines + (surprise,)


def _direction_line(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the reported and expected halves say together."""
    reported = context.score(M.EARNINGS_GROWTH)
    expected = context.score(M.EXPECTED_EARNINGS_CHANGE)
    metrics = [
        metric
        for metric in (M.EARNINGS_GROWTH, M.EXPECTED_EARNINGS_CHANGE)
        if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return ()

    if reported is not None and expected is not None:
        if reported == _ABSENT and expected > _ABSENT:
            return (InsightLine("盈利下滑但预期改善，分歧较大。", reference),)
        if reported > _ABSENT and expected == _ABSENT:
            return (InsightLine("盈利改善但预期回落。", reference),)
        if reported >= _STRONG and expected > _ABSENT:
            return (InsightLine("已公布与预期同向改善，盈利方向一致。", reference),)
        if reported == _ABSENT and expected == _ABSENT:
            return (InsightLine("盈利与预期同时走弱，方向向下。", reference),)

    if reported is not None:
        if reported >= _STRONG:
            return (InsightLine("已公布盈利明显改善。", reference),)
        if reported == _ABSENT:
            return (InsightLine("已公布盈利同比下滑。", reference),)
        if reported == _WEAKEST:
            return (InsightLine("已公布盈利基本持平。", reference),)
    return (InsightLine("市场对盈利的预期在改变。", reference),)


def _surprise_line(context: InsightContext) -> InsightLine | None:
    """Return what the last report did against its estimate, or None.

    This is the only earnings measurement that describes something finished rather than
    something expected: the quarter has been reported and the number is what it was. It
    is described and not graded — the reading layer decides that, and it decided against
    grading it — so the sentence reports the difference and claims nothing about it.

    Where guidance is missing, the sentence is where a reader finds out. AIS does not
    read what a company says about its own next quarter, because no source it reads
    publishes it, and the estimates that stand in its place are somebody else's opinion.
    """
    word = context.word(M.EARNINGS_SURPRISE)
    value = context.value(M.EARNINGS_SURPRISE)
    reference = context.reference(M.EARNINGS_SURPRISE)
    if word is None or value is None or not reference:
        return None
    band = context.band(M.EARNINGS_SURPRISE)
    if band is not None and band.is_flat:
        return InsightLine(
            "最近一次财报与预期基本一致；公司 Guidance 不可获得。", reference
        )
    return InsightLine(
        f"最近一次财报{word} {abs(value):.1%}；公司 Guidance 不可获得。", reference
    )
