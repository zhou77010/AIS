"""AIS evidence level concept.

The evidence level states how strong a piece of evidence is in qualitative
terms. It is a label, not a measurement.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceLevel(StrEnum):
    """Qualitative strength of a piece of evidence."""

    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
