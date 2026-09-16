"""Federal Reserve event provider.

The Federal Reserve publishes its own meeting schedule, and a policy decision is
the clearest macro event there is: it moves the rate the whole market discounts
with, and it falls on a date known years ahead.

The provider reads the published calendar page and returns the meetings it can
read. It reports what the page says and nothing else: it does not interpret a
meeting, does not predict a decision, and does not add the other macro releases
AIS has no source for.

**It fails empty rather than wrong.** The page is prose for people, and a change
to its markup would silently produce nonsense if the reading were relaxed to keep
it working. Every guard below therefore discards the whole reading instead of
returning a partial one: no date AIS cannot stand behind is ever published as an
event.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from config.logging_config import get_logger
from data.http import HttpTransport, UrllibTransport
from models.catalyst_event import CatalystEvent, CatalystEventKind

SOURCE_NAME = "Federal Reserve"

_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
_LOGGER_NAME = "market_data"

# The Fed schedules eight meetings a year. Fewer than this from a year's section
# means the page was read wrongly, and a partly read calendar is worse than none.
_MIN_MEETINGS_PER_YEAR = 4
_MAX_YEARS_AHEAD = 2

_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

# One pass over the page in document order, matching whichever of the three
# things appears next: a year heading, a meeting's month, or its day span.
_TOKEN = re.compile(
    r">(\d{4}) FOMC Meetings<"
    r"|fomc-meeting__month[^>]*>(?:<strong>)?\s*([A-Z][a-z]+)"
    r"|fomc-meeting__date[^>]*>\s*(\d{1,2})(?:\s*[-\u2013]\s*(\d{1,2}))?"
)


class FederalReserveEventProvider:
    """Retrieves the published Federal Reserve meeting schedule."""

    def __init__(self, transport: HttpTransport | None = None) -> None:
        """Create the provider.

        Args:
            transport: Transport to talk through. Defaults to the standard
                library transport; tests supply a stand-in.
        """
        self._transport: HttpTransport = (
            transport if transport is not None else UrllibTransport()
        )
        self._logger = get_logger(_LOGGER_NAME)

    def fetch_events(self, symbol: str) -> tuple[CatalystEvent, ...]:
        """Return the scheduled meetings that are still ahead.

        The schedule is not specific to an asset, so the symbol is only used to
        attach the events to the asset being analysed.

        Args:
            symbol: Trading symbol the events are attached to.

        Returns:
            The forthcoming meetings, possibly none.
        """
        try:
            page = self._transport.get(_URL)
        except Exception as error:  # noqa: BLE001 - the contract is to never raise
            self._logger.warning(
                "meeting schedule unavailable from %s: %s",
                SOURCE_NAME,
                f"{type(error).__name__}: {error}",
            )
            return ()

        events = _meetings(page, symbol, datetime.now())
        if not events:
            self._logger.warning(
                "%s published a schedule that could not be read; no macro events "
                "were recorded",
                SOURCE_NAME,
            )
        return events


def _meetings(page: str, symbol: str, moment: datetime) -> tuple[CatalystEvent, ...]:
    """Return the meetings the published page states, or none when unreadable."""
    years: dict[int, list[date]] = {}
    year: int | None = None
    month: int | None = None

    for match in _TOKEN.finditer(page):
        heading, month_name, first_day, last_day = match.groups()
        if heading is not None:
            year = int(heading)
            month = None
            years.setdefault(year, [])
            continue
        if month_name is not None:
            month = _MONTHS.get(month_name)
            continue
        if year is None or month is None:
            continue
        # A meeting that spans two days decides on the second one, which is the
        # day the statement is published.
        day = int(last_day or first_day)
        try:
            years[year].append(date(year, month, day))
        except ValueError:
            return ()

    if not any(len(days) >= _MIN_MEETINGS_PER_YEAR for days in years.values()):
        return ()

    horizon = date(moment.year + _MAX_YEARS_AHEAD, 12, 31)
    events = [
        CatalystEvent(
            kind=CatalystEventKind.FOMC,
            occurs_on=day,
            source=SOURCE_NAME,
            confirmed=True,
            description="美联储议息会议",
            symbol=symbol,
        )
        for year, days in sorted(years.items())
        if len(days) >= _MIN_MEETINGS_PER_YEAR
        for day in sorted(days)
        if moment.date() <= day <= horizon
    ]
    return tuple(sorted(events, key=lambda event: (event.occurs_on, event.kind)))
