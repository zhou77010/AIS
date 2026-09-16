"""What the reported results said and what is expected next, read together.

The two halves of the Earnings question can point the same way or in opposite
directions. When they point in opposite directions, the disagreement is the
finding: the market is expecting something the results have not shown yet.

Nothing here says the next report will be good. It says what the last one showed
and what the expectation already contains.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from contracts.market_data_provider import MarketMetric as M
from models.insight import InsightLine

_STRONG = 0.15
_NEGATIVE = 0.0


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the earnings measurements mean, in reading order."""
    reported = context.value(M.EARNINGS_GROWTH)
    expected = context.value(M.EXPECTED_EARNINGS_CHANGE)
    metrics = [
        metric
        for metric in (M.EARNINGS_GROWTH, M.EXPECTED_EARNINGS_CHANGE)
        if context.has(metric)
    ]
    reference = context.reference(*metrics)
    if not reference:
        return ()

    if reported is not None and expected is not None:
        if reported < _NEGATIVE <= expected:
            return (
                InsightLine("已公布盈利下滑，但预期转为改善，分歧较大。", reference),
            )
        if reported >= _NEGATIVE and expected < _NEGATIVE:
            return (
                InsightLine("盈利已经改善，但预期转为回落，需要观察原因。", reference),
            )
        if reported >= _STRONG and expected > 0:
            return (InsightLine("已公布与预期同向改善，盈利方向一致。", reference),)
        if reported < _NEGATIVE and expected < _NEGATIVE:
            return (InsightLine("盈利与预期同时走弱，方向向下。", reference),)

    if reported is not None:
        if reported >= _STRONG:
            return (InsightLine("已公布盈利明显改善。", reference),)
        if reported < _NEGATIVE:
            return (InsightLine("已公布盈利同比下滑。", reference),)
        return (InsightLine("已公布盈利基本持平。", reference),)
    return (InsightLine("市场对盈利的预期在改变。", reference),)
