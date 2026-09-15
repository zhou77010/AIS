"""AIS risk profile domain models.

A risk profile describes how risky an asset is and which risks drive that.
It is a description, never a measurement procedure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RiskLevel(StrEnum):
    """Level of risk carried by an asset."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass(frozen=True)
class RiskProfile:
    """Descriptive risk characteristics of an asset.

    Attributes:
        level: Overall risk level.
        summary: Short explanation of the risk level.
        key_risks: Named risks that drive the level.
    """

    level: RiskLevel
    summary: str
    key_risks: tuple[str, ...]
