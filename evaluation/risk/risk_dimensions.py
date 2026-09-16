"""The kinds of uncertainty a risk judgement is about.

These are the dimensions the Constitution fixes in its Section 5.2. The set is
closed: nothing here adds to it, removes from it, or renames its members.

A dimension is named for the uncertainty, never for a measurement. A measurement
is evidence for a dimension; it is never the dimension. Which evidence supports
which dimension is decided beside the rules that use it, and each rule declares
the dimension it serves.
"""

from __future__ import annotations

from enum import StrEnum


class RiskDimension(StrEnum):
    """A kind of uncertainty that can invalidate an investment thesis."""

    BUSINESS = "business"
    FINANCIAL = "financial"
    VALUATION = "valuation"
    MARKET = "market"
    EVENT = "event"
    LIQUIDITY = "liquidity"
    EVIDENCE = "evidence"
    HORIZON = "horizon"
