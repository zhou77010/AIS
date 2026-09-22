"""One report a day, at a stated hour, with state of its own.

A scheduled report is a message AIS owes a reader at an hour the reader chose. It is not
the evaluation cycle and it does not obey the cycle's rules: it is not gated by the
market, it is not gated by change, and it is computed at the hour it is sent rather than
earlier and delivered late. What follows is the machinery every such report shares, and
nothing about what any particular report says.

**Each report is independent of every other.** A report has its own name in the
scheduler's log, its own key in the state file, its own attempt count and its own
delivery state. Two reports sharing a key would each read the other's day as their own
and would then either send a second copy or stay silent, and neither is visible from
outside. So the policy lives here once, and each report brings its own identity to it:
sharing the mechanism is not sharing the state.

**Delivery is part of the state, not a detail of the attempt.** A report that reached
nobody has not been sent, however many times it was attempted, and the day it was owed
is
still owed. An attempt therefore ends in one of two ways:

* **delivered** — at least one channel carried the message — and the day is settled;
* **failed** — nobody was told anything — and the day stays owed, up to a stated number
  of attempts.

Partial failure is not a state of its own, and deliberately so: a channel failing while
another delivered is a degraded delivery, not a missing one, and resending it would send
a second copy to whoever the first attempt reached. Only a delivery that reached nobody
leaves anything owed.

**A retry is spaced and capped.** It is spaced because the hour the report was owed at
is
already behind, so an attempt that failed would otherwise be immediately due again — a
wake-up loop that costs a full analysis of the universe each time round. It is capped
because a report the reader opened the morning for stops being that report if it arrives
at noon, and because an outage that does not end must not keep the runtime busy until
midnight.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta

from app.runtime_state import (
    ReportDelivery,
    ReportName,
    ReportRecord,
    RuntimeState,
)
from config.logging_config import get_logger
from utils.constants import CycleStatus
from utils.daily_moment import DailyMoment

_LOGGER_NAME = "runtime"

# How many times one report is attempted in a day. Three: the point is to survive an
# outage that lasts minutes at the hour the report was due, and not to keep a phone
# ringing all morning.
MAX_REPORT_ATTEMPTS = 3

# How long to wait before trying again after an attempt that reached nobody. It is the
# same length as the evaluation cycle's default interval, so a failing report never
# wakes
# the process more often than the work that runs anyway.
REPORT_RETRY_INTERVAL = timedelta(minutes=30)


@dataclass(frozen=True)
class ReportOutcome:
    """What one attempt at a report did.

    Attributes:
        status: What the run did, for the scheduler's log.
        delivered: Whether at least one channel carried the message. It is the fact the
            runtime's state is built on: a report that reached a reader is done with,
            and
            one that reached nobody is still owed.
    """

    status: CycleStatus
    delivered: bool


class ScheduledReport:
    """A report that is owed once a local day, and where today's stands.

    It is a schedule in the sense the scheduler means: it answers when it is next owed
    and runs the work when it is. The answer comes from the hour and from what was
    written down, so a restart neither repeats a report nor loses one.

    Subclasses supply identity and work; this class supplies the policy. A subclass is
    responsible for its own name, its own key and its own words, and for nothing about
    when it runs or what an attempt does to the day.
    """

    def __init__(
        self,
        *,
        name: str,
        key: ReportName,
        moment: DailyMoment,
        state: RuntimeState,
        work: Callable[[], ReportOutcome],
        clock: Callable[[], datetime] | None = None,
        max_attempts: int = MAX_REPORT_ATTEMPTS,
        retry_interval: timedelta = REPORT_RETRY_INTERVAL,
    ) -> None:
        """Create the report.

        Args:
            name: What the schedule is called in the log.
            key: The bucket this report's record is written under. It is the report's
                identity in the state file and is never shared with another report.
            moment: Hour of the day it is owed at.
            state: Where the state of each day's report is written down.
            work: Work that produces and delivers the report, and reports whether it
                reached anybody.
            clock: Where the current moment is read from. Defaults to the system clock,
                which is what a running process uses; a test supplies one so that what
                it asserts does not depend on the day it is run.
            max_attempts: How many times a day it may be attempted.
            retry_interval: How long to wait after an attempt that reached nobody.
        """
        self._name = name
        self._key = key
        self._moment = moment
        self._state = state
        self._work = work
        self._clock = clock if clock is not None else _utc_now
        self._max_attempts = max_attempts
        self._retry_interval = retry_interval
        self._memory: ReportRecord | None = None
        self._logger = get_logger(_LOGGER_NAME)

    @property
    def name(self) -> str:
        """Return what the schedule is called."""
        return self._name

    @property
    def key(self) -> ReportName:
        """Return the report's identity in the state file."""
        return self._key

    @property
    def repeats(self) -> bool:
        """Return whether the report is owed again. It is owed every day."""
        return True

    @property
    def moment(self) -> DailyMoment:
        """Return the hour the report is owed at."""
        return self._moment

    def next_due(self, now: datetime) -> datetime:
        """Return the moment the report is next owed.

        A day that has been delivered, or that has run out of attempts, is finished with
        and the next report is tomorrow's. A day whose attempt reached nobody is still
        owed, and it is owed no earlier than one retry interval after that attempt: the
        hour itself is already behind, so without the spacing a failed report would be
        due again the moment it failed.

        Args:
            now: Moment to measure from.

        Returns:
            The next moment it is owed. An hour already behind is returned as it is, so
            a report missed because the process was not running is sent late rather than
            not at all.
        """
        record = self._record(self._moment.local_day(now))
        due = self._moment.at(now)
        if record.is_settled:
            return self._moment.at(now, days_ahead=1)
        if record.attempted_at is None:
            return due
        return max(due, record.attempted_at + self._retry_interval)

    def ran(self, now: datetime) -> None:
        """Record nothing: the state of the day is written with the work.

        The scheduler records that work ran, which is not the same as the report having
        been delivered. What is owed is decided by delivery, so that is written down by
        :meth:`work` and not here.
        """

    def work(self) -> CycleStatus:
        """Run today's report and write down what the attempt did to the day.

        There are three things it can do, and they are different in kind:

        * it is delivered, and the day is finished with;
        * it reaches nobody, and the day is still owed — spaced and capped, so this
          repeats at most until the attempts run out;
        * it reaches nobody for the last time, and the day is abandoned rather than
          retried until midnight.

        A report that fails is reported as a failure in the log, where a person can see
        it. The reader is not told: the channel that would tell them is the one that
        just
        failed.

        Returns:
            The outcome of the run, for the scheduler's log.
        """
        moment = self._clock()
        day = self._moment.local_day(moment)
        record = self._record(day)
        self._logger.info(
            "%s for %s, attempt %d of %d",
            self._name,
            day,
            record.attempts + 1,
            self._max_attempts,
        )
        outcome = self._work()
        return self._settle(day, record, moment, outcome)

    def _settle(
        self,
        day: date,
        record: ReportRecord,
        moment: datetime,
        outcome: ReportOutcome,
    ) -> CycleStatus:
        """Write down what one attempt did to the day and report it."""
        attempt = replace(record, attempts=record.attempts + 1, attempted_at=moment)
        if outcome.delivered:
            self._commit(replace(attempt, delivery=ReportDelivery.SENT))
            self._logger.info("%s for %s was delivered", self._name, day)
            return outcome.status

        if attempt.attempts >= self._max_attempts:
            self._commit(replace(attempt, delivery=ReportDelivery.ABANDONED))
            self._logger.error(
                "the %s for %s reached nobody in %d attempts and will not be tried "
                "again today; the reader was not told",
                self._name,
                day,
                attempt.attempts,
            )
            return outcome.status

        self._commit(attempt)
        self._logger.warning(
            "the %s for %s reached nobody and is still owed; it will be tried again in "
            "%d minute(s), %d attempt(s) left",
            self._name,
            day,
            _minutes(self._retry_interval),
            self._max_attempts - attempt.attempts,
        )
        return outcome.status

    def _record(self, day: date) -> ReportRecord:
        """Return where the given day's report stands.

        A record about another day says nothing about this one: the report is owed once
        per local day, so yesterday's outcome is not today's. The process keeps its own
        copy of what it has done as well as reading the file, so that a state file which
        cannot be written cannot make the report run again for ever.
        """
        record = _furthest(self._memory, self._state.report(self._key))
        if record is None or record.day != day:
            return ReportRecord(day=day)
        return record

    def _commit(self, record: ReportRecord) -> None:
        """Write down where today's report stands, in memory and on disk."""
        self._memory = record
        self._state.record_report(self._key, record)


def _furthest(
    first: ReportRecord | None, second: ReportRecord | None
) -> ReportRecord | None:
    """Return whichever of two records is further along.

    Two records describe the same day when the file is readable, and the one with more
    attempts is the truer of the two: the file is written best-effort, and the process
    is
    what actually ran the work. A record about a different day is used as it is, because
    what happened on one day says nothing about another.
    """
    if first is None:
        return second
    if second is None:
        return first
    if first.day != second.day:
        return first if first.day > second.day else second
    return first if first.attempts >= second.attempts else second


def _minutes(interval: timedelta) -> int:
    """Return an interval in whole minutes, for a log line."""
    return int(interval.total_seconds() // 60)


def _utc_now() -> datetime:
    """Return the current moment, which is what a running process reads."""
    return datetime.now(UTC)
