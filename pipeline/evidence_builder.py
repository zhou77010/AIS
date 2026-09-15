"""AIS evidence builder.

Builds an EvidenceCollection for an asset from placeholder evidence. The
pipeline is deterministic and performs no evaluation, scoring, or I/O.
"""

from __future__ import annotations

from datetime import datetime

from evidence.evidence_collection import EvidenceCollection
from evidence.evidence_source import EvidenceSource
from models.asset import Asset
from models.category import Category
from pipeline.evidence_factory import EvidenceFactory

# Placeholder evidence is deterministic and therefore fully reliable; real
# providers determine confidence dynamically. The fixed timestamp keeps the
# pipeline deterministic.
_PLACEHOLDER_CONFIDENCE = 1.0
_PLACEHOLDER_TIMESTAMP = datetime(2000, 1, 1)


class EvidenceBuilder:
    """Builds an EvidenceCollection for an asset."""

    def __init__(self) -> None:
        """Create the builder with a default evidence factory."""
        self._factory = EvidenceFactory()

    def build(self, asset: Asset) -> EvidenceCollection:
        """Build placeholder evidence for the asset.

        Args:
            asset: Asset to build evidence for.

        Returns:
            EvidenceCollection holding one placeholder item per category.
        """
        items = tuple(
            self._factory.create(
                id=f"{asset.ticker}.{category.value}",
                category=category,
                title=f"Placeholder {category.value} evidence",
                description=(
                    f"Placeholder evidence for {asset.name} "
                    f"in the {category.value} category."
                ),
                source=EvidenceSource.SYSTEM,
                timestamp=_PLACEHOLDER_TIMESTAMP,
                confidence=_PLACEHOLDER_CONFIDENCE,
                metadata={},
            )
            for category in Category
        )
        return EvidenceCollection(asset=asset, items=items)
