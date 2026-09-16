"""Provisional visual grade for a category.

The report shows an investor a grade out of five rather than the raw category
score, because the raw score is a mean of measurements on different scales and
means nothing: 13.26 beside 0.48 beside 5.95 cannot be compared, and asking a
reader to do so is asking them to be misled.

Where the grade comes from. It is **not** derived from the category score. It is
read from each measurement against the range that measurement is conventionally
read in — a price to earnings ratio below twelve reads cheap, above thirty five
reads expensive. The measurements are graded individually and the category grade
is their mean, rounded.

**This is presentation, and it is provisional.** It is not the AIS Standard
Score, it is not methodology, and it is not Constitution semantics. The bands
below are conventional rules of thumb, not decisions anyone has approved. They
exist so that the report is readable today, and they are to be replaced once the
standard score is defined. Until then the report says so in its own footer, and
the score itself stays raw and untouched underneath: this module reads evidence,
it never changes a judgement.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.analysis_result import AnalysisResult
from contracts.market_data_provider import MarketMetric
from models.category import Category

MIN_GRADE = 1
MAX_GRADE = 5

# Bands for measurements where a smaller number reads better. Each entry is
# (threshold, grade): the first threshold the value falls at or below wins.
_LOWER_IS_BETTER: dict[MarketMetric, tuple[tuple[float, int], ...]] = {
    MarketMetric.PE: ((12.0, 5), (18.0, 4), (25.0, 3), (35.0, 2)),
    MarketMetric.PEG: ((1.0, 5), (1.5, 4), (2.0, 3), (3.0, 2)),
    MarketMetric.EV_EBITDA: ((8.0, 5), (12.0, 4), (18.0, 3), (25.0, 2)),
    MarketMetric.BETA: ((0.8, 5), (1.0, 4), (1.3, 3), (1.8, 2)),
    # The source reports this as a percentage, so 100 means debt equals equity.
    MarketMetric.DEBT_TO_EQUITY: ((30.0, 5), (60.0, 4), (100.0, 3), (200.0, 2)),
    MarketMetric.RISK_VOLATILITY: ((0.20, 5), (0.30, 4), (0.45, 3), (0.70, 2)),
}

# Measurements where a negative reading means the quantity being measured
# against is not there, rather than that the reading is low. A negative price to
# earnings ratio means a loss, not a bargain, and grading it as the lowest
# multiple on the list would state the opposite of the truth.
_NEGATIVE_MEANS_ABSENT = frozenset(
    {
        MarketMetric.PE,
        MarketMetric.PEG,
        MarketMetric.EV_EBITDA,
        MarketMetric.DEBT_TO_EQUITY,
    }
)

# Bands for measurements where a larger number reads better. Signed
# measurements belong here too: a price below its moving average, or a drawdown,
# is a real reading and not a missing one, and it is read by how far from zero
# it is on the side that matters.
_HIGHER_IS_BETTER: dict[MarketMetric, tuple[tuple[float, int], ...]] = {
    MarketMetric.FCF_YIELD: ((0.06, 5), (0.04, 4), (0.02, 3), (0.0, 2)),
    MarketMetric.CURRENT_RATIO: ((2.0, 5), (1.5, 4), (1.2, 3), (1.0, 2)),
    MarketMetric.PROFIT_MARGIN: ((0.20, 5), (0.12, 4), (0.07, 3), (0.03, 2)),
    MarketMetric.RETURN_ON_EQUITY: ((0.25, 5), (0.15, 4), (0.10, 3), (0.05, 2)),
    MarketMetric.FREE_CASH_FLOW_MARGIN: ((0.15, 5), (0.10, 4), (0.05, 3), (0.02, 2)),
    MarketMetric.MARKET_DIRECTION: ((0.20, 5), (0.10, 4), (0.03, 3), (-0.03, 2)),
    MarketMetric.TREND_RANGE_POSITION: ((0.8, 5), (0.6, 4), (0.4, 3), (0.2, 2)),
    MarketMetric.TREND_DIRECTION: ((0.20, 5), (0.10, 4), (0.03, 3), (-0.03, 2)),
    MarketMetric.EARNINGS_GROWTH: ((0.30, 5), (0.15, 4), (0.05, 3), (0.0, 2)),
    MarketMetric.EXPECTED_EARNINGS_CHANGE: ((0.30, 5), (0.15, 4), (0.05, 3), (0.0, 2)),
    MarketMetric.TREND_MA20_GAP: ((0.05, 5), (0.0, 4), (-0.03, 3), (-0.08, 2)),
    MarketMetric.TREND_MA60_GAP: ((0.05, 5), (0.0, 4), (-0.03, 3), (-0.08, 2)),
    MarketMetric.TREND_MA120_GAP: ((0.08, 5), (0.02, 4), (-0.05, 3), (-0.12, 2)),
    MarketMetric.TREND_MACD: ((0.010, 5), (0.0, 4), (-0.010, 3), (-0.030, 2)),
    MarketMetric.TREND_RSI: ((60.0, 5), (50.0, 4), (40.0, 3), (30.0, 2)),
    MarketMetric.TREND_VOLUME_RATIO: ((0.30, 5), (0.10, 4), (-0.10, 3), (-0.30, 2)),
    MarketMetric.RISK_DRAWDOWN: ((-0.05, 5), (-0.10, 4), (-0.20, 3), (-0.35, 2)),
}


def grade_for_category(result: AnalysisResult, category: Category) -> int | None:
    """Return the provisional grade for one category, or None when it has none.

    Args:
        result: Analysis result to read.
        category: Category to grade.

    Returns:
        A grade from one to five, or None when no measurement of the category
        was retrieved. None means the report shows no grade rather than a low
        one, because nothing was read.
    """
    snapshot = result.market_data
    if snapshot is None:
        return None

    readings = [
        reading
        for point in snapshot.available_points
        if category in point.metric.categories
        for reading in (_reading_of(point.metric, point.value),)
        if reading is not None
    ]
    return _rounded_mean(readings)


def stars(grade: int) -> str:
    """Return the filled and empty stars for a grade."""
    filled = max(MIN_GRADE, min(MAX_GRADE, grade))
    return "★" * filled + "☆" * (MAX_GRADE - filled)


def _reading_of(metric: MarketMetric, value: float | None) -> int | None:
    """Return the grade one measurement reads at, or None when it is not graded.

    A negative reading of a ratio never reads as "very low, therefore very
    good". A negative price to earnings ratio, a negative enterprise value to
    EBITDA, or negative owners' equity all mean the quantity the ratio is
    measured against is not there, and grading them as cheap would state the
    opposite of the truth. They read at the worst grade instead.
    """
    if value is None:
        return None
    if metric in _LOWER_IS_BETTER:
        if metric is MarketMetric.BETA:
            # Beta describes how far the asset moves with its market, in either
            # direction. The size of the movement is what is read here.
            value = abs(value)
        elif metric in _NEGATIVE_MEANS_ABSENT and value < 0:
            return MIN_GRADE
        for threshold, grade in _LOWER_IS_BETTER[metric]:
            if value <= threshold:
                return grade
        return MIN_GRADE
    for threshold, grade in _HIGHER_IS_BETTER.get(metric, ()):
        if value >= threshold:
            return grade
    if metric in _HIGHER_IS_BETTER:
        return MIN_GRADE
    return None


def _rounded_mean(readings: Sequence[int]) -> int | None:
    """Return the mean of the readings, rounded, or None when there are none."""
    if not readings:
        return None
    return max(MIN_GRADE, min(MAX_GRADE, round(sum(readings) / len(readings))))
