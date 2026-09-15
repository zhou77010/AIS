"""AIS evidence source concept.

The source states where a piece of evidence came from, so that every item can
be traced back to its origin.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceSource(StrEnum):
    """Origin a piece of evidence came from."""

    SEC = "sec"
    EARNINGS = "earnings"
    MARKET_DATA = "market_data"
    NEWS = "news"
    MACRO = "macro"
    MANUAL = "manual"
    SYSTEM = "system"
    UNKNOWN = "unknown"
