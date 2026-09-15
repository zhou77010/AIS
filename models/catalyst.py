"""AIS catalyst domain models.

A catalyst is an event expected to change how an asset is assessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class CatalystStatus(StrEnum):
    """Lifecycle status of a catalyst."""

    PLANNED = "planned"
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Catalyst:
    """Event expected to change how an asset is assessed.

    Attributes:
        title: Short name of the catalyst.
        expected_date: Date the catalyst is expected to occur, or None when no
            exact date is known.
        expected_impact: Description of the impact expected on the assessment.
        confidence: Confidence in the catalyst, from 0.0 to 1.0.
        status: Lifecycle status of the catalyst.
    """

    title: str
    expected_date: date | None
    expected_impact: str
    confidence: float
    status: CatalystStatus
