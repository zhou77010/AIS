"""AIS asset profile domain concept.

The asset profile states which kind of instrument an asset is.
"""

from __future__ import annotations

from enum import StrEnum


class AssetProfile(StrEnum):
    """Kind of instrument an asset represents."""

    MATURE_TECH = "mature_tech"
    HIGH_GROWTH = "high_growth"
    FINANCIAL = "financial"
    CYCLICAL = "cyclical"
    ETF = "etf"
    UNKNOWN = "unknown"
