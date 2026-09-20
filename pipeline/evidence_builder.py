"""AIS evidence builder.

Builds an EvidenceCollection for an asset. The pipeline is deterministic and
performs no evaluation, scoring, or I/O: market data is handed in already
retrieved, and this module only turns it into evidence.

Three kinds of evidence are produced:

* one placeholder item per category, kept so that a collection built without a
  market data source stays complete and deterministic;
* one item per market metric when a snapshot is supplied, whether the metric was
  retrieved or not, so that a metric a source could not provide is recorded with
  the reason it is missing instead of silently disappearing;
* one item per environment measurement when one is supplied. The environment is not
  about this asset — it is the same for every asset in the pass — and it is filed
  under the same category and read through the same reading layer as everything
  else. Only its identifier differs, because it belongs to no ticker.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, time

from contracts.catalyst_event_provider import (
    CATALYST_EVIDENCE_ID,
    CONFIRMED_METADATA_KEY,
    DATE_METADATA_KEY,
    DESCRIPTION_METADATA_KEY,
    KIND_METADATA_KEY,
    SCOPE_METADATA_KEY,
    SOURCE_METADATA_KEY,
    SYMBOL_METADATA_KEY,
)
from contracts.market_data_provider import (
    MARKET_EVIDENCE_ID,
    METRIC_METADATA_KEY,
    VALUE_METADATA_KEY,
    MarketDataSnapshot,
)
from contracts.market_environment import (
    ENVIRONMENT_EVIDENCE_ID,
    EnvironmentSnapshot,
)
from evidence.evidence_collection import EvidenceCollection
from evidence.evidence_item import EvidenceItem
from evidence.evidence_source import EvidenceSource
from models.asset import Asset
from models.catalyst_event import CatalystEvent
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

# A catalyst event is a fact a source states, so its evidence is fully trusted.
# Whether the source presents the date as settled is carried as metadata instead
# of being turned into a confidence, because how much less a rumoured date can be
# trusted is a judgement and not a number this layer may invent.
_EVENT_CONFIDENCE = 1.0


class EvidenceBuilder:
    """Builds an EvidenceCollection for an asset."""

    def __init__(self) -> None:
        """Create the builder with a default evidence factory."""
        self._factory = EvidenceFactory()

    def build(
        self,
        asset: Asset,
        market_data: MarketDataSnapshot | None = None,
        events: Sequence[CatalystEvent] = (),
        environment: EnvironmentSnapshot | None = None,
    ) -> EvidenceCollection:
        """Build evidence for the asset.

        Args:
            asset: Asset to build evidence for.
            market_data: Market data retrieved for the asset, or None when no
                market data source was consulted.
            events: Dated catalyst events retrieved for the asset, in the order
                they should be recorded.
            environment: The environment the asset is being judged in, or None when
                none was retrieved. It is the same object for every asset in a pass.

        Returns:
            EvidenceCollection holding one placeholder item per category, plus one
            item per market metric when a snapshot was supplied, plus one item per
            catalyst event, plus one item per environment measurement.
        """
        items = [*self._placeholder_items(asset)]
        if market_data is not None:
            items.extend(self._market_data_items(asset, market_data))
        if environment is not None:
            items.extend(self._environment_items(environment))
        items.extend(self._event_items(asset, events))
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
                id=MARKET_EVIDENCE_ID.format(
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

    def _environment_items(
        self, environment: EnvironmentSnapshot
    ) -> tuple[EvidenceItem, ...]:
        """Return one item per environment measurement, retrieved or not.

        The item carries no ticker in its identifier, because the fact is not about
        one: the same evidence is filed for every asset in the pass, which is what
        it means for the market's measurements to be shared. The source is recorded
        as market data, since that is what it is; what makes it different is whose
        measurements they are.
        """
        return tuple(
            self._factory.create(
                id=ENVIRONMENT_EVIDENCE_ID.format(metric=point.metric.value),
                category=point.metric.primary_category,
                title=f"{environment.source}: {point.metric.label}",
                description=point.reason,
                source=EvidenceSource.MARKET_DATA,
                timestamp=environment.retrieved_at,
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
            for point in environment.points
        )

    def _event_items(
        self, asset: Asset, events: Sequence[CatalystEvent]
    ) -> tuple[EvidenceItem, ...]:
        """Return one item per catalyst event.

        An event is recorded as evidence because it is the ground a catalyst
        judgement stands on, and every judgement must be traceable to what it
        was made from. The item carries the event's own date rather than the
        moment it was retrieved: the date is the fact, and when AIS happened to
        read it is not.
        """
        seen: dict[str, int] = {}
        items: list[EvidenceItem] = []
        for event in events:
            base = CATALYST_EVIDENCE_ID.format(
                ticker=asset.ticker, kind=event.kind.value, date=event.occurs_on
            )
            seen[base] = seen.get(base, 0) + 1
            suffix = "" if seen[base] == 1 else f".{seen[base]}"
            items.append(
                self._factory.create(
                    id=f"{base}{suffix}",
                    category=Category.CATALYST,
                    title=f"{event.source}: {event.description}",
                    description=(
                        f"{event.description} on {event.occurs_on}, reported by "
                        f"{event.source}"
                        + ("." if event.confirmed else ", not confirmed.")
                    ),
                    source=EvidenceSource.CALENDAR,
                    timestamp=datetime.combine(event.occurs_on, time.min),
                    confidence=_EVENT_CONFIDENCE,
                    metadata={
                        KIND_METADATA_KEY: event.kind.value,
                        SCOPE_METADATA_KEY: event.scope.value,
                        DATE_METADATA_KEY: event.occurs_on.isoformat(),
                        SOURCE_METADATA_KEY: event.source,
                        CONFIRMED_METADATA_KEY: "true" if event.confirmed else "false",
                        DESCRIPTION_METADATA_KEY: event.description,
                        SYMBOL_METADATA_KEY: event.symbol or "",
                    },
                )
            )
        return tuple(items)
