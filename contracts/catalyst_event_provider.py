"""Contract for catalyst event providers.

A catalyst event provider is any source of dated events that could change the
investment case for an asset: a market data vendor's calendar, a central bank's
published meeting schedule, a curated list maintained by hand.

**A provider returns facts and classifies nothing.** It reports what kind of
event it is and when it falls. Whether that event bears on the company, on its
industry or on the conditions everything is valued under is AIS's reading, made
in one table in :mod:`models.catalyst_event`. A provider that decided it would be
making a judgement, and this layer returns observations.

**A provider never raises and never invents a date.** A source that cannot be
reached, or that answers with something unreadable, returns no events, and the
category reports that it found nothing rather than filling the gap.
"""

from __future__ import annotations

from typing import Protocol

from models.catalyst_event import CatalystEvent

# Keys used in the metadata of the evidence items that carry a catalyst event.
# They are defined once, here, because the pipeline writes them and the catalyst
# rules read them, and neither may invent its own spelling.
KIND_METADATA_KEY = "catalyst_kind"
SCOPE_METADATA_KEY = "catalyst_scope"
DATE_METADATA_KEY = "catalyst_date"
SOURCE_METADATA_KEY = "catalyst_source"
CONFIRMED_METADATA_KEY = "catalyst_confirmed"
DESCRIPTION_METADATA_KEY = "catalyst_description"
SYMBOL_METADATA_KEY = "catalyst_symbol"

# How the evidence for one event is identified, spelled the same way here as it
# is written by the pipeline, so that an insight can point back at the event it
# was read from.
CATALYST_EVIDENCE_ID = "{ticker}.catalyst.{kind}.{date}"


class CatalystEventProvider(Protocol):
    """Contract for any source of dated catalyst events."""

    def fetch_events(self, symbol: str) -> tuple[CatalystEvent, ...]:
        """Return the events the source knows about for a symbol.

        Args:
            symbol: Trading symbol the events are requested for. A provider of
                events that are not specific to one asset ignores it.

        Returns:
            The events retrieved, possibly none. An implementation never raises
            and never invents a date.
        """
