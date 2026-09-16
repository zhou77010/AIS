"""Curated catalyst calendar.

Some events matter and no connected source publishes them: a launch window, a
product launch, a regulatory decision date, an investor day. AIS has two options
for those. It can infer them, which is guessing, or it can read a list somebody
maintains and say who wrote it.

This provider reads the list. It is a file in the repository, in JSON, holding
dates a person has entered together with where each one came from. Nothing is
derived from it and nothing is filled in: an event that is not in the file does
not exist as far as AIS is concerned.

The file is allowed to be absent. A missing file is not an error, it is the
statement that no curated events have been entered yet, and the category reports
the absence for the layer it belongs to.

Schema::

    {
      "events": [
        {
          "kind": "launch_window",
          "date": "2026-10-05",
          "description": "Neutron 火箭发射窗口",
          "symbol": "RKLB",
          "source": "Company guidance",
          "confirmed": false
        }
      ]
    }

``kind`` must be a member of :class:`~models.catalyst_event.CatalystEventKind`.
Which layer an event belongs to is not written in the file: AIS reads that from
the kind, so a curator states what happened and not how AIS should weigh it.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date, datetime
from logging import Logger
from pathlib import Path
from typing import Any

from config.logging_config import get_logger
from models.catalyst_event import CatalystEvent, CatalystEventKind

SOURCE_NAME = "Curated calendar"
_LOGGER_NAME = "market_data"
_JSON_KEY = "events"


class CuratedCatalystEventProvider:
    """Reads dated events a person has entered into a file."""

    def __init__(self, path: Path) -> None:
        """Create the provider.

        Args:
            path: File holding the curated events. It may not exist.
        """
        self._path = path
        self._logger = get_logger(_LOGGER_NAME)

    def fetch_events(self, symbol: str) -> tuple[CatalystEvent, ...]:
        """Return the curated events for a symbol that are still ahead.

        Args:
            symbol: Trading symbol to select events for. An entry with no symbol
                applies to every asset.

        Returns:
            The forthcoming events, possibly none.
        """
        entries = self._read()
        if entries is None:
            return ()

        moment = datetime.now()
        events: list[CatalystEvent] = []
        for entry in entries:
            event = _event(entry, moment, self._logger)
            if event is None:
                continue
            if event.symbol is not None and event.symbol.upper() != symbol.upper():
                continue
            events.append(event)
        return tuple(sorted(events, key=lambda event: (event.occurs_on, event.kind)))

    def _read(self) -> list[Any] | None:
        """Return the entries in the file, or None when there are none to read."""
        if not self._path.exists():
            self._logger.info(
                "no curated catalyst calendar at %s; no curated events", self._path
            )
            return None
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            self._logger.warning(
                "curated catalyst calendar at %s could not be read: %s",
                self._path,
                f"{type(error).__name__}: {error}",
            )
            return None
        if not isinstance(payload, Mapping):
            return None
        entries = payload.get(_JSON_KEY)
        return entries if isinstance(entries, list) else None


def _event(entry: Any, moment: datetime, logger: Logger) -> CatalystEvent | None:
    """Return one curated event, or None when the entry is not usable.

    An entry that cannot be read is skipped with a warning rather than repaired.
    A date AIS cannot parse is not a date, and guessing at one would put an event
    in the report that nobody scheduled.
    """
    if not isinstance(entry, Mapping):
        return None
    kind = _kind(entry.get("kind"))
    occurs_on = _date(entry.get("date"))
    description = entry.get("description")
    if kind is None or occurs_on is None or not isinstance(description, str):
        logger.warning("ignoring unusable curated catalyst entry: %r", entry)
        return None
    if occurs_on < moment.date():
        return None
    symbol = entry.get("symbol")
    source = entry.get("source")
    return CatalystEvent(
        kind=kind,
        occurs_on=occurs_on,
        source=source if isinstance(source, str) and source else SOURCE_NAME,
        confirmed=entry.get("confirmed") is True,
        description=description,
        symbol=symbol if isinstance(symbol, str) and symbol else None,
    )


def _kind(raw: Any) -> CatalystEventKind | None:
    """Return the event kind an entry names, or None when it is not one of ours."""
    if not isinstance(raw, str):
        return None
    try:
        return CatalystEventKind(raw)
    except ValueError:
        return None


def _date(raw: Any) -> date | None:
    """Return the date an entry states, or None when it states none."""
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None
