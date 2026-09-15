"""AIS category domain concept.

Categories are the fixed set of angles from which an asset is assessed.
The set is defined by the AIS Constitution and must not be extended or
renamed without approval.
"""

from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    """Assessment category, as defined by the AIS Constitution."""

    MARKET = "market"
    FUNDAMENTAL = "fundamental"
    VALUATION = "valuation"
    EARNINGS = "earnings"
    TREND = "trend"
    HPO = "hpo"
    RISK = "risk"
    CATALYST = "catalyst"
    POSITIONING = "positioning"
