"""The parts of an Earnings judgement.

The Constitution asks one question of this category and names both of its parts
in the question itself: what have the reported results said, and what are they
expected to say next.

Because the question names its parts, this category does not need an aspect set
invented for it the way Market and Trend did. The two parts below are the
question, and both are measured, so a coverage of two of two says what it looks
like it says.

Nothing beyond the two parts is claimed. Guidance and estimate revisions are
real things investors watch, and no source for either is connected, so they are
not part of the question this category answers.
"""

from __future__ import annotations

from enum import StrEnum


class EarningsPart(StrEnum):
    """A part of the earnings question, as the Constitution states it."""

    REPORTED = "reported"
    EXPECTED = "expected"
