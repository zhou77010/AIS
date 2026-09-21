"""AIS United States Treasury yield curve provider.

Every rate AIS reads comes from here and from nowhere else. The Treasury publishes the
whole daily curve — one month through thirty years, including the two year and the ten
year — as a CSV file with no key and no account, and that file is the authority for
what a yield was on a given day.

**One authority per fact.** A vendor also quotes a ten year yield, and reading both
would put two slightly different ten year yields in the same report: two numbers, one
fact, and a reader with no way to tell which one the sentence was written from. So the
vendor's rate quote is not read at all. It is not a fallback either: a fallback that
disagrees is the defect it was meant to cover for, and the honest behaviour when this
source is unavailable is to say the rate could not be read.

**One definition of the curve.** The file carries the three month bill, the two year
note and the ten year note, and AIS reads the ten year less the two year. That is the
spread the market quotes as "the curve"; the three month against the ten year is a
different measure with a different meaning, and holding both would be the same defect
as holding two ten year yields — one concept, two versions.

**What is derived, and how.** The newest session in the file against the one before it,
read as the ten year's change, the spread's level, and the spread's change. The file is
published newest first and AIS sorts by the date it parses rather than trusting the
order: a file that arrives in another order must not silently reverse a day's move. The
dates the two sessions fell on are stated in every reason, so a reader of the expanded
report can see exactly which days a move was measured between.

The provider never raises and never invents a value: a measurement that cannot be
retrieved is returned as a point without a value that states why.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Sequence
from datetime import date, datetime

from config.logging_config import get_logger
from contracts.market_environment import (
    EnvironmentMetric,
    EnvironmentPoint,
    EnvironmentSnapshot,
)
from data.http import HttpTransport, UrllibTransport

SOURCE_NAME = "US Treasury"

_LOGGER_NAME = "market_data"
_CURVE_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
    "&field_tdr_date_value={year}&page&_format=csv"
)

_DATE_COLUMN = "Date"
_TEN_YEAR_COLUMN = "10 Yr"
_TWO_YEAR_COLUMN = "2 Yr"
_DATE_FORMAT = "%m/%d/%Y"

# Yields are published in percent; a basis point is a hundredth of one.
_BASIS_POINTS = 100.0

# A move needs two sessions, and both legs of the spread need to be present.
_SESSIONS_NEEDED = 2


class TreasuryYieldCurveProvider:
    """Retrieves the rate measurements AIS reads, from the Treasury's own curve."""

    def __init__(
        self,
        transport: HttpTransport | None = None,
        today: Callable[[], date] | None = None,
    ) -> None:
        """Create the provider.

        Args:
            transport: Transport to talk through. Defaults to the standard library
                transport; tests supply a stand-in.
            today: Source of the current day, which decides which year's file is
                read. Defaults to the system clock; tests supply their own.
        """
        self._transport: HttpTransport = (
            transport if transport is not None else UrllibTransport()
        )
        self._today = today if today is not None else date.today
        self._logger = get_logger(_LOGGER_NAME)

    def fetch(self) -> EnvironmentSnapshot:
        """Return the rate measurements as the Treasury publishes them.

        The snapshot carries the three measurements this source is able to take and no
        others: the measurements another source carries are not this one's to fill in,
        and a point saying "not mine" would be a claim about a file this provider never
        opened.

        The call never raises. A file that cannot be read, or that holds fewer than
        two usable sessions, produces points without values that state why.

        Returns:
            Snapshot holding this source's measurements.
        """
        sessions = self._sessions()
        return EnvironmentSnapshot(
            source=SOURCE_NAME,
            retrieved_at=datetime.now(),
            points=tuple(_point(metric, sessions) for metric in _METRICS),
        )

    def _sessions(self) -> tuple[_Session, ...]:
        """Return the sessions of the curve, newest first, at most two of them.

        The file is published newest first, and it is sorted here rather than trusted:
        a day's move read backwards is a move in the wrong direction, and nothing about
        the output would look wrong.

        One session is enough to answer with: the level of the curve needs one, and only
        the two changes need a session to compare against. Asking for two here would
        throw away an answer this source can give.
        """
        year = self._today().year
        rows = self._rows(year)
        if len(rows) < _SESSIONS_NEEDED:
            # Early in a year the current file holds almost nothing, and the session
            # before the new year is in the previous one.
            rows.extend(self._rows(year - 1))
        sessions = sorted(rows, key=lambda session: session.day, reverse=True)
        if not sessions:
            self._logger.warning("%s published no usable curve session", SOURCE_NAME)
        return tuple(sessions[:_SESSIONS_NEEDED])

    def _rows(self, year: int) -> list[_Session]:
        """Return the usable sessions of one year's file, possibly none."""
        url = _CURVE_URL.format(year=year)
        try:
            payload = self._transport.get(url)
        except Exception as error:  # noqa: BLE001 - the contract is to never raise
            self._logger.warning(
                "%s curve for %d unavailable: %s",
                SOURCE_NAME,
                year,
                f"{type(error).__name__}: {error}",
            )
            return []
        sessions = _sessions_from(payload)
        self._logger.info(
            "%s curve for %d: %d usable session(s)", SOURCE_NAME, year, len(sessions)
        )
        return sessions


class _Session:
    """One published session: the day, and the two yields AIS reads.

    It is a plain local holder rather than a model, because it exists only between
    parsing the file and turning it into points.
    """

    __slots__ = ("day", "ten_year", "two_year")

    def __init__(self, day: date, ten_year: float, two_year: float) -> None:
        self.day = day
        self.ten_year = ten_year
        self.two_year = two_year

    @property
    def spread(self) -> float:
        """Return the ten year less the two year, in percent."""
        return self.ten_year - self.two_year


def _sessions_from(payload: str) -> list[_Session]:
    """Return the usable sessions of one curve file.

    A row missing either leg, or carrying something that is not a number, is dropped
    rather than repaired: a spread computed from one yield and one guess is not a
    spread. A blank file is not an error — the year has simply not been published yet.
    """
    reader = csv.DictReader(io.StringIO(payload))
    if reader.fieldnames is None:
        return []
    columns = {name.strip(): name for name in reader.fieldnames}
    if not {_DATE_COLUMN, _TEN_YEAR_COLUMN, _TWO_YEAR_COLUMN} <= set(columns):
        return []

    sessions: list[_Session] = []
    for row in reader:
        day = _day(row.get(columns[_DATE_COLUMN]))
        ten_year = _number(row.get(columns[_TEN_YEAR_COLUMN]))
        two_year = _number(row.get(columns[_TWO_YEAR_COLUMN]))
        if day is None or ten_year is None or two_year is None:
            continue
        sessions.append(_Session(day=day, ten_year=ten_year, two_year=two_year))
    return sessions


def _day(raw: str | None) -> date | None:
    """Return the day a row is dated, or None when it states none."""
    if raw is None:
        return None
    try:
        return datetime.strptime(raw.strip(), _DATE_FORMAT).date()
    except ValueError:
        return None


def _number(raw: str | None) -> float | None:
    """Return the yield a row states, or None when it states none."""
    if raw is None:
        return None
    try:
        return float(raw.strip())
    except ValueError:
        return None


# Which measurements this source carries. The rates are one subject and they are read
# from one place: a rate that came from somewhere else would be a second version of a
# fact this file already states.
_METRICS: tuple[EnvironmentMetric, ...] = (
    EnvironmentMetric.TEN_YEAR_YIELD_CHANGE,
    EnvironmentMetric.CURVE_STEEPNESS,
    EnvironmentMetric.CURVE_CHANGE,
)


def _point(
    metric: EnvironmentMetric,
    sessions: Sequence[_Session],
) -> EnvironmentPoint:
    """Return one rate measurement, read from the sessions the file provided.

    The level of the curve is answered from the newest session alone; a change needs the
    one before it as well, and says so when there is not one.
    """
    if not sessions:
        return EnvironmentPoint(
            metric=metric,
            value=None,
            reason=(
                f"{SOURCE_NAME} could not provide the daily yield curve, so this "
                f"measurement was not computed. No other source is read for rates: "
                f"two versions of one yield is worse than none."
            ),
        )

    newest = sessions[0]
    if metric is EnvironmentMetric.CURVE_STEEPNESS:
        spread = newest.spread * _BASIS_POINTS
        return EnvironmentPoint(
            metric=metric,
            value=spread,
            reason=(
                f"{SOURCE_NAME} daily yield curve: ten year less two year "
                f"{spread:+.1f} basis points on {newest.day:%Y-%m-%d}, from "
                f"{newest.two_year:.3f}% and {newest.ten_year:.3f}%."
            ),
        )

    if len(sessions) < _SESSIONS_NEEDED:
        return EnvironmentPoint(
            metric=metric,
            value=None,
            reason=(
                f"{SOURCE_NAME} published one usable curve session, "
                f"{newest.day:%Y-%m-%d}, and a change needs the session before it, so "
                f"it was not computed."
            ),
        )
    previous = sessions[1]

    if metric is EnvironmentMetric.TEN_YEAR_YIELD_CHANGE:
        change = (newest.ten_year - previous.ten_year) * _BASIS_POINTS
        return EnvironmentPoint(
            metric=metric,
            value=change,
            reason=(
                f"{SOURCE_NAME} daily yield curve: ten year {change:+.1f} basis "
                f"points, {previous.ten_year:.3f}% on {previous.day:%Y-%m-%d} to "
                f"{newest.ten_year:.3f}% on {newest.day:%Y-%m-%d}."
            ),
        )

    change = (newest.spread - previous.spread) * _BASIS_POINTS
    return EnvironmentPoint(
        metric=metric,
        value=change,
        reason=(
            f"{SOURCE_NAME} daily yield curve: the ten year less two year spread "
            f"{change:+.1f} basis points, from {previous.spread * _BASIS_POINTS:+.1f} "
            f"on {previous.day:%Y-%m-%d} to {newest.spread * _BASIS_POINTS:+.1f} on "
            f"{newest.day:%Y-%m-%d}."
        ),
    )
