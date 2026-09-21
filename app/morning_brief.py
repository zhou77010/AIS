"""The daily morning brief: one report a day, at a stated hour.

AIS already sends a message when a conclusion changes. That is a different thing
from a report that arrives every morning whether or not anything changed, and the
two must not be run by the same rules.

**What makes this report different from the cycle:**

* **It is not gated by the market.** It is sent at an hour a reader chose, and that
  hour falls outside the United States session by definition. A report that waits for
  a market to open is a report that never arrives at the hour it was asked for.
* **It is not gated by change.** "Nothing has changed" is not a reason to say
  nothing once a day; it is what most days look like.
* **It is computed when it is sent.** The state it describes is the state at the hour
  it is stated about. Computing it earlier and delivering it later would make it a
  report about a moment the reader is not in.
* **It is owed once per local day, and that survives a restart.** A second copy is a
  repeated message and a missed one is silence nobody notices, so the day it was sent
  is written down rather than remembered.

**What it is not.** It is not the pre-market brief, which is a report of its own that
waits for evidence AIS does not have yet. It is not an alert: nothing here decides
whether the reader should be interrupted, because this report is expected.

**Delivery is part of the state, not a detail of the attempt.** A brief that reached
nobody has not been sent, however many times it was attempted, and the day it was
owed is still owed. So an attempt ends in one of two ways, and each moves the day
differently:

* **delivered** — at least one channel carried the message — and the day is settled;
* **failed** — nobody was told anything — and the day stays owed, up to a stated
  number of attempts.

Partial failure is not a state of its own, and deliberately so: a channel failing
while another delivered is a degraded delivery, not a missing one, and resending it
would send a second copy to whoever the first attempt reached. Only a delivery that
reached nobody leaves anything owed.

**A retry is spaced and capped.** It is spaced because the hour the brief was owed at
is already behind, so an attempt that failed would otherwise be immediately due again
— a wake-up loop that costs a full analysis of the universe each time round. It is
capped because the report the reader opened the morning for stops being that report
if it arrives at noon, and because an outage that does not end must not keep the
runtime busy until midnight.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta

from app.runtime_state import ReportDelivery, ReportName, ReportRecord, RuntimeState
from config.logging_config import get_logger
from utils.constants import CycleStatus
from utils.daily_moment import DailyMoment

_LOGGER_NAME = "runtime"

# Where this report's state is written. It is not the name the scheduler logs, and it
# is not shared with any other report: a report that read another's day as its own
# would either send a second copy or stay silent, and neither is visible from outside.
_REPORT = ReportName.MORNING_BRIEF

# How many times the brief is attempted in one day. Three: the point is to survive an
# outage that lasts minutes at the hour the brief was due, and not to keep a phone
# ringing all morning.
MAX_BRIEF_ATTEMPTS = 3

# How long to wait before trying again after an attempt that reached nobody. It is the
# same length as the evaluation cycle's default interval, so a failing brief never
# wakes the process more often than the work that runs anyway.
BRIEF_RETRY_INTERVAL = timedelta(minutes=30)


@dataclass(frozen=True)
class BriefOutcome:
    """What one attempt at the brief did.

    Attributes:
        status: What the run did, for the scheduler's log.
        delivered: Whether at least one channel carried the message. It is the fact
            the runtime's state is built on: a brief that reached a reader is done
            with, and one that reached nobody is still owed.
    """

    status: CycleStatus
    delivered: bool


class MorningBrief:
    """The daily brief, and where today's stands.

    It is a schedule in the sense the scheduler means: it answers when it is next
    owed and runs the work when it is. The answer comes from the hour and from what
    was written down, so a restart neither repeats a brief nor loses one.
    """

    def __init__(
        self,
        moment: DailyMoment,
        state: RuntimeState,
        work: Callable[[], BriefOutcome],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Create the brief.

        Args:
            moment: Hour of the day it is owed at.
            state: Where the state of each day's brief is written down.
            work: Work that produces and delivers the brief, and reports whether it
                reached anybody.
            clock: Where the current moment is read from. Defaults to the system
                clock, which is what a running process uses; a test supplies one so
                that what it asserts does not depend on the day it is run.
        """
        self._moment = moment
        self._state = state
        self._work = work
        self._clock = clock if clock is not None else _utc_now
        self._memory: ReportRecord | None = None
        self._logger = get_logger(_LOGGER_NAME)

    @property
    def name(self) -> str:
        """Return what the schedule is called."""
        return "morning-brief"

    @property
    def repeats(self) -> bool:
        """Return whether the brief is owed again. It is owed every day."""
        return True

    @property
    def moment(self) -> DailyMoment:
        """Return the hour the brief is owed at."""
        return self._moment

    def next_due(self, now: datetime) -> datetime:
        """Return the moment the brief is next owed.

        A day that has been delivered, or that has run out of attempts, is finished
        with and the next brief is tomorrow's. A day whose attempt reached nobody is
        still owed, and it is owed no earlier than one retry interval after that
        attempt: the hour itself is already behind, so without the spacing a failed
        brief would be due again the moment it failed.

        Args:
            now: Moment to measure from.

        Returns:
            The next moment it is owed. An hour already behind is returned as it is,
            so a brief missed because the process was not running is sent late rather
            than not at all.
        """
        record = self._record(self._moment.local_day(now))
        due = self._moment.at(now)
        if record.is_settled:
            return self._moment.at(now, days_ahead=1)
        if record.attempted_at is None:
            return due
        return max(due, record.attempted_at + BRIEF_RETRY_INTERVAL)

    def ran(self, now: datetime) -> None:
        """Record nothing: the state of the day is written with the work.

        The scheduler records that work ran, which is not the same as the brief
        having been delivered. What is owed is decided by delivery, so that is written
        down by :meth:`work` and not here.
        """

    def work(self) -> CycleStatus:
        """Run today's brief and write down what the attempt did to the day.

        There are three things it can do, and they are different in kind:

        * it is delivered, and the day is finished with;
        * it reaches nobody, and the day is still owed — spaced and capped, so this
          repeats at most until the attempts run out;
        * it reaches nobody for the last time, and the day is abandoned rather than
          retried until midnight.

        A brief that fails is reported as a failure in the log, where a person can
        see it. The reader is not told: the channel that would tell them is the one
        that just failed.

        Returns:
            The outcome of the run, for the scheduler's log.
        """
        moment = self._clock()
        day = self._moment.local_day(moment)
        record = self._record(day)
        self._logger.info(
            "morning brief for %s, attempt %d of %d",
            day,
            record.attempts + 1,
            MAX_BRIEF_ATTEMPTS,
        )
        outcome = self._work()
        return self._settle(day, record, moment, outcome)

    def _settle(
        self,
        day: date,
        record: ReportRecord,
        moment: datetime,
        outcome: BriefOutcome,
    ) -> CycleStatus:
        """Write down what one attempt did to the day and report it."""
        attempt = replace(record, attempts=record.attempts + 1, attempted_at=moment)
        if outcome.delivered:
            self._commit(replace(attempt, delivery=ReportDelivery.SENT))
            self._logger.info("morning brief for %s was delivered", day)
            return outcome.status

        if attempt.attempts >= MAX_BRIEF_ATTEMPTS:
            self._commit(replace(attempt, delivery=ReportDelivery.ABANDONED))
            self._logger.error(
                "the brief for %s reached nobody in %d attempts and will not be "
                "tried again today; the reader was not told",
                day,
                attempt.attempts,
            )
            return outcome.status

        self._commit(attempt)
        self._logger.warning(
            "the brief for %s reached nobody and is still owed; it will be tried "
            "again in %d minute(s), %d attempt(s) left",
            day,
            _minutes(BRIEF_RETRY_INTERVAL),
            MAX_BRIEF_ATTEMPTS - attempt.attempts,
        )
        return outcome.status

    def _record(self, day: date) -> ReportRecord:
        """Return where the given day's brief stands.

        A record about another day says nothing about this one: the brief is owed once
        per local day, so yesterday's outcome is not today's. The process keeps its own
        copy of what it has done as well as reading the file, so that a state file
        which cannot be written cannot make the brief run again for ever.
        """
        record = _furthest(self._memory, self._state.report(_REPORT))
        if record is None or record.day != day:
            return ReportRecord(day=day)
        return record

    def _commit(self, record: ReportRecord) -> None:
        """Write down where today's brief stands, in memory and on disk."""
        self._memory = record
        self._state.record_report(_REPORT, record)


def _furthest(
    first: ReportRecord | None, second: ReportRecord | None
) -> ReportRecord | None:
    """Return whichever of two records is further along.

    Two records describe the same day when the file is readable, and the one with more
    attempts is the truer of the two: the file is written best-effort, and the process
    is what actually ran the work. A record about a different day is used as it is,
    because what happened on one day says nothing about another.
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
