"""The star grade a category is shown with.

The grade is a **view of the category's reading**, and nothing more. It does not
decide what a number means: the reading layer does that, once, for every consumer.
This module takes the reading's mean and turns it into stars, and it holds no
threshold of its own.

That is a change from how it worked. The grade used to own a table of thresholds
that the sentences then wrote down a second time, which is how a report ended up
saying an asset had a near term catalyst in one place and no clear catalyst in
another. There is one table now, and this module does not have a copy of it.

**The grade is provisional in the same way the reading is.** It is not the AIS
Standard Score and it is not method: it is a way of showing a mean on a phone. It
is replaced together with the reading layer, never on its own.
"""

from __future__ import annotations

from datetime import datetime

from analysis.analysis_result import AnalysisResult
from evaluation.reading.bands import MAX_SCORE, MIN_SCORE
from evaluation.reading.category import CategoryReading, read_category
from evaluation.reading.windows import catalyst_score
from models.category import Category

MIN_GRADE = MIN_SCORE
MAX_GRADE = MAX_SCORE


def grade_for_category(result: AnalysisResult, category: Category) -> int | None:
    """Return the grade for one category, or None when it has none.

    Args:
        result: Analysis result to read.
        category: Category to grade.

    Returns:
        A grade from one to five, or None when nothing about the category could be
        read. None means the report shows no grade rather than a low one, because
        nothing was read.
    """
    if category is Category.CATALYST:
        days = catalyst_days(result)
        return None if days is None else catalyst_score(days)
    return read_category(result.market_data, category).mean_score


def catalyst_days(result: AnalysisResult) -> int | None:
    """Return how far away the nearest event that could change a view is.

    A catalyst is read from a date rather than from a measurement, so it does not
    go through the scales. The window it is read against is the same one the
    sentences and the opportunity condition use, which is what stops them
    disagreeing about what counts as coming.

    The reading is the nearest such event, never how many there are: a crowded
    month and a quiet one read the same when the nearest thing is the same
    distance away. Events that move the price without moving a view are left out,
    so the reading does not improve because shares are about to go ex-dividend.
    """
    moment = moment_for(result)
    upcoming = [
        event
        for event in result.events
        if event.is_upcoming(moment) and not event.is_mechanical
    ]
    if not upcoming:
        return None
    return min(event.days_from(moment) for event in upcoming)


def moment_for(result: AnalysisResult) -> datetime:
    """Return the moment readings are measured against.

    The moment the data was retrieved is used when there is one, so that a report
    describes the run it came from. A run without market data has no such moment,
    and the current time is the only honest alternative.
    """
    snapshot = result.market_data
    return datetime.now() if snapshot is None else snapshot.retrieved_at


def reading_for(result: AnalysisResult, category: Category) -> CategoryReading:
    """Return the category's reading, for callers that need more than the grade."""
    return read_category(result.market_data, category)


def stars(grade: int) -> str:
    """Return the filled and empty stars for a grade."""
    filled = max(MIN_GRADE, min(MAX_GRADE, grade))
    return "★" * filled + "☆" * (MAX_GRADE - filled)
