"""The pre-market brief: one report a day, thirty minutes before the open.

AIS sends one report after the United States day has ended. This is the other end of the
same day: the hour before the next session opens, when the pre-market has already traded
and nothing about the session itself has happened yet.

**What makes this report a report of its own:**

* **Its hour answers a different question.** The morning brief says what happened and
where
  the asset stands; this one says what price is doing before the open, which is a fact
  that
  does not exist twelve hours earlier and is stale five hours later.
* **It is not gated by the market either.** The hour falls before the session in which
the
  reader would act, so it is the one moment a report cannot wait for that session to
  open.
* **It holds three kinds of evidence, and it says which of them answered.** The
environment,
  the company's own pre-market evidence and news arrive at different speeds. Waiting for
  all three would mean never speaking; this report states what it has (see
  :mod:`analysis.premarket_report`).

**What it is not.** It is not the morning brief sent at another hour: the two are
separate
schedules, with separate names, separate state and separate attempts, and neither reads
the other's day. It is not an alert either — it is an expected report, so nothing here
decides whether the reader should be interrupted.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from app.runtime_state import ReportName, RuntimeState
from app.scheduled_report import ReportOutcome, ScheduledReport
from utils.daily_moment import DailyMoment

# What the schedule is called in the log. It is deliberately not the key the state is
# written under, and it is deliberately not the morning brief's name.
NAME = "premarket-brief"


class PreMarketBrief(ScheduledReport):
    """The daily pre-market brief, and where today's stands.

    It answers when it is next owed and runs the work when it is, exactly as the morning
    brief does, and it holds its own day: the state file keeps one record per report, so
    the two can be delivered in either order, at either hour, and a failure in one says
    nothing about the other.
    """

    def __init__(
        self,
        moment: DailyMoment,
        state: RuntimeState,
        work: Callable[[], ReportOutcome],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Create the pre-market brief.

        Args:
            moment: Hour of the day it is owed at.
            state: Where the state of each day's report is written down.
            work: Work that produces and delivers the report, and reports whether it
                reached anybody.
            clock: Where the current moment is read from. Defaults to the system clock,
                which is what a running process uses; a test supplies one so that what
                it
                asserts does not depend on the day it is run.
        """
        super().__init__(
            name=NAME,
            key=ReportName.PREMARKET_BRIEF,
            moment=moment,
            state=state,
            work=work,
            clock=clock,
        )
