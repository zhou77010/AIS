"""AIS normalized score.

A normalized score is one metric after it has been converted into the AIS
standard scale. The conversion itself is the normalizer's responsibility; this
model only carries the outcome.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedScore:
    """One metric expressed on the AIS standard scale.

    Attributes:
        raw_value: Value the metric had before normalization.
        normalized_value: Value of the metric on the standard scale.
        confidence: Confidence in the normalized value, from 0.0 to 1.0.
        reason: Human readable explanation carried from the source metric.
        evidence_references: Identifiers of the evidence behind the metric.
    """

    raw_value: float
    normalized_value: float
    confidence: float
    reason: str
    evidence_references: tuple[str, ...] = ()
