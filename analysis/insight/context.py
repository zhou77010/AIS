"""What a category's evidence is read as, when it is interpreted.

An insight builder needs three things: how each measurement it might mention reads,
the dated events if it is the catalyst, and a way to name the evidence a sentence
was read from. This module holds all three, so no builder reimplements the lookup
and no builder decides for itself what a number means.

**A builder asks for a reading, never for a threshold.** The words and the bands
come from the reading layer, so a sentence and the grade beside it are reading the
same scale. When they were separate, a report could call a valuation attractive
directly above a sentence saying the cash flow did not support it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from analysis.analysis_result import AnalysisResult
from contracts.catalyst_event_provider import CATALYST_EVIDENCE_ID
from contracts.market_data_provider import MARKET_EVIDENCE_ID, MarketMetric
from evaluation.reading.bands import Band, band_for, scale_for, score_for
from evaluation.reading.category import CategoryReading, read_category
from models.catalyst_event import CatalystEvent
from models.category import Category
from models.category_rating import CategoryRating


@dataclass(frozen=True)
class InsightContext:
    """One category's evidence, read and ready to be interpreted.

    Attributes:
        category: Category being interpreted.
        ticker: Symbol the evidence belongs to.
        values: Every measurement that was retrieved, keyed by metric. A metric
            that is absent was not retrieved, and a builder must behave as though
            the clause it would have written does not exist.
        reading: What this category's own measurements read as.
        events: The forthcoming events, for the category that reads a calendar.
        moment: Moment the reading is taken against.
        rating: Where the category stood last time and how it has moved, or None
            when there is nothing to compare with.
    """

    category: Category
    ticker: str
    values: Mapping[MarketMetric, float]
    reading: CategoryReading
    events: tuple[CatalystEvent, ...]
    moment: datetime
    rating: CategoryRating | None

    def has(self, *metrics: MarketMetric) -> bool:
        """Return whether every one of these measurements was retrieved."""
        return all(metric in self.values for metric in metrics)

    def has_any(self, *metrics: MarketMetric) -> bool:
        """Return whether any one of these measurements was retrieved."""
        return any(metric in self.values for metric in metrics)

    def value(self, metric: MarketMetric) -> float | None:
        """Return one measurement, or None when it was not retrieved."""
        return self.values.get(metric)

    def band(self, metric: MarketMetric) -> Band | None:
        """Return the band a measurement reads in, or None when it was not read.

        A builder compares bands rather than raw numbers, so the thresholds stay in
        one table and a sentence cannot drift away from the grade beside it.
        """
        value = self.values.get(metric)
        return None if value is None else band_for(metric, value)

    def word(self, metric: MarketMetric) -> str | None:
        """Return how a measurement is described, or None when it was not read."""
        band = self.band(metric)
        return None if band is None else band.word

    def score(self, metric: MarketMetric) -> int | None:
        """Return how a measurement scores, or None when it is not scored."""
        value = self.values.get(metric)
        return None if value is None else score_for(metric, value)

    def is_absent(self, metric: MarketMetric) -> bool:
        """Return whether a negative reading means the quantity measured against
        is not there rather than that the reading is low.

        A negative price to earnings ratio means a loss, not a bargain. A sentence
        that called it cheap would say the opposite of the truth, so the builder
        asks this before it reads the band.
        """
        scale = scale_for(metric)
        value = self.values.get(metric)
        if scale is None or value is None or not scale.negative_means_absent:
            return False
        return value < 0

    def is_at_least(self, metric: MarketMetric, score: int) -> bool:
        """Return whether a measurement reads at or above a score.

        The score is the position of a band, so asking this way keeps the
        thresholds in the reading layer while letting a sentence choose its phrase.
        """
        value = self.score(metric)
        return value is not None and value >= score

    def is_at_most(self, metric: MarketMetric, score: int) -> bool:
        """Return whether a measurement reads at or below a score."""
        value = self.score(metric)
        return value is not None and value <= score

    def reference(self, *metrics: MarketMetric) -> tuple[str, ...]:
        """Return the evidence identifiers behind these measurements.

        A builder calls this with exactly the measurements its sentence was read
        from, so that the sentence carries the reason it can be said at all.
        """
        return tuple(
            MARKET_EVIDENCE_ID.format(ticker=self.ticker, metric=metric.value)
            for metric in metrics
            if metric in self.values
        )

    def event_reference(self, event: CatalystEvent) -> str:
        """Return the evidence identifier of one dated event."""
        return CATALYST_EVIDENCE_ID.format(
            ticker=self.ticker, kind=event.kind.value, date=event.occurs_on
        )


def context_for(result: AnalysisResult, category: Category) -> InsightContext:
    """Return the interpretation context for one category of a result.

    The measurements offered are every one that was retrieved, and not only the
    ones the category's evaluator scores. The two sets are different on purpose: an
    evaluator must score only what answers its question, while an interpretation
    may need a second number to say what the first one means — a multiple means one
    thing beside a growing business and another beside a shrinking one. Every
    sentence still names the measurements it was read from, so the wider reach costs
    no traceability.
    """
    snapshot = result.market_data
    return InsightContext(
        category=category,
        ticker=result.asset.ticker,
        values=(
            {}
            if snapshot is None
            else {
                point.metric: point.value
                for point in snapshot.available_points
                if point.value is not None
            }
        ),
        reading=read_category(snapshot, category),
        events=result.events,
        moment=_moment_for(result),
        rating=result.rating_for(category),
    )


def _moment_for(result: AnalysisResult) -> datetime:
    """Return the moment a reading is measured against."""
    snapshot = result.market_data
    return datetime.now() if snapshot is None else snapshot.retrieved_at
