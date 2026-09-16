"""Tests for the coverage model.

Coverage answers how much of a category was assessed. It is what stops a score
from being read as a statement about a whole category when only part of it was
examined.
"""

from __future__ import annotations

import pytest

from models.coverage import Coverage
from utils.exceptions import ValidationError


def test_coverage_reports_how_much_of_a_category_was_assessed() -> None:
    coverage = Coverage(assessed=3, total=8)

    assert coverage.assessed == 3
    assert coverage.total == 8
    assert coverage.describe() == "3/8"
    assert coverage.is_complete is False


def test_coverage_is_complete_only_when_every_unit_was_assessed() -> None:
    assert Coverage(assessed=5, total=5).is_complete is True
    assert Coverage(assessed=0, total=5).is_complete is False


def test_coverage_accepts_a_category_nothing_was_assessed_in() -> None:
    coverage = Coverage(assessed=0, total=8)

    assert coverage.assessed == 0
    assert coverage.is_complete is False


def test_coverage_rejects_a_category_with_no_units() -> None:
    with pytest.raises(ValidationError, match="at least one unit"):
        Coverage(assessed=0, total=0)


def test_coverage_rejects_more_assessed_than_the_category_has() -> None:
    with pytest.raises(ValidationError, match="between 0 and total"):
        Coverage(assessed=6, total=5)


def test_coverage_rejects_a_negative_count() -> None:
    with pytest.raises(ValidationError, match="between 0 and total"):
        Coverage(assessed=-1, total=5)
