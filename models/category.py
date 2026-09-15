"""AIS category domain concept.

Categories are the fixed set of angles from which an asset is assessed.
The set is defined by the AIS Constitution and must not be extended or
renamed without approval.

Presentation order is a separate concern from membership and is defined here as
:data:`CATEGORY_ORDER`, so that every renderer orders the categories the same
way. Membership order in the enumeration is an implementation detail and must
never be relied on for presentation.
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


# The canonical order in which every AIS renderer presents the categories. It is
# defined explicitly rather than taken from the enumeration, so that reordering
# the enumeration can never silently reorder a report.
CATEGORY_ORDER: tuple[Category, ...] = (
    Category.HPO,
    Category.MARKET,
    Category.FUNDAMENTAL,
    Category.VALUATION,
    Category.EARNINGS,
    Category.TREND,
    Category.RISK,
    Category.CATALYST,
    Category.POSITIONING,
)
