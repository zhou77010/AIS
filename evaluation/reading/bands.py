"""What a measurement means, defined once.

Every number AIS reads is read against a scale, and this module owns every one of
those scales. They were previously written down in three places that did not know
about each other — the star grade had one set, the sentences had another, and the
opportunity conditions had a third — and they disagreed in public. A report said a
valuation was attractive beside a sentence saying the cash flow did not support it,
because one read a rounded average and the other read a measurement.

**One scale per measurement.** A scale says which way it runs, where its steps
fall, and what each step is called. The word is what a sentence uses; the position
is what a grade uses. Both come from the same row, so they cannot drift.

**Provisional, and provisional together.** These are conventional rules of thumb,
not the AIS Standard Score and not a decision anyone has approved. They exist so
that the report is readable today. When the standard score is defined it replaces
this module, and it replaces the whole of it — changing one row and not the others
is how a report starts contradicting itself.

**A scale may describe without judging.** Institutional and insider holdings have
words and no scores, because a large holding is not a better one without a scale
that says so. Those measurements are read and never graded.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from contracts.market_data_provider import MarketMetric

MIN_SCORE = 1
MAX_SCORE = 5


class Direction(StrEnum):
    """Which way a scale runs, and therefore which way reads better."""

    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"


@dataclass(frozen=True)
class Band:
    """One step of a scale.

    Attributes:
        threshold: The value that qualifies for this step: the reading is in this
            band when it falls at or below the threshold on a scale where lower is
            better, and at or above it where higher is.
        word: How a reading in this band is described. It is what a sentence says
            and it is the only place the wording is decided.
    """

    threshold: float
    word: str


@dataclass(frozen=True)
class MetricScale:
    """How one measurement is read.

    Attributes:
        direction: Which way reads better.
        bands: The steps of the scale, best first. Position carries the score: the
            first band is the best reading and the last is the second worst, and a
            reading that reaches none of them is the worst.
        below_word: What a reading that reaches none of the bands is called.
        graded: Whether the measurement contributes to a grade. A scale that only
            describes is read for its word and never for a score.
        negative_means_absent: Whether a negative reading means the quantity being
            measured against is not there rather than that the reading is low. A
            negative price to earnings ratio means a loss, not a bargain, and
            reading it as the cheapest multiple on the list would state the
            opposite of the truth.
        read_absolute: Whether the size of the reading is what matters, in either
            direction. Beta describes how far an asset moves with its market, and
            the movement is what is read.
    """

    direction: Direction
    bands: tuple[Band, ...]
    below_word: str
    graded: bool = True
    negative_means_absent: bool = False
    read_absolute: bool = False


def _lower(
    bands: tuple[tuple[float, str], ...],
    below_word: str,
    *,
    graded: bool = True,
    negative_means_absent: bool = False,
    read_absolute: bool = False,
) -> MetricScale:
    """Return a scale on which a smaller reading is a better one."""
    return MetricScale(
        direction=Direction.LOWER_IS_BETTER,
        bands=tuple(Band(threshold, word) for threshold, word in bands),
        below_word=below_word,
        graded=graded,
        negative_means_absent=negative_means_absent,
        read_absolute=read_absolute,
    )


def _higher(
    bands: tuple[tuple[float, str], ...],
    below_word: str,
    *,
    graded: bool = True,
) -> MetricScale:
    """Return a scale on which a larger reading is a better one."""
    return MetricScale(
        direction=Direction.HIGHER_IS_BETTER,
        bands=tuple(Band(threshold, word) for threshold, word in bands),
        below_word=below_word,
        graded=graded,
    )


# Every scale AIS reads a number against. The words are what the report says; the
# position of a band is the score it carries. Adding a measurement means adding a
# row here, and any component that reads it picks the row up without being told.
SCALES: dict[MarketMetric, MetricScale] = {
    # --- What is being paid, relative to what the business delivers ----------
    MarketMetric.PE: _lower(
        ((12.0, "很便宜"), (18.0, "便宜"), (25.0, "合理"), (35.0, "偏贵")),
        "很贵",
        negative_means_absent=True,
    ),
    MarketMetric.PEG: _lower(
        ((1.0, "很低"), (1.5, "偏低"), (2.0, "合理"), (3.0, "偏高")),
        "很高",
        negative_means_absent=True,
    ),
    MarketMetric.EV_EBITDA: _lower(
        ((8.0, "很低"), (12.0, "偏低"), (18.0, "合理"), (25.0, "偏高")),
        "很高",
        negative_means_absent=True,
    ),
    MarketMetric.FCF_YIELD: _higher(
        ((0.06, "充足"), (0.04, "偏厚"), (0.02, "偏薄"), (0.0, "很薄")),
        "为负",
    ),
    # --- The business, and whether the numbers agree with each other ---------
    MarketMetric.PROFIT_MARGIN: _higher(
        ((0.20, "很强"), (0.12, "较强"), (0.07, "偏薄"), (0.03, "很薄")),
        "为负",
    ),
    MarketMetric.RETURN_ON_EQUITY: _higher(
        ((0.25, "很高"), (0.15, "较高"), (0.10, "中等"), (0.05, "偏低")),
        "为负",
    ),
    MarketMetric.FREE_CASH_FLOW_MARGIN: _higher(
        ((0.15, "很厚"), (0.10, "偏厚"), (0.05, "偏薄"), (0.02, "很薄")),
        "为负",
    ),
    MarketMetric.CURRENT_RATIO: _higher(
        ((2.0, "充足"), (1.5, "稳健"), (1.2, "尚可"), (1.0, "偏紧")),
        "紧张",
    ),
    MarketMetric.DEBT_TO_EQUITY: _lower(
        # The source reports this as a percentage, so 100 means debt equals equity.
        ((30.0, "很低"), (60.0, "偏低"), (100.0, "中等"), (200.0, "偏高")),
        "很高",
        negative_means_absent=True,
    ),
    # --- The environment the asset is judged in ------------------------------
    MarketMetric.MARKET_DIRECTION: _higher(
        ((0.20, "明显上行"), (0.10, "上行"), (0.03, "基本持平"), (-0.03, "走弱")),
        "明显走弱",
    ),
    # --- What the price has actually been doing ------------------------------
    MarketMetric.TREND_MA20_GAP: _higher(
        ((0.05, "明显上方"), (0.0, "上方"), (-0.03, "小幅下方"), (-0.08, "下方")),
        "明显下方",
    ),
    MarketMetric.TREND_MA60_GAP: _higher(
        ((0.05, "明显上方"), (0.0, "上方"), (-0.03, "小幅下方"), (-0.08, "下方")),
        "明显下方",
    ),
    MarketMetric.TREND_MA120_GAP: _higher(
        ((0.08, "明显上方"), (0.02, "上方"), (-0.05, "接近均线"), (-0.12, "下方")),
        "明显下方",
    ),
    MarketMetric.TREND_MACD: _higher(
        ((0.010, "明显转强"), (0.0, "偏强"), (-0.010, "转弱"), (-0.030, "明显转弱")),
        "很弱",
    ),
    MarketMetric.TREND_RSI: _higher(
        ((60.0, "强势"), (50.0, "偏强"), (40.0, "中性"), (30.0, "偏弱")),
        "弱势",
    ),
    MarketMetric.TREND_VOLUME_RATIO: _higher(
        ((0.30, "明显放大"), (0.10, "略微放大"), (-0.10, "接近均值"), (-0.30, "萎缩")),
        "明显萎缩",
    ),
    MarketMetric.TREND_RANGE_POSITION: _higher(
        ((0.8, "接近高位"), (0.6, "中高位"), (0.4, "中位"), (0.2, "中低位")),
        "接近低位",
    ),
    MarketMetric.TREND_DIRECTION: _higher(
        ((0.20, "明显上行"), (0.10, "上行"), (0.03, "基本持平"), (-0.03, "走弱")),
        "明显走弱",
    ),
    # --- What could make this judgement wrong, and how badly -----------------
    MarketMetric.BETA: _lower(
        ((0.8, "很低"), (1.0, "偏低"), (1.3, "中等"), (1.8, "偏高")),
        "很高",
        read_absolute=True,
    ),
    MarketMetric.RISK_VOLATILITY: _lower(
        ((0.20, "温和"), (0.30, "偏温和"), (0.45, "偏高"), (0.70, "明显偏高")),
        "极高",
    ),
    MarketMetric.RISK_DRAWDOWN: _higher(
        ((-0.05, "很小"), (-0.10, "较小"), (-0.20, "中等"), (-0.35, "较大")),
        "很大",
    ),
    # --- What the reported results said, and what is expected next -----------
    MarketMetric.EARNINGS_GROWTH: _higher(
        ((0.30, "强劲"), (0.15, "明显改善"), (0.05, "小幅改善"), (0.0, "持平")),
        "下滑",
    ),
    MarketMetric.EXPECTED_EARNINGS_CHANGE: _higher(
        ((0.30, "强劲"), (0.15, "明显改善"), (0.05, "小幅改善"), (0.0, "持平")),
        "下滑",
    ),
    # --- Who else holds this asset, and how crowded that is ------------------
    MarketMetric.SHORT_PERCENT_OF_FLOAT: _lower(
        ((0.02, "很低"), (0.05, "偏低"), (0.10, "中性"), (0.20, "偏重")),
        "很重",
    ),
    MarketMetric.SHORT_RATIO: _lower(
        ((1.0, "很低"), (2.0, "偏低"), (4.0, "中等"), (7.0, "偏高")),
        "很高",
    ),
    # A holding is described and not judged: a large institutional position is not
    # a better one, and neither is a small insider stake. These scales carry words
    # and no score, so they are read by a sentence and never by a grade.
    MarketMetric.INSTITUTIONAL_OWNERSHIP: _higher(
        ((0.60, "机构为主"), (0.40, "机构较多"), (0.20, "机构与个人共同持有")),
        "机构参与度低",
        graded=False,
    ),
    MarketMetric.INSIDER_OWNERSHIP: _higher(
        ((0.10, "管理层持股较重"), (0.03, "管理层有持股")),
        "管理层持股很少",
        graded=False,
    ),
}


def scale_for(metric: MarketMetric) -> MetricScale | None:
    """Return the scale a measurement is read against, or None when it has none.

    A measurement with no scale is not read at all: it is carried as a fact and
    nothing is claimed about whether it is good.
    """
    return SCALES.get(metric)


def band_for(metric: MarketMetric, value: float) -> Band | None:
    """Return the band a reading falls in, or None when the measurement has no scale.

    Args:
        metric: Measurement being read.
        value: The value that was retrieved.

    Returns:
        The band the reading falls in. A reading that reaches none of the bands
        comes back as one carrying the scale's worst wording, so that a caller
        never has to decide what an off-scale reading is called.
    """
    scale = SCALES.get(metric)
    if scale is None:
        return None
    value = abs(value) if scale.read_absolute else value
    if scale.negative_means_absent and value < 0:
        return Band(threshold=value, word=scale.below_word)
    for band in scale.bands:
        if scale.direction is Direction.LOWER_IS_BETTER:
            if value <= band.threshold:
                return band
        elif value >= band.threshold:
            return band
    return Band(threshold=value, word=scale.below_word)


def score_for(metric: MarketMetric, value: float) -> int | None:
    """Return how one reading scores, or None when it is not scored.

    The score is the position of the band and not a judgement of its own: the best
    band scores five and a reading that reaches no band scores one. A scale that
    only describes has no score at all.

    Args:
        metric: Measurement being read.
        value: The value that was retrieved.

    Returns:
        A score from one to five, or None when this measurement is not graded.
    """
    scale = SCALES.get(metric)
    if scale is None or not scale.graded:
        return None
    band = band_for(metric, value)
    if band is None:
        return None
    for index, candidate in enumerate(scale.bands):
        if candidate == band:
            return MAX_SCORE - index
    return MIN_SCORE
