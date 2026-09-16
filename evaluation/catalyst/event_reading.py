"""Reading catalyst events back out of the evidence.

Events are written into the evidence by the pipeline and read back here, so that
the catalyst judgement stands on recorded evidence like every other judgement in
AIS. This module is the single place that knows how an event is written down and
how it is read back, so no rule and no evaluator reimplements the lookup.
"""

from __future__ import annotations

from datetime import date

from contracts.catalyst_event_provider import (
    CONFIRMED_METADATA_KEY,
    DATE_METADATA_KEY,
    DESCRIPTION_METADATA_KEY,
    KIND_METADATA_KEY,
    SOURCE_METADATA_KEY,
    SYMBOL_METADATA_KEY,
)
from evidence.evidence_collection import EvidenceCollection
from models.catalyst_event import CatalystEvent, CatalystEventKind


def read_events(evidence: EvidenceCollection) -> tuple[CatalystEvent, ...]:
    """Return the catalyst events the evidence holds, in the order recorded.

    An item whose metadata is incomplete is skipped rather than repaired: an
    event missing its date or its kind is not an event, and inventing the missing
    half would put something in the calendar that no source stated.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        The events recorded, possibly none. None means no event source was read
        or nothing was found, and either way nothing is claimed about the future.
    """
    events: list[CatalystEvent] = []
    for item in evidence.items:
        kind = _kind(item.metadata.get(KIND_METADATA_KEY))
        occurs_on = _date(item.metadata.get(DATE_METADATA_KEY))
        if kind is None or occurs_on is None:
            continue
        description = item.metadata.get(DESCRIPTION_METADATA_KEY, "")
        events.append(
            CatalystEvent(
                kind=kind,
                occurs_on=occurs_on,
                source=item.metadata.get(SOURCE_METADATA_KEY, ""),
                confirmed=item.metadata.get(CONFIRMED_METADATA_KEY) == "true",
                description=description,
                symbol=item.metadata.get(SYMBOL_METADATA_KEY) or None,
            )
        )
    return tuple(events)


def _kind(raw: str | None) -> CatalystEventKind | None:
    """Return the event kind a value names, or None when it names none of ours."""
    if not raw:
        return None
    try:
        return CatalystEventKind(raw)
    except ValueError:
        return None


def _date(raw: str | None) -> date | None:
    """Return the date a value states, or None when it states none."""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None
