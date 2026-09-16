"""Tests for the provisional category grade.

The grade is what an investor sees instead of a category score. These tests
describe what each measurement reads at, and, most importantly, that a
degenerate reading never reads as a good one.
"""

from __future__ import annotations

import pytest

from analysis.category_grade import MAX_GRADE, MIN_GRADE, _reading_of, stars
from contracts.market_data_provider import MarketMetric


def test_a_low_multiple_reads_better_than_a_high_one() -> None:
    assert _reading_of(MarketMetric.PE, 10.0) == 5
    assert _reading_of(MarketMetric.PE, 16.0) == 4
    assert _reading_of(MarketMetric.PE, 22.0) == 3
    assert _reading_of(MarketMetric.PE, 30.0) == 2
    assert _reading_of(MarketMetric.PE, 90.0) == 1


def test_a_higher_margin_reads_better_than_a_lower_one() -> None:
    assert _reading_of(MarketMetric.PROFIT_MARGIN, 0.30) == 5
    assert _reading_of(MarketMetric.PROFIT_MARGIN, 0.15) == 4
    assert _reading_of(MarketMetric.PROFIT_MARGIN, 0.08) == 3
    assert _reading_of(MarketMetric.PROFIT_MARGIN, 0.04) == 2
    assert _reading_of(MarketMetric.PROFIT_MARGIN, 0.01) == 1


def test_a_negative_ratio_never_reads_as_cheap() -> None:
    # A negative enterprise value to EBITDA means there is no EBITDA to measure
    # against. Reading it as a very low multiple would call it the cheapest
    # thing on the list.
    assert _reading_of(MarketMetric.EV_EBITDA, -238.22) == MIN_GRADE
    assert _reading_of(MarketMetric.PE, -12.0) == MIN_GRADE
    assert _reading_of(MarketMetric.PEG, -0.4) == MIN_GRADE


def test_negative_owners_equity_reads_as_the_worst_case() -> None:
    assert _reading_of(MarketMetric.DEBT_TO_EQUITY, -50.0) == MIN_GRADE


def test_a_negative_margin_reads_as_the_worst_case() -> None:
    assert _reading_of(MarketMetric.PROFIT_MARGIN, -0.215) == MIN_GRADE
    assert _reading_of(MarketMetric.RETURN_ON_EQUITY, -0.079) == MIN_GRADE
    assert _reading_of(MarketMetric.FREE_CASH_FLOW_MARGIN, -0.328) == MIN_GRADE


def test_beta_is_read_by_how_far_it_moves_not_by_which_way() -> None:
    assert _reading_of(MarketMetric.BETA, 2.61) == MIN_GRADE
    assert _reading_of(MarketMetric.BETA, -2.61) == MIN_GRADE
    assert _reading_of(MarketMetric.BETA, 0.7) == MAX_GRADE


def test_a_measurement_with_no_bands_is_not_graded() -> None:
    assert _reading_of(MarketMetric.AVERAGE_VOLUME, 50_000_000.0) is None
    assert _reading_of(MarketMetric.FLOAT_SHARES, 2_500_000_000.0) is None


def test_a_missing_value_is_not_graded() -> None:
    assert _reading_of(MarketMetric.PE, None) is None


@pytest.mark.parametrize(
    ("grade", "expected"),
    [
        (5, "★★★★★"),
        (4, "★★★★☆"),
        (3, "★★★☆☆"),
        (1, "★☆☆☆☆"),
    ],
)
def test_stars_show_the_grade_out_of_five(grade: int, expected: str) -> None:
    assert stars(grade) == expected


def test_stars_never_leave_the_scale() -> None:
    assert stars(0) == "★☆☆☆☆"
    assert stars(9) == "★★★★★"
