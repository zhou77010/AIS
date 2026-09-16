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

from contracts.market_data_provider import MarketMetric
from models.category import Category
from models.decision_state import DecisionState

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
    Category.MARKET: ("市场波动性", "利率环境"),
    Category.TREND: ("价格路径",),
}

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
    }
)

# Measurements where the sign is the point, and a plus is worth showing.
SIGNED_METRICS = frozenset(
    {
        MarketMetric.MARKET_DIRECTION,
        MarketMetric.TREND_DIRECTION,
        MarketMetric.EARNINGS_GROWTH,
        MarketMetric.EXPECTED_EARNINGS_CHANGE,
    }
)


def category_label(category: Category) -> str:
    """Return the name a category is reported under."""
    return CATEGORY_LABELS[category]


def decision_label(state: DecisionState) -> str:
    """Return the name a decision state is reported under."""
    return DECISION_LABELS[state]


def metric_name(metric: MarketMetric) -> str:
    """Return the name a measurement is reported under."""
    return METRIC_NAMES[metric]
