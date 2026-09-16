"""The parts of a Catalyst judgement.

The Constitution asks one question of this category: what identifiable event
could change this picture, and when? The question has two halves, and they are
not equally answerable.

**Scheduled events.** Events a market data source can date: when the next
results are due, when the shares next go ex-dividend. A date is available, so
these are measured.

**Events with no source.** Product launches, regulatory decisions, launch
windows, shareholder meetings and macro events are all real catalysts, and no
source connected to AIS reports any of them. They are not measured, and because
they are named here they are also not quietly dropped: a coverage of one part of
two is a truthful statement that the category looked at the calendar and not at
the world.

Naming the second half is the point of this module. A category that declared
itself complete because it had measured everything it could reach would be
claiming to have answered a question it has only half answered.
"""

from __future__ import annotations

from enum import StrEnum


class CatalystPart(StrEnum):
    """A part of the catalyst question, as the Constitution states it."""

    SCHEDULED = "scheduled"
    EXTERNAL = "external"
