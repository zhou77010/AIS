"""Turning measurements into the sentences an investor reads.

A report is not a table of numbers. A reader wants to be told what the numbers
amount to, in their own language: "整体趋势向上" rather than a range position of
0.717 beside a change of +24.6%.

Everything here is a translation, never a new judgement. Each sentence restates
measurements that were retrieved and says nothing that those measurements do not
already say. Where a measurement is missing, the sentence is not written at all;
nothing is inferred to fill it.

The bands below are the same kind of provisional presentation as the category
grade: conventional readings, not methodology and not Constitution semantics,
and to be replaced once the standard score is defined. See
:mod:`analysis.category_grade`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from analysis.analysis_result import AnalysisResult
from analysis.labels import opportunity_condition_label, opportunity_headline
from contracts.market_data_provider import MarketDataPoint, MarketMetric
from models.category import Category
from models.opportunity_assessment import OpportunityAssessment

# Which moving averages the price is measured against, nearest first.
_MOVING_AVERAGES = (
    MarketMetric.TREND_MA20_GAP,
    MarketMetric.TREND_MA60_GAP,
    MarketMetric.TREND_MA120_GAP,
)

_MACD_STRONG = 0.010
_MACD_WEAK = -0.010
_RSI_STRONG = 60.0
_RSI_WEAK = 40.0
_VOLUME_BUSY = 0.30
_VOLUME_QUIET = -0.30

# Older readings, used only when no indicator could be computed. Where the
# price sits within the range it has traded in.
_POSITION_BANDS: tuple[tuple[float, str], ...] = (
    (0.80, "接近一年高位"),
    (0.60, "位于一年高位区间"),
    (0.40, "位于一年中段"),
    (0.20, "位于一年低位区间"),
    (float("-inf"), "接近一年低位"),
)

# Which way the price has moved over the window.
_DIRECTION_BANDS: tuple[tuple[float, str], ...] = (
    (0.20, "整体趋势向上"),
    (0.05, "整体小幅上行"),
    (-0.05, "整体横盘"),
    (-0.20, "整体小幅下行"),
    (float("-inf"), "整体趋势向下"),
)


def measurements_of(
    result: AnalysisResult, category: Category
) -> list[MarketDataPoint]:
    """Return the retrieved measurements that bear on one category.

    A measurement may support more than one category, so a category's readings
    are the ones whose categories include it, not only the ones filed under it.
    """
    snapshot = result.market_data
    if snapshot is None:
        return []
    return [
        point
        for point in snapshot.available_points
        if category in point.metric.categories
    ]


def sentence_for(result: AnalysisResult, category: Category) -> str | None:
    """Return the plain language sentence for a category, when one is written.

    Only categories whose measurements read better as a sentence have one. The
    rest report their measurements, and this returns None for them.
    """
    if category not in _SENTENCE_BUILDERS:
        return None
    values = {
        point.metric: point.value
        for point in measurements_of(result, category)
        if point.value is not None
    }
    return _SENTENCE_BUILDERS[category](values)


# Which categories are written as a sentence, and the function that writes it.
# Every sentence restates measurements that were retrieved and adds nothing to
# them; a category whose readings are simply a list of figures is not here.
_SENTENCE_BUILDERS: dict[
    Category, Callable[[Mapping[MarketMetric, float]], str | None]
] = {
    Category.TREND: lambda values: trend_sentence(values),
    Category.CATALYST: lambda values: catalyst_sentence(values),
    Category.POSITIONING: lambda values: positioning_sentence(values),
}


def trend_sentence(values: Mapping[MarketMetric, float]) -> str | None:
    """Return what the price has been doing, in plain language.

    The sentence restates the measurements that were retrieved and says nothing
    they do not already say. A measurement that is missing removes its clause
    rather than being inferred.

    Args:
        values: Retrieved trend measurements, keyed by metric.

    Returns:
        A sentence, or None when none of the measurements were retrieved.
    """
    clauses: list[str] = []

    alignment = _alignment_clause(values)
    if alignment is not None:
        clauses.append(alignment)

    momentum = _momentum_clause(values)
    if momentum is not None:
        clauses.append(momentum)

    volume = _volume_clause(values)
    if volume is not None:
        clauses.append(volume)

    if not clauses:
        return _fallback_sentence(values)
    return "，".join(clauses) + "。"


def _alignment_clause(values: Mapping[MarketMetric, float]) -> str | None:
    """Return where the price sits against its moving averages."""
    gaps = [values[metric] for metric in _MOVING_AVERAGES if metric in values]
    if not gaps:
        return None
    above = sum(1 for gap in gaps if gap > 0)
    if above == len(gaps):
        return "价格站上全部均线"
    if above * 2 > len(gaps):
        return "价格位于多数均线上方"
    if above == 0:
        return "价格跌破全部均线"
    return "价格在多空均线之间"


def _momentum_clause(values: Mapping[MarketMetric, float]) -> str | None:
    """Return what momentum and strength read as."""
    macd = values.get(MarketMetric.TREND_MACD)
    rsi = values.get(MarketMetric.TREND_RSI)

    if macd is not None and macd >= _MACD_STRONG:
        return "动能明显转强"
    if macd is not None and macd <= _MACD_WEAK:
        return "动能转弱"
    if rsi is not None and rsi >= _RSI_STRONG:
        return "走势偏强"
    if rsi is not None and rsi <= _RSI_WEAK:
        return "走势偏弱"
    if macd is not None or rsi is not None:
        return "动能中性"
    return None


def _volume_clause(values: Mapping[MarketMetric, float]) -> str | None:
    """Return what trading activity reads as."""
    ratio = values.get(MarketMetric.TREND_VOLUME_RATIO)
    if ratio is None:
        return None
    if ratio >= _VOLUME_BUSY:
        return "成交量明显放大"
    if ratio <= _VOLUME_QUIET:
        return "成交量明显萎缩"
    return None


def _fallback_sentence(values: Mapping[MarketMetric, float]) -> str | None:
    """Return a sentence from the older readings, when no indicator was computed."""
    position = values.get(MarketMetric.TREND_RANGE_POSITION)
    direction = values.get(MarketMetric.TREND_DIRECTION)
    parts: list[str] = []
    if direction is not None:
        parts.append(_band(direction, _DIRECTION_BANDS))
    if position is not None:
        parts.append(_band(position, _POSITION_BANDS))
    if not parts:
        return None
    return "，".join(parts) + "。"


def _band(value: float, bands: tuple[tuple[float, str], ...]) -> str:
    """Return the phrase a value reads at, first matching band winning."""
    for threshold, phrase in bands:
        if value >= threshold:
            return phrase
    return bands[-1][1]


# How near an event has to be to count as the thing likely to move the price.
_NEAR_EVENT_DAYS = 30.0

# Conventional readings for who is holding, and how crowded that is.
_INSTITUTIONAL_HEAVY = 0.60
_INSTITUTIONAL_LIGHT = 0.20
_INSIDER_HIGH = 0.10
_SHORT_HEAVY = 0.10
_SHORT_LIGHT = 0.03
_COVER_HEAVY_DAYS = 4.0
_COVER_LIGHT_DAYS = 2.0


def catalyst_sentence(values: Mapping[MarketMetric, float]) -> str | None:
    """Return why the price could move in the near future, in plain language.

    The sentence is about the distance to what is coming, because that is what
    makes an event a catalyst. It says when and does not say which way: whether a
    report will be good is not known before it is published, and a sentence that
    implied otherwise would be a forecast.

    Args:
        values: Retrieved catalyst measurements, keyed by metric.

    Returns:
        A sentence, or None when no forthcoming event was retrieved.
    """
    events: list[tuple[float, str]] = []
    earnings = values.get(MarketMetric.NEXT_EARNINGS_DAYS)
    if earnings is not None:
        events.append((earnings, f"{round(earnings)} 天后预计发布财报"))
    dividend = values.get(MarketMetric.NEXT_EX_DIVIDEND_DAYS)
    if dividend is not None:
        events.append((dividend, f"{round(dividend)} 天后除息"))

    if not events:
        return None
    events.sort()
    nearest, phrase = events[0]
    tail = (
        "，是近期最明确的波动来源。"
        if nearest <= _NEAR_EVENT_DAYS
        else "，是接下来最值得留意的时间点。"
    )
    return "，".join(text for _, text in events) + tail


def positioning_sentence(values: Mapping[MarketMetric, float]) -> str | None:
    """Return who is holding the asset, and how crowded that is.

    Holdings and crowding are stated as they were retrieved. A large holding is
    not called a good one: the scale that would say so is not defined yet, and a
    sentence is not the place to invent it.

    Args:
        values: Retrieved positioning measurements, keyed by metric.

    Returns:
        A sentence, or None when none of the measurements were retrieved.
    """
    clauses: list[str] = []

    institutions = values.get(MarketMetric.INSTITUTIONAL_OWNERSHIP)
    if institutions is not None:
        if institutions >= _INSTITUTIONAL_HEAVY:
            clauses.append("筹码以机构为主")
        elif institutions <= _INSTITUTIONAL_LIGHT:
            clauses.append("机构参与度不高")
        else:
            clauses.append("机构与个人共同持有")

    insiders = values.get(MarketMetric.INSIDER_OWNERSHIP)
    if insiders is not None and insiders >= _INSIDER_HIGH:
        clauses.append("管理层持股较重")

    crowding = _crowding_clause(
        values.get(MarketMetric.SHORT_PERCENT_OF_FLOAT),
        values.get(MarketMetric.SHORT_RATIO),
    )
    if crowding is not None:
        clauses.append(crowding)

    if not clauses:
        return None
    return "，".join(clauses) + "。"


def _crowding_clause(short_share: float | None, cover_days: float | None) -> str | None:
    """Return how crowded the short side of the trade is, or None when unmeasured."""
    if short_share is None and cover_days is None:
        return None
    heavy = (short_share is not None and short_share >= _SHORT_HEAVY) or (
        cover_days is not None and cover_days >= _COVER_HEAVY_DAYS
    )
    if heavy:
        return "空头力量较重"
    light = (short_share is None or short_share <= _SHORT_LIGHT) and (
        cover_days is None or cover_days <= _COVER_LIGHT_DAYS
    )
    return "空头力量有限" if light else "空头力量中性"


def opportunity_sentence(assessment: OpportunityAssessment) -> str:
    """Return why this is, or is not, one of the better opportunities today.

    The sentence names the conditions that hold and the conditions that do not,
    which is the whole of what the judgement contains: there is no combined score
    behind it to explain, because none was computed. A condition that could not
    be judged is left out of the sentence and named separately by the report,
    rather than being written as though it had failed.

    Args:
        assessment: Opportunity judgement to write.

    Returns:
        A sentence, always one: an opportunity that could not be judged at all is
        itself something a reader is owed.
    """
    held = [
        opportunity_condition_label(result.condition, True)
        for result in assessment.satisfied
    ]
    missing = [
        opportunity_condition_label(result.condition, False)
        for result in assessment.unsatisfied
    ]

    if assessment.grade is None:
        return "尚无可用的类别判断，机会条件无法评估。"

    lead = opportunity_headline(assessment.grade)
    if held and missing:
        return f"{lead}：{'、'.join(held)}；但{'、'.join(missing)}。"
    if held:
        return f"{lead}：{'、'.join(held)}。"
    return f"{lead}：{'、'.join(missing)}。"
