"""The parts of a Positioning judgement.

The Constitution asks one question of this category: who else holds this asset,
and how crowded is that? Naming the question makes three parts visible.

**Ownership.** Who is on the register: institutions and insiders. Sources report
these as shares of the company held, which is what is measured.

**Crowding.** How much of the trade is already on the other side: short interest
and the days needed to cover it.

**Flow.** Whether money is arriving or leaving, and whether options or sentiment
are leaning one way. No source connected to AIS reports any of it.

Only the first two are measured, so coverage reads two parts of three. Naming
flow is the point of this module: a category that stopped at what it could reach
would be claiming the question was answered when a third of it was not.
"""

from __future__ import annotations

from enum import StrEnum


class PositioningPart(StrEnum):
    """A part of the positioning question, as the Constitution states it."""

    OWNERSHIP = "ownership"
    CROWDING = "crowding"
    FLOW = "flow"
