"""The words AIS reports use.

Every renderer takes its wording from here, so that the console report and the
mobile report call the same thing the same name and a term is translated once
rather than twice.

The report is written for an investor, so this is where developer language is
translated: category names, decision states and measurements are named in
Chinese. A measurement keeps its conventional name, because those names are what
an investor already reads elsewhere.
"""

from __future__ import annotations

from datetime import datetime

from contracts.market_data_provider import MarketMetric
from models.catalyst_event import CatalystEvent, CatalystEventKind, CatalystEventScope
from models.category import Category
from models.decision_state import DecisionState
from models.opportunity_assessment import OpportunityCondition

# Category names. HPO is deliberately left as HPO: the Constitution does not
# specify what it means, so it cannot be translated without inventing a meaning
# for it.
CATEGORY_LABELS: dict[Category, str] = {
    Category.MARKET: "市场环境",
    Category.FUNDAMENTAL: "基本面",
    Category.VALUATION: "估值",
    Category.EARNINGS: "盈利",
    Category.TREND: "趋势",
    Category.HPO: "HPO",
    Category.RISK: "风险",
    Category.CATALYST: "催化因素",
    Category.POSITIONING: "仓位",
}

# What each category counts when it says how much of itself it looked at.
CATEGORY_UNIT_NOUNS: dict[Category, str] = {
    Category.RISK: "个维度",
    Category.MARKET: "个方面",
    Category.TREND: "个方面",
    Category.EARNINGS: "个部分",
    Category.CATALYST: "个部分",
    Category.POSITIONING: "个部分",
}

CATEGORY_DEFAULT_UNIT_NOUN = "项"

# What an assessed category still does not cover, named the way an investor
# would say it. These are the things a reader is owed when a category was only
# partly looked at: naming them is more use than a fraction, and the fraction is
# model bookkeeping.
#
# This mirrors what each evaluator documents about itself. If an evaluator
# starts covering one of these, this list must lose it with it; the report only
# prints the list when the category's own coverage says it is incomplete, so a
# category that becomes complete stops printing it.
UNASSESSED_ITEMS: dict[Category, tuple[str, ...]] = {
    Category.RISK: ("业务风险", "估值风险", "事件风险", "证据风险", "长期风险"),
    # Volatility and rates were named here while nothing measured them. They are
    # measured now, so what remains is what the environment question still does not
    # reach: the industry an asset competes in, where money is moving, and what the
    # currency it earns in is doing.
    Category.MARKET: ("行业环境", "资金流向", "汇率环境"),
    Category.TREND: ("价格路径",),
    # Named by layer, because that is how the catalyst question is read and how
    # the report groups what it did find.
    Category.CATALYST: ("行业事件",),
    Category.POSITIONING: (
        "机构持仓变化",
        "内部人交易",
        "资金流向",
        "期权持仓",
        "市场情绪",
    ),
}

# What is shown where a grade would be when nothing was read. None is not a low
# grade, so it must never be drawn as one.
NO_GRADE = "暂无评级"

# What every report closes with, in the same words on every channel.
DISCLAIMER = "不构成投资建议"

DECISION_LABELS: dict[DecisionState, str] = {
    DecisionState.WATCH: "观望",
    DecisionState.ACCUMULATE: "增持",
    DecisionState.BUY: "买入",
    DecisionState.HOLD: "持有",
    DecisionState.TRIM: "减持",
    DecisionState.SELL: "卖出",
    DecisionState.WAIT: "等待",
}

METRIC_NAMES: dict[MarketMetric, str] = {
    MarketMetric.PE: "市盈率",
    MarketMetric.PEG: "PEG",
    MarketMetric.EV_EBITDA: "EV/EBITDA",
    MarketMetric.FCF_YIELD: "自由现金流收益率",
    MarketMetric.DCF: "DCF 公允价值",
    MarketMetric.BETA: "贝塔",
    MarketMetric.DEBT_TO_EQUITY: "负债权益比",
    MarketMetric.CURRENT_RATIO: "流动比率",
    MarketMetric.AVERAGE_VOLUME: "日均成交量",
    MarketMetric.FLOAT_SHARES: "流通股数",
    MarketMetric.PROFIT_MARGIN: "净利率",
    MarketMetric.RETURN_ON_EQUITY: "净资产收益率",
    MarketMetric.FREE_CASH_FLOW_MARGIN: "自由现金流利润率",
    MarketMetric.MARKET_DIRECTION: "大盘一年涨跌",
    MarketMetric.TREND_RANGE_POSITION: "52 周区间位置",
    MarketMetric.TREND_DIRECTION: "一年涨跌幅",
    MarketMetric.EARNINGS_GROWTH: "季度盈利同比",
    MarketMetric.EXPECTED_EARNINGS_CHANGE: "预期盈利变化",
    MarketMetric.TREND_MA20_GAP: "价格对 20 日均线",
    MarketMetric.TREND_MA60_GAP: "价格对 60 日均线",
    MarketMetric.TREND_MA120_GAP: "价格对 120 日均线",
    MarketMetric.TREND_MACD: "MACD 动能",
    MarketMetric.TREND_RSI: "相对强弱指标",
    MarketMetric.TREND_VOLUME_RATIO: "成交量对均值",
    MarketMetric.RISK_VOLATILITY: "年化波动率",
    MarketMetric.RISK_DRAWDOWN: "最大回撤",
    MarketMetric.SHORT_PERCENT_OF_FLOAT: "做空比例",
    MarketMetric.SHORT_RATIO: "空头回补天数",
    MarketMetric.INSTITUTIONAL_OWNERSHIP: "机构持股比例",
    MarketMetric.INSIDER_OWNERSHIP: "内部人持股比例",
}

# Measurements that are ratios, and read as percentages.
PERCENT_METRICS = frozenset(
    {
        MarketMetric.FCF_YIELD,
        MarketMetric.PROFIT_MARGIN,
        MarketMetric.RETURN_ON_EQUITY,
        MarketMetric.FREE_CASH_FLOW_MARGIN,
        MarketMetric.MARKET_DIRECTION,
        MarketMetric.TREND_RANGE_POSITION,
        MarketMetric.TREND_DIRECTION,
        MarketMetric.EARNINGS_GROWTH,
        MarketMetric.EXPECTED_EARNINGS_CHANGE,
        MarketMetric.TREND_MA20_GAP,
        MarketMetric.TREND_MA60_GAP,
        MarketMetric.TREND_MA120_GAP,
        MarketMetric.TREND_MACD,
        MarketMetric.TREND_VOLUME_RATIO,
        MarketMetric.RISK_VOLATILITY,
        MarketMetric.RISK_DRAWDOWN,
        MarketMetric.SHORT_PERCENT_OF_FLOAT,
        MarketMetric.INSTITUTIONAL_OWNERSHIP,
        MarketMetric.INSIDER_OWNERSHIP,
    }
)

# Measurements counted in days, which read as a distance in time rather than as a
# quantity with decimals.
DAY_METRICS = frozenset({MarketMetric.SHORT_RATIO})

# Measurements where the sign is the point, and a plus is worth showing.
SIGNED_METRICS = frozenset(
    {
        MarketMetric.MARKET_DIRECTION,
        MarketMetric.TREND_DIRECTION,
        MarketMetric.EARNINGS_GROWTH,
        MarketMetric.EXPECTED_EARNINGS_CHANGE,
        MarketMetric.TREND_MA20_GAP,
        MarketMetric.TREND_MA60_GAP,
        MarketMetric.TREND_MA120_GAP,
        MarketMetric.TREND_MACD,
        MarketMetric.TREND_VOLUME_RATIO,
        MarketMetric.RISK_DRAWDOWN,
    }
)


def category_label(category: Category) -> str:
    """Return the name a category is reported under."""
    return CATEGORY_LABELS[category]


# Whether a larger reading of a category's own measurement is better for the
# investor. Valuation and risk measure exposure, so a larger number is worse;
# the rest measure quality or strength, so larger is better.
#
# This is a presentation direction and not a scoring rule: it decides which way
# an arrow points, and nothing else. It is provisional in the same way the grade
# is, and is to be replaced when the standard score defines direction properly.
HIGHER_IS_BETTER: dict[Category, bool] = {
    Category.VALUATION: False,
    Category.RISK: False,
    # A nearer event and a less crowded short side are the readings this
    # category is looking for, and both are smaller numbers.
    Category.CATALYST: False,
    Category.POSITIONING: False,
}

# What a measurement moving a particular way reads as, in one phrase. A movement
# upward or downward is relative to the value the movement began from.
DRIVER_PHRASES: dict[tuple[MarketMetric, bool], str] = {
    (MarketMetric.PE, False): "市盈率回落",
    (MarketMetric.PE, True): "市盈率走高",
    (MarketMetric.PEG, False): "PEG 下降",
    (MarketMetric.PEG, True): "PEG 上升",
    (MarketMetric.EV_EBITDA, False): "EV/EBITDA 回落",
    (MarketMetric.EV_EBITDA, True): "EV/EBITDA 走高",
    (MarketMetric.FCF_YIELD, True): "自由现金流收益率改善",
    (MarketMetric.FCF_YIELD, False): "自由现金流收益率下降",
    (MarketMetric.BETA, False): "贝塔降低",
    (MarketMetric.BETA, True): "贝塔上升",
    (MarketMetric.RISK_VOLATILITY, False): "波动率下降",
    (MarketMetric.RISK_VOLATILITY, True): "波动率上升",
    (MarketMetric.RISK_DRAWDOWN, True): "最大回撤修复",
    (MarketMetric.RISK_DRAWDOWN, False): "最大回撤加深",
    (MarketMetric.DEBT_TO_EQUITY, False): "负债下降",
    (MarketMetric.DEBT_TO_EQUITY, True): "负债上升",
    (MarketMetric.CURRENT_RATIO, True): "短期偿债能力改善",
    (MarketMetric.CURRENT_RATIO, False): "短期偿债能力下降",
    (MarketMetric.PROFIT_MARGIN, True): "利润率改善",
    (MarketMetric.PROFIT_MARGIN, False): "利润率下降",
    (MarketMetric.RETURN_ON_EQUITY, True): "净资产收益率提升",
    (MarketMetric.RETURN_ON_EQUITY, False): "净资产收益率下降",
    (MarketMetric.FREE_CASH_FLOW_MARGIN, True): "现金流改善",
    (MarketMetric.FREE_CASH_FLOW_MARGIN, False): "现金流恶化",
    (MarketMetric.TREND_MA20_GAP, True): "重新站上 20 日均线",
    (MarketMetric.TREND_MA20_GAP, False): "跌破 20 日均线",
    (MarketMetric.TREND_MA60_GAP, True): "站上 60 日均线",
    (MarketMetric.TREND_MA60_GAP, False): "跌破 60 日均线",
    (MarketMetric.TREND_MA120_GAP, True): "站上 120 日均线",
    (MarketMetric.TREND_MA120_GAP, False): "跌破 120 日均线",
    (MarketMetric.TREND_MACD, True): "MACD 金叉",
    (MarketMetric.TREND_MACD, False): "MACD 死叉",
    (MarketMetric.TREND_RSI, True): "RSI 回升",
    (MarketMetric.TREND_RSI, False): "RSI 走弱",
    (MarketMetric.TREND_VOLUME_RATIO, True): "成交量放大",
    (MarketMetric.TREND_VOLUME_RATIO, False): "成交量萎缩",
    (MarketMetric.EARNINGS_GROWTH, True): "盈利预期上修",
    (MarketMetric.EARNINGS_GROWTH, False): "盈利预期下修",
    (MarketMetric.EXPECTED_EARNINGS_CHANGE, True): "盈利预期上修",
    (MarketMetric.EXPECTED_EARNINGS_CHANGE, False): "盈利预期下修",
    (MarketMetric.MARKET_DIRECTION, True): "大盘走强",
    (MarketMetric.MARKET_DIRECTION, False): "大盘走弱",
    (MarketMetric.TREND_DIRECTION, True): "价格上行",
    (MarketMetric.TREND_DIRECTION, False): "价格下行",
    (MarketMetric.TREND_RANGE_POSITION, True): "价格上行",
    (MarketMetric.TREND_RANGE_POSITION, False): "价格下行",
    (MarketMetric.SHORT_PERCENT_OF_FLOAT, True): "空头仓位加重",
    (MarketMetric.SHORT_PERCENT_OF_FLOAT, False): "空头仓位减轻",
    (MarketMetric.SHORT_RATIO, True): "空头回补压力上升",
    (MarketMetric.SHORT_RATIO, False): "空头回补压力下降",
    (MarketMetric.INSTITUTIONAL_OWNERSHIP, True): "机构持股上升",
    (MarketMetric.INSTITUTIONAL_OWNERSHIP, False): "机构持股下降",
}


def is_improvement(category: Category, momentum: float) -> bool:
    """Return whether a movement is an improvement for this category.

    Args:
        category: Category the movement is in.
        momentum: How far the category's own measurement has moved.

    Returns:
        True when the movement is towards a better reading of the category.
    """
    if momentum == 0:
        return False
    return (momentum > 0) == HIGHER_IS_BETTER.get(category, True)


def driver_phrase(metric: MarketMetric, rising: bool) -> str:
    """Return what a measurement moving one way reads as."""
    return DRIVER_PHRASES.get(
        (metric, rising), f"{METRIC_NAMES[metric]}{'上升' if rising else '下降'}"
    )


# How each named opportunity condition reads when it holds and when it does not.
# The two are written as separate phrases rather than as one phrase negated: "not
# an attractive valuation" is a sentence, and "估值不具备吸引力" is not.
OPPORTUNITY_CONDITION_LABELS: dict[OpportunityCondition, tuple[str, str]] = {
    OpportunityCondition.VALUATION: ("估值具备吸引力", "估值偏高"),
    OpportunityCondition.TREND: ("趋势向好", "趋势偏弱"),
    OpportunityCondition.RISK: ("风险可控", "风险偏高"),
    OpportunityCondition.CATALYST: ("有近期催化", "暂无近期催化"),
    OpportunityCondition.POSITIONING: ("资金不拥挤", "资金较为拥挤"),
}

# What a count of held conditions amounts to, highest first.
OPPORTUNITY_HEADLINES: tuple[tuple[int, str], ...] = (
    (4, "当前属于值得优先配置的机会"),
    (3, "当前机会一般，优先级不高"),
    (0, "目前不是优先配置的时点"),
)


def opportunity_condition_label(
    condition: OpportunityCondition, satisfied: bool
) -> str:
    """Return how one opportunity condition reads, held or not held."""
    held, missing = OPPORTUNITY_CONDITION_LABELS[condition]
    return held if satisfied else missing


def opportunity_headline(grade: int) -> str:
    """Return what a count of held conditions amounts to."""
    for threshold, headline in OPPORTUNITY_HEADLINES:
        if grade >= threshold:
            return headline
    return OPPORTUNITY_HEADLINES[-1][1]


# How the three layers of the catalyst question are named, in the order the
# report writes them: what the company has scheduled, what its industry faces,
# and what every asset is valued under.
CATALYST_SCOPE_LABELS: dict[CatalystEventScope, str] = {
    CatalystEventScope.COMPANY: "公司",
    CatalystEventScope.INDUSTRY: "行业",
    CatalystEventScope.MACRO: "宏观",
}

# What each kind of event is called when it is written into the report. A kind
# with no entry falls back to whatever the source called it, which is why every
# source states a description.
CATALYST_KIND_LABELS: dict[CatalystEventKind, str] = {
    CatalystEventKind.EARNINGS: "公布财报",
    CatalystEventKind.EX_DIVIDEND: "除息",
    CatalystEventKind.DIVIDEND: "派息",
    CatalystEventKind.SPLIT: "拆股",
    CatalystEventKind.INVESTOR_DAY: "投资者日",
    CatalystEventKind.PRODUCT_LAUNCH: "产品发布",
    CatalystEventKind.LAUNCH_WINDOW: "发射窗口",
    CatalystEventKind.REGULATORY: "监管决定",
    CatalystEventKind.SHAREHOLDER_MEETING: "股东大会",
    CatalystEventKind.INDUSTRY_POLICY: "行业政策",
    CatalystEventKind.COMPETITION: "竞争格局变化",
    CatalystEventKind.INDUSTRY_NEWS: "行业消息",
    CatalystEventKind.FOMC: "美联储议息",
    CatalystEventKind.INFLATION: "通胀数据",
    CatalystEventKind.EMPLOYMENT: "就业数据",
    CatalystEventKind.GROWTH: "增长数据",
    CatalystEventKind.RATES: "利率决议",
    CatalystEventKind.FISCAL_POLICY: "财政政策",
    CatalystEventKind.TARIFF: "关税决定",
    CatalystEventKind.CURRENCY: "汇率事件",
}

# Why a kind of event matters to an investment case, in one short clause. This
# is why the event is worth reading about, and it is a property of the kind
# rather than of the instance: AIS states what this sort of event does to an
# investment case, and never what this particular one will do, because nobody
# knows that before it happens.
CATALYST_KIND_REASONS: dict[CatalystEventKind, str] = {
    CatalystEventKind.EARNINGS: "业绩与指引改变增长预期",
    CatalystEventKind.EX_DIVIDEND: "价格按股息调整",
    CatalystEventKind.DIVIDEND: "现金回报的兑现",
    CatalystEventKind.SPLIT: "改变每股价格与流动性",
    CatalystEventKind.INVESTOR_DAY: "管理层给出中期目标",
    CatalystEventKind.PRODUCT_LAUNCH: "检验增长假设",
    CatalystEventKind.LAUNCH_WINDOW: "直接检验执行能力",
    CatalystEventKind.REGULATORY: "可能改变市场准入",
    CatalystEventKind.SHAREHOLDER_MEETING: "可能改变治理结构",
    CatalystEventKind.INDUSTRY_POLICY: "改变整个赛道盈利结构",
    CatalystEventKind.COMPETITION: "改变份额与定价能力",
    CatalystEventKind.INDUSTRY_NEWS: "改变行业层面的预期",
    CatalystEventKind.FOMC: "利率路径影响估值分母",
    CatalystEventKind.INFLATION: "决定利率预期",
    CatalystEventKind.EMPLOYMENT: "影响利率与风险偏好",
    CatalystEventKind.GROWTH: "影响周期与盈利预期",
    CatalystEventKind.RATES: "改变资金成本",
    CatalystEventKind.FISCAL_POLICY: "改变需求与税负",
    CatalystEventKind.TARIFF: "改变成本与市场准入",
    CatalystEventKind.CURRENCY: "改变汇兑与毛利",
}


def catalyst_kind_label(kind: CatalystEventKind, description: str) -> str:
    """Return what an event is called, preferring the name the source used."""
    return description or CATALYST_KIND_LABELS.get(kind, kind.value)


def catalyst_when(event: CatalystEvent, moment: datetime) -> str:
    """Return when an event falls, in the words a reader would use.

    The distance is written out only while it is short enough to mean something.
    Beyond that a date is clearer than "43 days", which a reader has to convert
    before it tells them anything.
    """
    days = event.days_from(moment)
    if days <= 0:
        return "今日"
    if days == 1:
        return "明日"
    if days <= 14:
        return f"{days} 天后"
    return f"{event.occurs_on.month}月{event.occurs_on.day}日"


def catalyst_kind_reason(kind: CatalystEventKind) -> str:
    """Return why this kind of event matters to an investment case."""
    return CATALYST_KIND_REASONS.get(kind, "可能改变市场预期")


def catalyst_scope_label(scope: CatalystEventScope) -> str:
    """Return the name a layer of the catalyst question is reported under."""
    return CATALYST_SCOPE_LABELS[scope]


def decision_label(state: DecisionState) -> str:
    """Return the name a decision state is reported under."""
    return DECISION_LABELS[state]


def metric_name(metric: MarketMetric) -> str:
    """Return the name a measurement is reported under."""
    return METRIC_NAMES[metric]
