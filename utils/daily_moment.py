"""A moment of the day, in a fixed offset.

Some work is owed at a time of day rather than every so many minutes, and a time of
day only means something with an offset attached. This holds the two together and
answers the questions a schedule needs: which local day it is, when the moment falls
on a given day, and whether today's has passed.

**A fixed offset, not a time zone.** A time zone is a rule that can change; an
offset is a number. The moments AIS schedules are read in Beijing, which has held
UTC+8 since 1991 and does not observe daylight saving, so the offset is the honest
description and there is no rule to keep up with. A moment that does observe
daylight saving would need a zone, and this is deliberately not that.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

BEIJING_OFFSET = timedelta(hours=8)
_MINUTES_PER_HOUR = 60


@dataclass(frozen=True)
class DailyMoment:
    """A time of day, in a fixed offset from UTC.

    Attributes:
        hour: Hour of the local day, from zero to twenty three.
        minute: Minute of the hour.
        utc_offset: The offset the time of day is stated in.
    """

    hour: int
    minute: int
    utc_offset: timedelta

    def __post_init__(self) -> None:
        """Reject a moment that is not a time of day."""
        if not 0 <= self.hour <= 23 or not 0 <= self.minute <= 59:
            raise ValueError(
                f"a moment of the day cannot be {self.hour:02d}:{self.minute:02d}"
            )

    @classmethod
    def beijing(cls, hour: int, minute: int) -> DailyMoment:
        """Return a moment stated in Beijing time."""
        return cls(hour=hour, minute=minute, utc_offset=BEIJING_OFFSET)

    @property
    def timezone(self) -> timezone:
        """Return the offset as a time zone."""
        return timezone(self.utc_offset)

    def local_day(self, now: datetime) -> date:
        """Return the local day a moment falls on."""
        return now.astimezone(self.timezone).date()

    def at(self, now: datetime, *, days_ahead: int = 0) -> datetime:
        """Return this moment on a local day, as an absolute instant.

        Args:
            now: Moment naming the local day to use.
            days_ahead: How many local days after that day to take.

        Returns:
            The moment, carrying the offset it was stated in.
        """
        day = self.local_day(now) + timedelta(days=days_ahead)
        local = datetime.combine(day, time(self.hour, self.minute), self.timezone)
        return local

    def has_passed(self, now: datetime) -> bool:
        """Return whether today's moment is at or behind the given moment."""
        return now >= self.at(now)

    def next_due(self, now: datetime, *, sent_on: date | None = None) -> datetime:
        """Return the moment this is next owed.

        Args:
            now: Moment to measure from.
            sent_on: Local day it was last done on, or None when it never was.

        Returns:
            The next moment it is owed. A moment that is already behind is returned
            as it is rather than skipped, so that work missed — because the process
            was not running — is done late rather than not at all.
        """
        if sent_on is not None and sent_on >= self.local_day(now):
            return self.at(now, days_ahead=1)
        return self.at(now)

    def describe(self) -> str:
        """Return the moment written the way it is stated."""
        hours = int(self.utc_offset.total_seconds()) // 3600
        return f"{self.hour:02d}:{self.minute:02d} UTC+{hours:02d}:00"


def minutes_between(now: datetime, moment: datetime) -> float:
    """Return how long there is between two moments, never negative."""
    return max(0.0, (moment - now).total_seconds() / _MINUTES_PER_HOUR)
