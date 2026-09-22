"""What the runtime remembers between restarts.

A scheduled report is owed once per day, and "once" is only meaningful across a
restart: a process that stops and starts must not send a second copy, and a process
that was not running at the appointed hour must still send one when it comes back.
Neither is answerable from memory.

**A day is a state, not a flag.** Whether anything is still owed is not answered by
"was a brief sent". A brief that reached nobody is still owed and one that reached
somebody is finished with, and a flag cannot tell those apart — which is exactly the
case that matters, because the failure worth surviving is an outage at the hour the
report was due. So a day is written down as one of three states, with how many
attempts it has taken and when the last one was, and the runtime reads the state
instead of inferring it:

* :attr:`ReportDelivery.OWED` — not delivered, and still worth another attempt;
* :attr:`ReportDelivery.SENT` — at least one channel carried it, so nobody is owed it
  again;
* :attr:`ReportDelivery.ABANDONED` — the attempts for that day ran out, and the
  runtime stops trying rather than waking up to fail until midnight.

**A state file is not a fact about the world.** It records what AIS has done, which
is a thing AIS knows and a broker or a calendar does not. That is why it is written
by the runtime rather than configured by a person, and why an unreadable file is
treated as an empty one rather than as a reason to stop.

**One file, one bucket per report.** Nothing here is about the morning brief in
particular: a report is any message the runtime owes on a schedule, and the state
file holds one record per report under :data:`_REPORTS_KEY`, keyed by
:class:`ReportName`. A report's day, its attempts and its delivery are its own, and
two reports must never share a key — each would read the other's day as its own, and
would then either repeat itself or stay silent, which is the one failure this module
exists to prevent. The morning brief is the only report there is; the pre-market
brief is a second one when it is built, and it needs nothing from this module but a
member in that enum.

**Written by replacement.** The file is written to a temporary neighbour and moved
into place, so a process killed mid-write leaves the previous state intact rather
than a half-written one. A state file that cannot be read is a state file that was
not written.

**The shapes it was written in before are still read.** A record was once written at
the top level, under the report's name, and before that as the single day the brief
had been sent on. Both are read and neither is written: the day they name is a fact
the runtime recorded, and forgetting it would make a day that has already been
reported look owed.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path

from config.logging_config import get_logger

_LOGGER_NAME = "runtime"
# Where each report's record is written. A report with no bucket is a report that has
# never been attempted.
_REPORTS_KEY = "reports"
# Where the continuous things are written. They are kept apart from the report records
# because they answer a different question: a report record says what has been
# delivered, and a baseline says where something stood.
_BASELINES_KEY = "baselines"
# The key the morning brief's record was written at the top level of the file, before
# a report's state had a bucket of its own.
_BRIEF_KEY = "morning_brief"
# The key the brief's day was written under before a day became a state. It is still
# read, because the day it names is a fact the runtime recorded: forgetting it would
# make a day that has already been reported look owed, and the brief would be sent
# again the moment the process restarted.
_LEGACY_BRIEF_KEY = "morning_brief_sent_on"


class ReportName(StrEnum):
    """A report the runtime owes on a schedule.

    The name is the key the report's record is written under, and it is the whole of a
    report's identity as far as this module is concerned. Each report has its own, and
    adding one is a member here and a schedule that delivers it.

    It is deliberately not the same string as the schedule's own name in the scheduler's
    log: the log names a job, and this names a bucket in a file, and the two are read by
    different things. What must not happen is two reports sharing one of these.
    """

    MORNING_BRIEF = "morning_brief"
    PREMARKET_BRIEF = "premarket_brief"


class BaselineName(StrEnum):
    """Something continuous the runtime remembers between restarts.

    A report's record says what has already been delivered. A baseline says where
    something stood, so the next reading can be compared with it. They answer different
    questions and are kept apart: a baseline is never a claim about what the runtime
    owes.

    The set is deliberately small. A baseline exists to keep a measurement continuous
    across a restart — because a restart that silently resets one turns a comparison
    into a false statement — and not to remember everything a process happens to hold.
    """

    RATINGS = "ratings"
    RECOMMENDATIONS = "recommendations"


class ReportDelivery(StrEnum):
    """Where one report for one local day stands.

    Three states and no more. A state rather than a flag, because "was anything sent"
    cannot tell a report that reached a reader from one that reached nobody, and the
    difference decides whether the day is still owed.
    """

    OWED = "owed"
    SENT = "sent"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class ReportRecord:
    """Where one report for one local day stands.

    Attributes:
        day: Local day the record is about. A record about another day says nothing
            about this one, which is what makes "once a day" survive a restart that
            spans midnight.
        delivery: State the day reached.
        attempts: How many times the report was attempted that day, whether or not it
            was delivered.
        attempted_at: Moment of the last attempt, or None when there has been none. A
            retry is spaced from it, and that spacing is what keeps a failing report
            from becoming a loop: the hour it was owed at is already behind, so
            without it the runtime would try again immediately.
    """

    day: date
    delivery: ReportDelivery = ReportDelivery.OWED
    attempts: int = 0
    attempted_at: datetime | None = None

    @property
    def is_settled(self) -> bool:
        """Return whether the day is finished with, delivered or given up on."""
        return self.delivery is not ReportDelivery.OWED


@dataclass(frozen=True)
class RuntimeState:
    """What the runtime remembers between restarts.

    Attributes:
        path: File the state is read from and written to.
    """

    path: Path

    def report(self, name: ReportName) -> ReportRecord | None:
        """Return where one report stands, or None when nothing is written down.

        None is not the same as "owed": what it says is that the runtime has nothing
        recorded for that report, and the caller decides what a missing record means
        for the day it is asking about.

        Args:
            name: The report to ask about. Only that report's record is returned: the
                answer is never another report's day.
        """
        payload = self._read()
        raw = self._reports(payload).get(name.value)
        if isinstance(raw, Mapping):
            return self._parse(raw, name)
        return self._earlier(payload, name)

    def record_report(self, name: ReportName, record: ReportRecord) -> None:
        """Write down where one report for one day stands.

        The other reports in the file are left exactly as they were found: what one
        report did today is not evidence about another.

        Args:
            name: The report the record is about.
            record: The state the day reached.
        """
        payload = self._read()
        reports = self._reports(payload)
        reports[name.value] = _written(record)
        payload[_REPORTS_KEY] = reports
        self._forget_earlier(payload, name)
        self._write(payload)

    def baseline(self, name: BaselineName) -> Mapping[str, object]:
        """Return a baseline the runtime wrote down, or nothing when there is none.

        The payload is returned as it was written, because the shape belongs to the
        component that owns the baseline and not to this file. An unreadable or absent
        baseline is an empty one: a component that cannot restore what it held simply
        starts again, which is what it did before anything was written down.

        Args:
            name: Which baseline to read.

        Returns:
            The payload the component wrote, or an empty mapping.
        """
        held = self._read().get(_BASELINES_KEY)
        raw = held.get(name.value) if isinstance(held, Mapping) else None
        return dict(raw) if isinstance(raw, Mapping) else {}

    def record_baseline(
        self, name: BaselineName, payload: Mapping[str, object]
    ) -> None:
        """Write down a baseline so that a restart does not break its continuity.

        The other baselines in the file are left as they were found, and so are the
        report records: what one thing stood at is not evidence about another.

        Args:
            name: Which baseline is being written.
            payload: The state the owning component produced.
        """
        written = self._read()
        held = written.get(_BASELINES_KEY)
        baselines = dict(held) if isinstance(held, Mapping) else {}
        baselines[name.value] = dict(payload)
        written[_BASELINES_KEY] = baselines
        self._write(written)

    def _reports(self, payload: Mapping[str, object]) -> dict[str, object]:
        """Return the bucket per report, as a copy that is safe to write back."""
        held = payload.get(_REPORTS_KEY)
        return dict(held) if isinstance(held, Mapping) else {}

    def _earlier(
        self, payload: Mapping[str, object], name: ReportName
    ) -> ReportRecord | None:
        """Return the record an earlier shape of the file holds for one report.

        Only the morning brief was written before reports had buckets, so it is the
        only report with a shape to read here. The two older shapes are tried newest
        first, because a file written by a version that knew about the state is more
        recent than one written by a version that knew only about the day.
        """
        if name is not ReportName.MORNING_BRIEF:
            return None
        raw = payload.get(_BRIEF_KEY)
        if isinstance(raw, Mapping):
            return self._parse(raw, name)
        return self._legacy(payload)

    def _forget_earlier(self, payload: dict[str, object], name: ReportName) -> None:
        """Drop the earlier shapes once the record is written in its own bucket."""
        if name is not ReportName.MORNING_BRIEF:
            return
        payload.pop(_BRIEF_KEY, None)
        payload.pop(_LEGACY_BRIEF_KEY, None)

    def _parse(
        self, raw: Mapping[str, object], name: ReportName
    ) -> ReportRecord | None:
        """Return the record written in the file, or None when it cannot be read.

        A record whose day or state cannot be read is not half-read: half a record
        would be a claim about a day the runtime did not make, and the cost of a
        second report is lower than the cost of a wrong one.
        """
        day = _as_date(raw.get("day"))
        delivery = _as_delivery(raw.get("delivery"))
        if day is None or delivery is None:
            self._logger().warning(
                "runtime state at %s holds an unreadable record for %s: %r",
                self.path,
                name.value,
                dict(raw),
            )
            return None
        attempts = raw.get("attempts")
        return ReportRecord(
            day=day,
            delivery=delivery,
            attempts=attempts if isinstance(attempts, int) and attempts >= 0 else 0,
            attempted_at=_as_moment(raw.get("attempted_at")),
        )

    def _legacy(self, payload: Mapping[str, object]) -> ReportRecord | None:
        """Return the record the older format implies, or None when there is none.

        The older format held one key: the day the brief was sent. Reading it is what
        stops an upgrade from forgetting a day that has already been reported, which
        would send the reader a second copy.
        """
        day = _as_date(payload.get(_LEGACY_BRIEF_KEY))
        if day is None:
            return None
        self._logger().info(
            "runtime state at %s records the brief's day in the older format; "
            "it is read as a brief that was delivered",
            self.path,
        )
        return ReportRecord(day=day, delivery=ReportDelivery.SENT, attempts=1)

    def _read(self) -> dict[str, object]:
        """Return what is written down, or nothing when it cannot be read."""
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            self._logger().warning(
                "runtime state at %s could not be read: %s",
                self.path,
                f"{type(error).__name__}: {error}",
            )
            return {}
        return dict(payload) if isinstance(payload, dict) else {}

    def _write(self, payload: dict[str, object]) -> None:
        """Replace the state file, leaving the previous one intact if this fails."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_name(f"{self.path.name}.writing")
            temporary.write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )
            os.replace(temporary, self.path)
        except OSError as error:
            self._logger().error(
                "runtime state at %s could not be written: %s",
                self.path,
                f"{type(error).__name__}: {error}",
            )

    def _logger(self):
        """Return the logger this module writes to."""
        return get_logger(_LOGGER_NAME)


def _written(record: ReportRecord) -> dict[str, object]:
    """Return one record as it is written down."""
    return {
        "day": record.day.isoformat(),
        "delivery": record.delivery.value,
        "attempts": record.attempts,
        "attempted_at": (
            None if record.attempted_at is None else record.attempted_at.isoformat()
        ),
    }


def _as_date(raw: object) -> date | None:
    """Return the day a written value names, or None when it names none."""
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _as_moment(raw: object) -> datetime | None:
    """Return the moment a written value names, or None when it names none."""
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _as_delivery(raw: object) -> ReportDelivery | None:
    """Return the state a written value names, or None when it names none."""
    if not isinstance(raw, str):
        return None
    try:
        return ReportDelivery(raw)
    except ValueError:
        return None
