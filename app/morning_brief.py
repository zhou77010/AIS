"""The daily morning brief: one report a day, at a stated hour.

AIS already sends a message when a conclusion changes. That is a different thing from a
report that arrives every morning whether or not anything changed, and the two must not
be
run by the same rules.

**What makes this report different from the cycle:**

* **It is not gated by the market.** It is sent at an hour a reader chose, and that hour
  falls outside the United States session by definition. A report that waits for a
  market
  to open is a report that never arrives at the hour it was asked for.
* **It is not gated by change.** "Nothing has changed" is not a reason to say nothing
once
  a day; it is what most days look like.
* **It is computed when it is sent.** The state it describes is the state at the hour it
is
  stated about. Computing it earlier and delivering it later would make it a report
  about
  a moment the reader is not in.
* **It is owed once per local day, and that survives a restart.** A second copy is a
  repeated message and a missed one is silence nobody notices, so the day it was sent is
  written down rather than remembered.

**What it is not.** It is not the pre-market brief, which is a report of its own at its
own
hour, with its own state: the two share the delivery policy in
:mod:`app.scheduled_report` and share nothing else. It is not an alert either: nothing
here
decides whether the reader should be interrupted, because this report is expected.

**Where the policy lives.** When the report is owed, what a failed attempt does to the
day
and how a retry is spaced are not about the morning brief in particular, so they are
written once in :mod:`app.scheduled_report`. What is written here is what makes this
report
this report: its hour, its name, and the key its own state is kept under.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from app.runtime_state import ReportName, RuntimeState
from app.scheduled_report import (
    MAX_REPORT_ATTEMPTS,
    REPORT_RETRY_INTERVAL,
    ReportOutcome,
    ScheduledReport,
)
from utils.daily_moment import DailyMoment

# What this report's attempt limit and retry spacing are called here. They are the
# shared
# policy's numbers, named for this report so that a test asserting them asserts the
# morning brief's behaviour rather than a module's default.
MAX_BRIEF_ATTEMPTS = MAX_REPORT_ATTEMPTS
BRIEF_RETRY_INTERVAL = REPORT_RETRY_INTERVAL

# What the schedule is called in the log. It is deliberately not the key the state is
# written under: the log names a job, the state file names a bucket, and the two are
# read
# by different things.
NAME = "morning-brief"


class MorningBrief(ScheduledReport):
    """The daily morning brief, and where today's stands.

    It is a schedule in the sense the scheduler means: it answers when it is next owed
    and
    runs the work when it is. The answer comes from the hour and from what was written
    down, so a restart neither repeats a brief nor loses one.
    """

    def __init__(
        self,
        moment: DailyMoment,
        state: RuntimeState,
        work: Callable[[], ReportOutcome],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Create the brief.

        Args:
            moment: Hour of the day it is owed at.
            state: Where the state of each day's brief is written down.
            work: Work that produces and delivers the brief, and reports whether it
                reached anybody.
            clock: Where the current moment is read from. Defaults to the system clock,
                which is what a running process uses; a test supplies one so that what
                it
                asserts does not depend on the day it is run.
        """
        super().__init__(
            name=NAME,
            key=ReportName.MORNING_BRIEF,
            moment=moment,
            state=state,
            work=work,
            clock=clock,
        )
