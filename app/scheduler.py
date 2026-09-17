"""AIS scheduler.

Runs the work the runtime owes, at the moments it is owed.

**The loop is here and nowhere else.** Nothing else in AIS waits or repeats; the
scheduler is handed work and schedules, and it decides when each is due. It knows
nothing about analysis, notification or the market, so a schedule can be added
without it learning what the work is for.

**Schedules say when, not the scheduler.** Each schedule answers one question — when
am I next owed — and the scheduler sleeps to the earliest answer. That is what makes
a report land at a stated hour instead of drifting with whatever time the process
happened to start: the moment comes from the clock, not from the process.

**A schedule that is behind runs immediately rather than being skipped.** A process
that was not running when the hour arrived owes that work, and doing it late is
better than not doing it at all. A schedule decides for itself whether it is still
owed, because only it knows what it has already done.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol

from config.logging_config import get_logger
from utils.constants import CycleStatus

_LOGGER_NAME = "scheduler"
_SECONDS_PER_MINUTE = 60


class Schedule(Protocol):
    """Work the runtime owes, and when it is next owed.

    An implementation answers one question: given the moment now, when am I next
    owed? It may answer "now", which is how a schedule that is behind says it has
    been missed rather than merely becoming due.
    """

    @property
    def name(self) -> str:
        """Return what the schedule is called, for the log."""

    @property
    def repeats(self) -> bool:
        """Return whether the work is owed again after it has run."""

    def next_due(self, now: datetime) -> datetime:
        """Return the moment the work is next owed.

        Args:
            now: Moment to measure from.

        Returns:
            The next moment it is owed, which may be the moment given.
        """

    def ran(self, now: datetime) -> None:
        """Record that the work was run at a moment.

        A schedule that keeps its own cadence advances it here; one that reads what
        it has already done has nothing to do.
        """

    def work(self) -> CycleStatus:
        """Run the work and return its outcome."""


class IntervalSchedule:
    """Work owed every so many minutes, measured from the last time it ran.

    This is the cadence of the evaluation cycle, and its phase belongs to the
    process rather than to the clock: it says how often to look, not when. Work that
    has to land at a stated hour is a :class:`~app.morning_brief.MorningBrief`
    instead, and the two are separate schedules for exactly that reason.
    """

    def __init__(self, interval_minutes: int, work: Callable[[], CycleStatus]) -> None:
        """Create the schedule.

        Args:
            interval_minutes: Minutes to wait between runs. Zero or less runs the
                work once and never again.
            work: Work to run.
        """
        self._interval = timedelta(minutes=interval_minutes)
        self._work = work
        self._next: datetime | None = None

    @property
    def name(self) -> str:
        """Return what the schedule is called."""
        return "cycle"

    @property
    def repeats(self) -> bool:
        """Return whether the work is owed again."""
        return self._interval > timedelta(0)

    def next_due(self, now: datetime) -> datetime:
        """Return when the work is next owed. The first run is immediate."""
        return now if self._next is None else self._next

    def ran(self, now: datetime) -> None:
        """Move the next run one interval on from the moment it ran."""
        self._next = now + self._interval

    def work(self) -> CycleStatus:
        """Run the evaluation cycle."""
        return self._work()


class Scheduler:
    """Runs every schedule at the moment it is owed."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        """Create a scheduler that owes nothing yet.

        Args:
            clock: Source of the current moment. Defaults to the system clock; a
                caller supplies its own to test what the scheduler does at moments
                that would otherwise have to be waited for.
        """
        self._clock = clock if clock is not None else _now
        self._logger = get_logger(_LOGGER_NAME)

    def run(self, *schedules: Schedule) -> None:
        """Run the schedules until none is owed again, or until interrupted.

        A schedule that will not recur is dropped once it has run, so work owed once
        stops being owed rather than staying due for ever.

        Args:
            *schedules: Work the runtime owes, each with its own answer to when.
        """
        pending = list(schedules)
        while True:
            if not pending:
                self._logger.info("nothing is owed; stopping")
                return
            now = self._clock()
            deadlines = tuple(
                (schedule, schedule.next_due(now)) for schedule in pending
            )
            due = tuple(schedule for schedule, moment in deadlines if moment <= now)
            if not due:
                schedule, wake = min(deadlines, key=lambda entry: entry[1])
                self._logger.info(
                    "next: %s in %.0f minute(s)",
                    schedule.name,
                    (wake - now).total_seconds() / _SECONDS_PER_MINUTE,
                )
                time.sleep(max(0.0, (wake - now).total_seconds()))
                continue
            for schedule in due:
                self._run_once(schedule)
                schedule.ran(self._clock())
                if not schedule.repeats:
                    pending.remove(schedule)

    def _run_once(self, schedule: Schedule) -> None:
        """Run one schedule's work and report its outcome.

        Work that raises is recorded and the loop continues: an evaluation that fails
        once must not stop a system meant to keep running.
        """
        try:
            status = schedule.work()
        except Exception:  # noqa: BLE001 - the loop must survive any failure
            self._logger.exception(
                "%s failed unexpectedly and was recorded as %s",
                schedule.name,
                CycleStatus.EVALUATION_FAILED.value,
            )
            return
        self._logger.info("%s finished: %s", schedule.name, status.value)


def _now() -> datetime:
    """Return the current moment, in UTC."""
    return datetime.now(UTC)
