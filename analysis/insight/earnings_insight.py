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
    """Return what the earnings measurements mean, in reading order."""
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
