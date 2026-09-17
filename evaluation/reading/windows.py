"""The time windows AIS reads the calendar against.

A window is a threshold like any other, and it belongs in one place for the same
reason. "Near term" previously meant ninety days to the opportunity conditions and
thirty days to the sentence underneath them, so a report could say an asset had a
near term catalyst directly above a sentence saying there was no clear catalyst in
the near term. Both statements were produced from the same calendar.

**One window, one meaning.** A single number says what near term is, the catalyst
scale reads its bands from it, and the sentence and the opportunity condition both
take their meaning from those bands rather than deciding again.
"""

from __future__ import annotations

from evaluation.reading.bands import Band, Direction, MetricScale

# How near an event has to be to be treated as coming.
IMMINENT_DAYS = 7
NEAR_TERM_DAYS = 30
CATALYST_WINDOW_DAYS = 90
DISTANT_DAYS = 180

CATALYST_PROXIMITY_BANDS: tuple[Band, ...] = (
    Band(IMMINENT_DAYS, "即将落地"),
    Band(NEAR_TERM_DAYS, "一个月内"),
    Band(CATALYST_WINDOW_DAYS, "一个季度内"),
    Band(DISTANT_DAYS, "半年内"),
)

CATALYST_PROXIMITY: MetricScale = MetricScale(
    direction=Direction.LOWER_IS_BETTER,
    bands=CATALYST_PROXIMITY_BANDS,
    below_word="更远",
)


def catalyst_score(days: int) -> int:
    """Return how near a catalyst reads, in days.

    Args:
        days: Whole days until the nearest event that could change a view.

    Returns:
        A score from one to five, five being the nearest.
    """
    for index, band in enumerate(CATALYST_PROXIMITY_BANDS):
        if days <= band.threshold:
            return len(CATALYST_PROXIMITY_BANDS) + 1 - index
    return 1


def catalyst_word(days: int) -> str:
    """Return how a distance to the nearest catalyst is described."""
    for band in CATALYST_PROXIMITY_BANDS:
        if days <= band.threshold:
            return band.word
    return CATALYST_PROXIMITY.below_word


# The score a catalyst reaches when it is within the near term. It is derived from
# the bands rather than written down, so moving the near term window moves this
# with it and the opportunity condition cannot fall out of step with the sentence.
CATALYST_NEAR_TERM_SCORE = catalyst_score(NEAR_TERM_DAYS)


def is_near_term(days: int) -> bool:
    """Return whether a distance falls inside the near term window."""
    return days <= NEAR_TERM_DAYS
