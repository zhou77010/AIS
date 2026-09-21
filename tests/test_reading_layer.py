"""Tests for the reading layer.

The reading layer is the single owner of what a number means. These tests describe
what each measurement reads at, and — most importantly — that a degenerate reading
never reads as a good one. A negative enterprise value to EBITDA means there is
nothing to measure against, not that the asset is the cheapest thing on the list,
and a report that said otherwise would be stating the opposite of the truth.
"""

from __future__ import annotations

import pytest

from contracts.market_data_provider import MarketMetric
from evaluation.reading.bands import (
    MAX_SCORE,
    MIN_SCORE,
    SCALES,
    Direction,
    band_for,
    scale_for,
    score_for,
)

_ALL_METRICS = tuple(MarketMetric)

# The measurements no source publishes, so there is no number for a scale to read.
# They are carried as facts with the reason they are absent, and a scale for them
# would describe a value that never arrives.
_NEVER_RETRIEVED = (MarketMetric.DCF, MarketMetric.EARNINGS_GUIDANCE)


def test_a_low_multiple_reads_better_than_a_high_one() -> None:
    assert score_for(MarketMetric.PE, 10.0) == 5
    assert score_for(MarketMetric.PE, 16.0) == 4
    assert score_for(MarketMetric.PE, 22.0) == 3
    assert score_for(MarketMetric.PE, 30.0) == 2
    assert score_for(MarketMetric.PE, 90.0) == 1


def test_a_higher_margin_reads_better_than_a_lower_one() -> None:
    assert score_for(MarketMetric.PROFIT_MARGIN, 0.30) == 5
    assert score_for(MarketMetric.PROFIT_MARGIN, 0.15) == 4
    assert score_for(MarketMetric.PROFIT_MARGIN, 0.08) == 3
    assert score_for(MarketMetric.PROFIT_MARGIN, 0.04) == 2
    assert score_for(MarketMetric.PROFIT_MARGIN, 0.01) == 1


def test_a_negative_ratio_never_reads_as_cheap() -> None:
    assert score_for(MarketMetric.EV_EBITDA, -238.22) == MIN_SCORE
    assert score_for(MarketMetric.PE, -12.0) == MIN_SCORE
    assert score_for(MarketMetric.PEG, -0.4) == MIN_SCORE


def test_negative_owners_equity_reads_as_the_worst_case() -> None:
    assert score_for(MarketMetric.DEBT_TO_EQUITY, -50.0) == MIN_SCORE


def test_a_negative_margin_reads_as_the_worst_case() -> None:
    assert score_for(MarketMetric.PROFIT_MARGIN, -0.215) == MIN_SCORE
    assert score_for(MarketMetric.RETURN_ON_EQUITY, -0.079) == MIN_SCORE
    assert score_for(MarketMetric.FREE_CASH_FLOW_MARGIN, -0.328) == MIN_SCORE


def test_beta_is_read_by_how_far_it_moves_not_by_which_way() -> None:
    assert score_for(MarketMetric.BETA, 2.61) == MIN_SCORE
    assert score_for(MarketMetric.BETA, -2.61) == MIN_SCORE
    assert score_for(MarketMetric.BETA, 0.7) == MAX_SCORE


def test_a_measurement_with_no_scale_is_not_read_at_all() -> None:
    assert scale_for(MarketMetric.AVERAGE_VOLUME) is None
    assert score_for(MarketMetric.AVERAGE_VOLUME, 50_000_000.0) is None
    assert band_for(MarketMetric.FLOAT_SHARES, 2_500_000_000.0) is None
    assert score_for(MarketMetric.DCF, 1.0) is None


# --------------------------------------------------------------------------
# One scale per measurement, and a word for every band
# --------------------------------------------------------------------------


def test_every_scored_measurement_has_a_scale() -> None:
    # A measurement the evaluators grade but the reading layer does not know about
    # would be graded by a second, invisible table.
    unscaled = [
        metric
        for metric in _ALL_METRICS
        if metric not in _NEVER_RETRIEVED and scale_for(metric) is None
    ]

    assert unscaled == [MarketMetric.AVERAGE_VOLUME, MarketMetric.FLOAT_SHARES]


def test_every_band_carries_a_word() -> None:
    for metric, scale in SCALES.items():
        assert scale.below_word, metric
        for band in scale.bands:
            assert band.word, (metric, band)
            assert band.word != scale.below_word, (metric, band)


def test_a_scale_runs_five_deep_at_most() -> None:
    for metric, scale in SCALES.items():
        assert 1 <= len(scale.bands) <= MAX_SCORE - 1, metric


def test_the_direction_of_a_scale_is_declared_not_inferred() -> None:
    assert SCALES[MarketMetric.PE].direction is Direction.LOWER_IS_BETTER
    assert SCALES[MarketMetric.PROFIT_MARGIN].direction is Direction.HIGHER_IS_BETTER


def test_a_described_measurement_has_a_word_and_no_score() -> None:
    # A large institutional holding is not a better one, so the scale describes it
    # and does not grade it.
    assert score_for(MarketMetric.INSTITUTIONAL_OWNERSHIP, 0.66) is None
    assert band_for(MarketMetric.INSTITUTIONAL_OWNERSHIP, 0.66) is not None
    assert band_for(MarketMetric.INSTITUTIONAL_OWNERSHIP, 0.66).word == "机构为主"


# --------------------------------------------------------------------------
# The words match the bands
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("metric", "value", "word"),
    [
        (MarketMetric.RISK_VOLATILITY, 0.60, "明显偏高"),
        (MarketMetric.RISK_VOLATILITY, 0.40, "偏高"),
        (MarketMetric.RISK_VOLATILITY, 0.20, "温和"),
        (MarketMetric.PE, 10.0, "很便宜"),
        (MarketMetric.PE, 90.0, "很贵"),
        (MarketMetric.FREE_CASH_FLOW_MARGIN, -0.10, "为负"),
        (MarketMetric.TREND_MA20_GAP, 0.06, "明显上方"),
    ],
)
def test_a_reading_is_described_by_the_band_it_falls_in(
    metric: MarketMetric, value: float, word: str
) -> None:
    assert band_for(metric, value).word == word


def test_a_reading_below_every_band_is_described_as_the_worst() -> None:
    assert (
        band_for(MarketMetric.PROFIT_MARGIN, -0.5).word
        == SCALES[MarketMetric.PROFIT_MARGIN].below_word
    )
