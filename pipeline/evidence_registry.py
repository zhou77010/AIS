"""AIS evidence registry.

Provides category-based lookup of evidence. It performs no scoring.
"""

from __future__ import annotations

from evidence.evidence_collection import EvidenceCollection
from evidence.evidence_item import EvidenceItem
from models.category import Category


class EvidenceRegistry:
    """Category-based lookup over a collection of evidence."""

    def __init__(self, collection: EvidenceCollection) -> None:
        """Build a registry over the collection.

        Args:
            collection: Evidence to look up by category.
        """
        self._collection = collection

    def by_category(self, category: Category) -> tuple[EvidenceItem, ...]:
        """Return the evidence items that belong to the category.

        Args:
            category: Category to look up.

        Returns:
            Evidence items in the category, in collection order.
        """
        return tuple(
            item for item in self._collection.items if item.category == category
        )
