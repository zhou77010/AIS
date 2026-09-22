"""Tracking where each category stood, so its movement can be measured.

A grade says where a category stands today. It cannot say whether it got there
by climbing or by arriving all at once, and it cannot show a category improving
for weeks without yet crossing into the next grade. That needs the previous
reading, which is what this holds.

Three things are remembered for each category of each symbol: the score its
grade was set at, the moment the current run of movement began, and what every
measurement read at that moment. The last of those is what lets the report say
*why* a category is moving rather than only that it is.

The tracker holds its standing in memory and can write it down, because a restart that
silently reset it would turn a comparison into a false statement. A restored standing is
a real one: it was recorded at a real moment, so the movement measured from it is
movement that happened, including any that happened while the process was not running. A
standing that cannot be restored is treated as absent, and the first rating after that
carries no movement — which is the honest answer when there is nothing to compare with,
not an invented baseline.

Nothing here judges. The grade is decided elsewhere and handed in; the tracker
only remembers it and measures how far the measurement has travelled since.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

from contracts.market_data_provider import MarketMetric
from models.category import Category
from models.category_rating import CategoryRating


@dataclass
class _Standing:
    """Where a category stood when its grade was last set."""

    grade: int
    score: float
    changed_at: datetime
    reason: str
    since: datetime
    direction: int
    measurements: dict[MarketMetric, float] = field(default_factory=dict)


def _key(symbol: str, category: Category) -> str:
    """Return the key one standing is written under.

    A separator that cannot appear in a ticker keeps the two halves unambiguous, so a
    key is read back into exactly the pair it was written from.
    """
    return f"{symbol}|{category.value}"


def _split_key(key: object) -> tuple[str, Category] | None:
    """Return the symbol and category a written key names, or None."""
    if not isinstance(key, str) or "|" not in key:
        return None
    symbol, _, name = key.partition("|")
    if not symbol:
        return None
    try:
        return symbol, Category(name)
    except ValueError:
        return None


def _as_written(standing: _Standing) -> dict[str, object]:
    """Return one standing as it is written down."""
    return {
        "grade": standing.grade,
        "score": standing.score,
        "changed_at": standing.changed_at.isoformat(),
        "reason": standing.reason,
        "since": standing.since.isoformat(),
        "direction": standing.direction,
        "measurements": {
            metric.value: value for metric, value in standing.measurements.items()
        },
    }


def _as_standing(raw: object) -> _Standing | None:
    """Return the standing a written payload holds, or None when it cannot be read.

    A half-read standing would put a movement in the report that rests on a baseline
    nobody recorded, so anything unreadable is reported as absent instead.
    """
    if not isinstance(raw, Mapping):
        return None
    try:
        return _Standing(
            grade=int(raw["grade"]),
            score=float(raw["score"]),
            changed_at=datetime.fromisoformat(str(raw["changed_at"])),
            reason=str(raw["reason"]),
            since=datetime.fromisoformat(str(raw["since"])),
            direction=int(raw.get("direction", 0)),
            measurements=_as_measurements(raw.get("measurements")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _as_measurements(raw: object) -> dict[MarketMetric, float]:
    """Return the measurements a written payload holds, skipping anything unreadable."""
    if not isinstance(raw, Mapping):
        return {}
    readings: dict[MarketMetric, float] = {}
    for name, value in raw.items():
        try:
            metric = MarketMetric(name)
        except ValueError:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        readings[metric] = float(value)
    return readings


class RatingTracker:
    """Remembers the standing of every category of every symbol it has seen."""

    def __init__(self) -> None:
        """Create a tracker that has seen nothing yet."""
        self._standings: dict[tuple[str, Category], _Standing] = {}

    def snapshot(self) -> dict[str, object]:
        """Return everything the tracker holds, in a form that can be written down.

        The payload is the tracker's own shape and is read back by :meth:`restore`. It
        is flat and keyed by symbol and category so that a state file stays readable by
        a person, which is the only way a wrong baseline would ever be noticed.
        """
        return {
            _key(symbol, category): _as_written(standing)
            for (symbol, category), standing in self._standings.items()
        }

    def restore(self, payload: Mapping[str, object]) -> int:
        """Fill the tracker from a written payload and report how many it restored.

        A key or a standing that cannot be read is skipped rather than half-read, so a
        corrupt entry costs its own comparison and nothing else.

        Args:
            payload: What :meth:`snapshot` wrote, or an empty mapping.

        Returns:
            How many standings were restored, for the log line that says so.
        """
        restored = 0
        for key, raw in payload.items():
            parsed = _split_key(key)
            standing = _as_standing(raw)
            if parsed is None or standing is None:
                continue
            self._standings[parsed] = standing
            restored += 1
        return restored

    def update(
        self,
        symbol: str,
        category: Category,
        grade: int,
        score: float,
        reason: str,
        measurements: Mapping[MarketMetric, float],
        moment: datetime,
    ) -> CategoryRating:
        """Record where a category stands and return its rating.

        When the grade has changed, the movement starts again from zero and
        everything is refreshed. When it has not, the movement carries on
        accumulating from the score the grade was set at, and the moment the
        current run began is kept so the report can say how long it has lasted.

        Args:
            symbol: Symbol the category belongs to.
            category: Category being rated.
            grade: Position the category now stands at, from one to five.
            score: The category's own measurement, which the movement follows.
            reason: What the category says about itself now.
            measurements: What the category's measurements read now.
            moment: Moment the reading was taken.

        Returns:
            The rating for this reading.
        """
        key = (symbol, category)
        previous = self._standings.get(key)
        readings = dict(measurements)

        if previous is None or previous.grade != grade:
            self._standings[key] = _Standing(
                grade=grade,
                score=score,
                changed_at=moment,
                reason=reason,
                since=moment,
                direction=0,
                measurements=readings,
            )
            return CategoryRating(
                category=category,
                grade=grade,
                momentum=0.0,
                changed_at=moment,
                changed=True,
                previous_grade=None if previous is None else previous.grade,
                reason=reason,
                since=moment,
            )

        momentum = _momentum(previous.score, score)
        direction = _direction_of(momentum)
        if direction != 0 and previous.direction not in {0, direction}:
            # The measurement turned around, so the run the reader is being told
            # the length of starts here rather than at the grade change. A run
            # that only now starts moving is not a turn: nothing had been moving
            # before it, so the length it has lasted is still the whole standing.
            previous.since = moment
            previous.measurements = readings
        if direction != 0:
            previous.direction = direction

        driver, driver_from, driver_to = _dominant_mover(
            previous.measurements, readings
        )
        return CategoryRating(
            category=category,
            grade=grade,
            momentum=momentum,
            changed_at=previous.changed_at,
            changed=False,
            previous_grade=None,
            reason=previous.reason,
            since=previous.since,
            driver=driver,
            driver_from=driver_from,
            driver_to=driver_to,
        )


def _momentum(baseline: float, score: float) -> float:
    """Return how far a measurement has moved from the score a grade was set at.

    A baseline that is not positive carries no meaningful comparison: the
    measurement is not a quantity that a share of it would describe. That case
    reports no movement rather than a share of a negative number.
    """
    if baseline <= 0:
        return 0.0
    return score / baseline - 1.0


def _direction_of(momentum: float) -> int:
    """Return the way the measurement is going, or zero when it is still."""
    if momentum > 0:
        return 1
    if momentum < 0:
        return -1
    return 0


def _dominant_mover(
    baseline: Mapping[MarketMetric, float],
    current: Mapping[MarketMetric, float],
) -> tuple[MarketMetric | None, float | None, float | None]:
    """Return the measurement that moved most while the movement accumulated.

    Attribution is by size, because how much each measurement contributed to a
    judgement is a method AIS has not defined. The largest movement is the best
    available answer to "what changed", and it is an answer about the evidence
    rather than a summary of the whole category.
    """
    best: tuple[MarketMetric | None, float | None, float | None] = (None, None, None)
    largest = 0.0
    for metric, was in baseline.items():
        now = current.get(metric)
        if now is None or was == 0:
            continue
        change = abs(now / was - 1.0)
        if change > largest:
            largest = change
            best = (metric, was, now)
    return best
