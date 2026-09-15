"""AIS evidence factory.

Creates EvidenceItem objects from their parts. It performs no evaluation and
no calculations.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from evidence.evidence_item import EvidenceItem
from evidence.evidence_source import EvidenceSource
from models.category import Category


class EvidenceFactory:
    """Creates EvidenceItem objects."""

    def create(
        self,
        *,
        id: str,
        category: Category,
        title: str,
        description: str,
        source: EvidenceSource,
        timestamp: datetime,
        confidence: float,
        metadata: Mapping[str, str],
    ) -> EvidenceItem:
        """Create an EvidenceItem from its parts.

        Args:
            id: Identifier of the item.
            category: Category the evidence belongs to.
            title: Short name of the evidence.
            description: What the evidence states.
            source: Origin the evidence came from.
            timestamp: Moment the evidence was captured.
            confidence: Confidence in the evidence, from 0.0 to 1.0.
            metadata: Source specific extra information.

        Returns:
            The created EvidenceItem.
        """
        return EvidenceItem(
            id=id,
            category=category,
            title=title,
            description=description,
            source=source,
            timestamp=timestamp,
            confidence=confidence,
            metadata=metadata,
        )
