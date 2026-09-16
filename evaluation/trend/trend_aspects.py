"""The aspects of price behaviour a Trend judgement is about.

The Constitution asks one question of this category — what has the price
actually been doing, over a window that is stated — and requires the window to
be stated. It names no aspects.

This set is this implementation's reading of that question, and, like the Market
aspects, it is not Constitution semantics and is open to ratification. It exists
because coverage has to be measured against something: with two measurements and
two aspects, a category would report complete coverage while having seen nothing
about how the price travelled to where it is.

Reading the question as three aspects:

* **Position** — where the price sits within the range it has traded in.
* **Direction** — which way it moved over the window.
* **Path** — how it got there: steadily, or erratically. This needs the price
  over time rather than one snapshot, and is not measured.

Every aspect is about a stated window. The window is carried in the name of each
measurement, so it reaches the report with the number rather than being left
behind in the code.
"""

from __future__ import annotations

from enum import StrEnum


class TrendAspect(StrEnum):
    """An aspect of what the price has been doing."""

    POSITION = "position"
    DIRECTION = "direction"
    PATH = "path"
