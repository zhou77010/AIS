"""AIS evidence collection domain model.

An evidence collection gathers the evidence held for one asset.
"""

from __future__ import annotations

from dataclasses import dataclass

from evidence.evidence_item import EvidenceItem
from models.asset import Asset


@dataclass(frozen=True)
class EvidenceCollection:
    """All evidence held for one asset.

    Attributes:
        asset: Asset the evidence is about.
        items: Evidence items held for the asset.
    """

    asset: Asset
    items: tuple[EvidenceItem, ...]
