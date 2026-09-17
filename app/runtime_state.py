"""What the runtime remembers between restarts.

A scheduled report is owed once per day, and "once" is only meaningful across a
restart: a process that stops and starts must not send a second copy, and a process
that was not running at the appointed hour must still send one when it comes back.
Neither is answerable from memory.

So the small amount of state that decides what is still owed is written down. It is
not a cache and it is not a record of what was said: it holds the day the daily
brief was last sent, and nothing else.

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
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from config.logging_config import get_logger

_LOGGER_NAME = "runtime"
_BRIEF_KEY = "morning_brief_sent_on"


@dataclass(frozen=True)
class RuntimeState:
    """What the runtime remembers between restarts.

    Attributes:
        path: File the state is read from and written to.
    """

    path: Path

    def brief_sent_on(self) -> date | None:
        """Return the local day the daily brief was last sent, or None.

        None means it has never been sent, or that what was written could not be
        read. The two are treated alike on purpose: the cost of a second brief is a
        repeated message, and the cost of a missing one is silence that nobody
        notices.
        """
        payload = self._read()
        raw = payload.get(_BRIEF_KEY)
        if not isinstance(raw, str):
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            self._logger().warning("%s holds an unreadable date: %r", self.path, raw)
            return None

    def record_brief_sent(self, day: date) -> None:
        """Write down that the daily brief was sent on a local day.

        Args:
            day: Local day the brief was sent on.
        """
        payload = self._read()
        payload[_BRIEF_KEY] = day.isoformat()
        self._write(payload)

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
