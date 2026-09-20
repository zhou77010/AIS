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

* :attr:`BriefDelivery.OWED` — not delivered, and still worth another attempt;
* :attr:`BriefDelivery.SENT` — at least one channel carried it, so nobody is owed it
  again;
* :attr:`BriefDelivery.ABANDONED` — the attempts for that day ran out, and the
  runtime stops trying rather than waking up to fail until midnight.

**A state file is not a fact about the world.** It records what AIS has done, which
is a thing AIS knows and a broker or a calendar does not. That is why it is written
by the runtime rather than configured by a person, and why an unreadable file is
treated as an empty one rather than as a reason to stop.

**Written by replacement.** The file is written to a temporary neighbour and moved
into place, so a process killed mid-write leaves the previous state intact rather
than a half-written one. A state file that cannot be read is a state file that was
not written.
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
_BRIEF_KEY = "morning_brief"
# The key the brief's day was written under before a day became a state. It is still
# read, because the day it names is a fact the runtime recorded: forgetting it would
# make a day that has already been reported look owed, and the brief would be sent
# again the moment the process restarted.
_LEGACY_BRIEF_KEY = "morning_brief_sent_on"


class BriefDelivery(StrEnum):
    """Where the brief for one local day stands.

    Three states and no more. A state rather than a flag, because "was anything sent"
    cannot tell a brief that reached a reader from one that reached nobody, and the
    difference decides whether the day is still owed.
    """

    OWED = "owed"
    SENT = "sent"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class BriefRecord:
    """Where the brief for one local day stands.

    Attributes:
        day: Local day the record is about. A record about another day says nothing
            about this one, which is what makes "once a day" survive a restart that
            spans midnight.
        delivery: State the day reached.
        attempts: How many times the brief was attempted that day, whether or not it
            was delivered.
        attempted_at: Moment of the last attempt, or None when there has been none. A
            retry is spaced from it, and that spacing is what keeps a failing brief
            from becoming a loop: the hour it was owed at is already behind, so
            without it the runtime would try again immediately.
    """

    day: date
    delivery: BriefDelivery = BriefDelivery.OWED
    attempts: int = 0
    attempted_at: datetime | None = None

    @property
    def is_settled(self) -> bool:
        """Return whether the day is finished with, delivered or given up on."""
        return self.delivery is not BriefDelivery.OWED


@dataclass(frozen=True)
class RuntimeState:
    """What the runtime remembers between restarts.

    Attributes:
        path: File the state is read from and written to.
    """

    path: Path

    def brief_record(self) -> BriefRecord | None:
        """Return where the brief stands, or None when nothing is written down.

        None is not the same as "owed": what it says is that the runtime has nothing
        recorded, and the caller decides what a missing record means for the day it
        is asking about.
        """
        payload = self._read()
        raw = payload.get(_BRIEF_KEY)
        if isinstance(raw, Mapping):
            return self._parse(raw)
        return self._legacy(payload)

    def record_brief(self, record: BriefRecord) -> None:
        """Write down where the brief for one day stands.

        Args:
            record: The state the day reached.
        """
        payload = self._read()
        payload.pop(_LEGACY_BRIEF_KEY, None)
        payload[_BRIEF_KEY] = {
            "day": record.day.isoformat(),
            "delivery": record.delivery.value,
            "attempts": record.attempts,
            "attempted_at": (
                None if record.attempted_at is None else record.attempted_at.isoformat()
            ),
        }
        self._write(payload)

    def _parse(self, raw: Mapping[str, object]) -> BriefRecord | None:
        """Return the record written in the file, or None when it cannot be read.

        A record whose day or state cannot be read is not half-read: half a record
        would be a claim about a day the runtime did not make, and the cost of a
        second brief is lower than the cost of a wrong one.
        """
        day = _as_date(raw.get("day"))
        delivery = _as_delivery(raw.get("delivery"))
        if day is None or delivery is None:
            self._logger().warning(
                "runtime state at %s holds an unreadable brief record: %r",
                self.path,
                dict(raw),
            )
            return None
        attempts = raw.get("attempts")
        return BriefRecord(
            day=day,
            delivery=delivery,
            attempts=attempts if isinstance(attempts, int) and attempts >= 0 else 0,
            attempted_at=_as_moment(raw.get("attempted_at")),
        )

    def _legacy(self, payload: Mapping[str, object]) -> BriefRecord | None:
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
        return BriefRecord(day=day, delivery=BriefDelivery.SENT, attempts=1)

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


def _as_delivery(raw: object) -> BriefDelivery | None:
    """Return the state a written value names, or None when it names none."""
    if not isinstance(raw, str):
        return None
    try:
        return BriefDelivery(raw)
    except ValueError:
        return None
