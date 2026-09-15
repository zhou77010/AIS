"""Contract for evidence providers.

An evidence provider is a single evidence source that collects evidence items
for an asset. It never assembles the final collection. This module defines the
interface only and holds no implementation.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from evidence.evidence_item import EvidenceItem
from models.asset import Asset


class EvidenceProvider(Protocol):
    """Contract for a single evidence source."""

    def collect(self, asset: Asset) -> Iterable[EvidenceItem]:
        """Collect evidence items for an asset.

        Args:
            asset: Asset to collect evidence about.

        Returns:
            Evidence items collected for the asset.
        """
