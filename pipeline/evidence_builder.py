"""AIS evidence builder.

Builds an EvidenceCollection for an asset. The pipeline is deterministic and
performs no evaluation, scoring, or I/O: market data is handed in already
retrieved, and this module only turns it into evidence.

Two kinds of evidence are produced:

* one placeholder item per category, kept so that a collection built without a
  market data source stays complete and deterministic;
* one item per market metric when a snapshot is supplied, whether the metric was
  retrieved or not, so that a metric a source could not provide is recorded with
  the reason it is missing instead of silently disappearing.
"""

from __future__ import annotations

from datetime import datetime

from contracts.market_data_provider import (
    METRIC_METADATA_KEY,
    VALUE_METADATA_KEY,
    MarketDataSnapshot,
)
from evidence.evidence_collection import EvidenceCollection
from evidence.evidence_item import EvidenceItem
from evidence.evidence_source import EvidenceSource
from models.asset import Asset
from models.category import Category
from pipeline.evidence_factory import EvidenceFactory

# Placeholder evidence is deterministic and therefore fully reliable; real
# providers determine confidence dynamically. The fixed timestamp keeps the
# pipeline deterministic.
_PLACEHOLDER_CONFIDENCE = 1.0
_PLACEHOLDER_TIMESTAMP = datetime(2000, 1, 1)

# A retrieved market metric is a fact reported by a source, so its evidence is
# fully trusted; a metric the source could not provide carries no confidence.
_MARKET_DATA_CONFIDENCE = 1.0
_MISSING_MARKET_DATA_CONFIDENCE = 0.0

_MARKET_DATA_ID = "{ticker}.market_data.{metric}"


class EvidenceBuilder:
    """Builds an EvidenceCollection for an asset."""

    def __init__(self) -> None:
        """Create the builder with a default evidence factory."""
        self._factory = EvidenceFactory()

    def build(
        self,
        asset: Asset,
        market_data: MarketDataSnapshot | None = None,
    ) -> EvidenceCollection:
        """Build evidence for the asset.

        Args:
            asset: Asset to build evidence for.
            market_data: Market data retrieved for the asset, or None when no
                market data source was consulted.

        Returns:
            EvidenceCollection holding one placeholder item per category, plus
            one item per market metric when a snapshot was supplied.
        """
        items = [*self._placeholder_items(asset)]
        if market_data is not None:
            items.extend(self._market_data_items(asset, market_data))
        return EvidenceCollection(asset=asset, items=tuple(items))

    def _placeholder_items(self, asset: Asset) -> tuple[EvidenceItem, ...]:
        """Return one placeholder item per category."""
        return tuple(
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

    def _market_data_items(
        self, asset: Asset, market_data: MarketDataSnapshot
    ) -> tuple[EvidenceItem, ...]:
        """Return one item per metric of the snapshot, retrieved or not."""
        return tuple(
            self._factory.create(
                id=_MARKET_DATA_ID.format(
                    ticker=asset.ticker, metric=point.metric.value
                ),
                category=point.metric.primary_category,
                title=f"{market_data.source}: {point.metric.label}",
                description=point.reason,
                source=EvidenceSource.MARKET_DATA,
                timestamp=market_data.retrieved_at,
                confidence=(
                    _MARKET_DATA_CONFIDENCE
                    if point.value is not None
                    else _MISSING_MARKET_DATA_CONFIDENCE
                ),
                metadata={
                    METRIC_METADATA_KEY: point.metric.value,
                    VALUE_METADATA_KEY: (
                        "" if point.value is None else repr(point.value)
                    ),
                },
            )
            for point in market_data.points
        )
