"""AIS market clock.

Decides whether the market session is open, so that AIS does not evaluate while
the market it analyses is closed.

Scope: the United States regular session, Monday to Friday, from 09:30 to 16:00
Eastern time. Holidays are deliberately not considered, and other exchanges are
out of scope.

Time zone handling: the IANA time zone database is not shipped with every
platform AIS runs on, and AIS takes no third-party dependency, so the Eastern
offset is derived from the United States daylight saving rule in force since
2007 instead. Daylight saving runs from 02:00 on the second Sunday of March
until 02:00 on the first Sunday of November. If that rule ever changes, this
module must be changed with it.

This module is a stateless helper with no dependency on any AIS layer, which is
why it lives in ``utils`` rather than in the application layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone

MARKET_NAME = "US"

_OPEN_TIME = time(hour=9, minute=30)
_CLOSE_TIME = time(hour=16, minute=0)
_WEEKEND_START = 5

_DAYLIGHT_OFFSET = timedelta(hours=-4)
_STANDARD_OFFSET = timedelta(hours=-5)

_DST_START_MONTH = 3
_DST_START_OCCURRENCE = 2
_DST_START_HOUR_UTC = 7

_DST_END_MONTH = 11
_DST_END_OCCURRENCE = 1
_DST_END_HOUR_UTC = 6


@dataclass(frozen=True)
class MarketStatus:
    """Whether the market session is open, and why.

    Attributes:
        is_open: Whether the regular session is open.
        reason: Human readable explanation, suitable for a log line.
    """

    is_open: bool
    reason: str


class MarketClock:
    """Decides whether the market session is open."""

    def status(self, moment: datetime) -> MarketStatus:
        """Return whether the market is open at the given moment.

        Args:
            moment: Timezone aware moment to test.

        Returns:
            Status holding the outcome and the reason for it.

        Raises:
            ValueError: When the moment carries no time zone. A naive moment
                cannot be placed on the market's clock, and guessing the offset
                would silently produce a wrong answer.
        """
        if moment.tzinfo is None:
            raise ValueError("the market clock needs a timezone aware moment")

        local = moment.astimezone(_eastern_timezone(moment))
        if local.weekday() >= _WEEKEND_START:
            return MarketStatus(
                is_open=False,
                reason=f"{MARKET_NAME} market closed: weekend ({local:%A})",
            )
        if local.time() < _OPEN_TIME:
            return MarketStatus(
                is_open=False,
                reason=(
                    f"{MARKET_NAME} market closed: before the "
                    f"{_OPEN_TIME:%H:%M} open"
                ),
            )
        if local.time() >= _CLOSE_TIME:
            return MarketStatus(
                is_open=False,
                reason=(
                    f"{MARKET_NAME} market closed: after the "
                    f"{_CLOSE_TIME:%H:%M} close"
                ),
            )
        return MarketStatus(
            is_open=True,
            reason=f"{MARKET_NAME} market open ({local:%Y-%m-%d %H:%M %Z})",
        )


def _eastern_timezone(moment: datetime) -> timezone:
    """Return the Eastern offset in force at the given moment."""
    utc = moment.astimezone(UTC)
    start = _daylight_start_utc(utc.year)
    end = _daylight_end_utc(utc.year)
    offset = _DAYLIGHT_OFFSET if start <= utc < end else _STANDARD_OFFSET
    return timezone(offset)


def _daylight_start_utc(year: int) -> datetime:
    """Return the moment United States daylight saving starts, in UTC.

    02:00 Eastern Standard Time is 07:00 UTC.
    """
    return _utc_moment(
        year, _DST_START_MONTH, _DST_START_OCCURRENCE, _DST_START_HOUR_UTC
    )


def _daylight_end_utc(year: int) -> datetime:
    """Return the moment United States daylight saving ends, in UTC.

    02:00 Eastern Daylight Time is 06:00 UTC.
    """
    return _utc_moment(year, _DST_END_MONTH, _DST_END_OCCURRENCE, _DST_END_HOUR_UTC)


def _utc_moment(year: int, month: int, occurrence: int, hour: int) -> datetime:
    """Return the nth Sunday of a month, at an hour, in UTC."""
    day = _nth_sunday(year, month, occurrence)
    return datetime.combine(day, time(hour=hour), tzinfo=UTC)


def _nth_sunday(year: int, month: int, occurrence: int) -> date:
    """Return the date of the nth Sunday of a month.

    Args:
        year: Calendar year.
        month: Calendar month.
        occurrence: Which Sunday of the month, counting from one.

    Returns:
        Date of the requested Sunday.
    """
    first_of_month = date(year, month, 1)
    days_until_sunday = (6 - first_of_month.weekday()) % 7
    return date(year, month, 1 + days_until_sunday + (occurrence - 1) * 7)
