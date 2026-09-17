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
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime

from app.runtime_state import RuntimeState
from config.logging_config import get_logger
from utils.constants import CycleStatus
from utils.daily_moment import DailyMoment

_LOGGER_NAME = "runtime"


class MorningBrief:
    """The daily brief, and whether today's has already been sent.

    It is a schedule in the sense the scheduler means: it answers when it is next
    owed and runs the work when it is. The answer comes from the hour and from what
    was written down, so a restart neither repeats a brief nor loses one.
    """

    def __init__(
        self,
        moment: DailyMoment,
        state: RuntimeState,
        work: Callable[[], CycleStatus],
    ) -> None:
        """Create the brief.

        Args:
            moment: Hour of the day it is owed at.
            state: Where the day it was last sent is written down.
            work: Work that produces and delivers the brief.
        """
        self._moment = moment
        self._state = state
        self._work = work
        self._sent: date | None = None
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

        The answer comes from the clock and from the day it was last sent, never
        from when the process started.

        Args:
            now: Moment to measure from.

        Returns:
            The next hour it is owed at. An hour already behind is returned as it
            is, so a brief missed because the process was not running is sent late
            rather than not at all.
        """
        return self._moment.next_due(now, sent_on=self._sent_on())

    def ran(self, now: datetime) -> None:
        """Record nothing: the day the brief was sent is recorded with the work.

        The scheduler records that work ran, which is not the same as the brief
        having been delivered. What is owed is decided by delivery, so that is
        written down by :meth:`work` and not here.
        """

    def work(self) -> CycleStatus:
        """Run the brief for today and write down that the day is done.

        The day is recorded whatever the outcome. A brief is owed once a day, and
        the attempt is the day's brief: retrying a delivery failure would send a
        second copy to whoever the first attempt reached, and would repeat a full
        evaluation of the universe on every wake until it stopped failing. A failure
        is reported as a failure instead, in the log and in the cycle status.

        Returns:
            The outcome of producing and delivering the brief.
        """
        day = self._moment.local_day(datetime.now(UTC))
        self._logger.info("morning brief for %s", day)
        status = self._work()
        self._sent = day
        self._state.record_brief_sent(day)
        return status

    def _sent_on(self) -> date | None:
        """Return the day the brief was last sent, from memory and from the file.

        Both are consulted, and the later of the two wins. The written one survives a
        restart; the remembered one keeps a state file that cannot be written from
        turning the brief into a loop.
        """
        written = self._state.brief_sent_on()
        if self._sent is None:
            return written
        if written is None:
            return self._sent
        return max(self._sent, written)
