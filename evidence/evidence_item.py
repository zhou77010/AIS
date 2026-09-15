"""AIS evidence item domain model.

An evidence item is a single, traceable fact about an asset: what it states,
where it came from, when it was captured, and how much confidence it carries.
It states no evaluation of the asset.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from evidence.evidence_source import EvidenceSource
from models.category import Category


@dataclass(frozen=True)
class EvidenceItem:
    """Single piece of evidence about an asset.

    Attributes:
        id: Identifier of the item, unique within the collection it belongs to.
        category: Category the evidence belongs to.
        title: Short name of the evidence.
        description: What the evidence states.
        source: Origin the evidence came from.
        timestamp: Moment the evidence was captured.
        confidence: Confidence in the evidence, from 0.0 to 1.0.
        metadata: Source specific extra information.
    """

    id: str
    category: Category
    title: str
    description: str
    source: EvidenceSource
    timestamp: datetime
    confidence: float
    metadata: Mapping[str, str]
