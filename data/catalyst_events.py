"""AIS catalyst event provider selection.

The single place in AIS that decides which catalyst event sources the system
reads. Nothing outside the Data layer names one, and every other component
depends on the :class:`~contracts.catalyst_event_provider.CatalystEventProvider`
contract alone.

Three sources are combined, and each answers a different part of the calendar:

* **A market data vendor** — what a company has scheduled: results, ex-dividend
  and dividend dates. This is the only company calendar any connected source
  publishes.
* **A central bank** — the published meeting schedule, which is macro by nature
  and is not specific to a symbol.
* **A curated file** — events a person has entered, for everything no source
  publishes.

The sources are additive: one that answers nothing does not stop the others, and
an event is never merged with another. Two sources reporting the same date
produce two events, because AIS has no basis for deciding they are the same
thing.
"""

from __future__ import annotations

from collections.abc import Iterable

from config.config import Config
from contracts.catalyst_event_provider import CatalystEventProvider
from data.curated_catalyst_calendar import CuratedCatalystEventProvider
from data.federal_reserve_event_provider import FederalReserveEventProvider
from data.yahoo_market_data_provider import YahooMarketDataProvider
from models.catalyst_event import CatalystEvent


class CompositeCatalystEventProvider:
    """Reads every configured source and returns the events they report."""

    def __init__(self, providers: Iterable[CatalystEventProvider]) -> None:
        """Create the provider over the sources it should read.

        Args:
            providers: Sources to read, in the order they are read.
        """
        self._providers = tuple(providers)

    def fetch_events(self, symbol: str) -> tuple[CatalystEvent, ...]:
        """Return the events every source reports for a symbol.

        Args:
            symbol: Trading symbol the events are requested for.

        Returns:
            The events, ordered by date. A source that reports nothing
            contributes nothing.
        """
        events = [
            event
            for provider in self._providers
            for event in provider.fetch_events(symbol)
        ]
        return tuple(sorted(events, key=lambda event: (event.occurs_on, event.kind)))


def build_catalyst_event_provider() -> CatalystEventProvider:
    """Return the catalyst event provider AIS uses.

    The return type is the contract rather than the implementation, so that a
    caller cannot depend on anything vendor specific.

    Returns:
        The provider AIS reads dated events from.
    """
    return CompositeCatalystEventProvider(
        (
            YahooMarketDataProvider(),
            FederalReserveEventProvider(),
            CuratedCatalystEventProvider(
                Config.from_environment().catalyst_calendar_file
            ),
        )
    )
