"""AIS decision state domain concept.

The decision state names the conclusion reached about an asset.
The member names are fixed by the AIS Constitution.
"""

from __future__ import annotations

from enum import StrEnum


class DecisionState(StrEnum):
    """Conclusion reached about an asset."""

    WATCH = "watch"
    ACCUMULATE = "accumulate"
    BUY = "buy"
    HOLD = "hold"
    TRIM = "trim"
    SELL = "sell"
    WAIT = "wait"
