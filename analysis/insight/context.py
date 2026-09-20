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
from contracts.market_data_provider import MARKET_EVIDENCE_ID
from contracts.market_environment import (
    ENVIRONMENT_EVIDENCE_ID,
    ENVIRONMENT_SECTOR_EVIDENCE_ID,
    EnvironmentMetric,
)
from evaluation.reading.bands import (
    Band,
    ReadableMetric,
    band_for,
    scale_for,
    score_for,
)
from evaluation.reading.category import CategoryReading, read_category
from models.asset_profile import AssetProfile
from models.catalyst_event import CatalystEvent
from models.category import Category
from models.category_rating import CategoryRating
from models.sector import Sector


@dataclass(frozen=True)
class InsightContext:
    """One category's evidence, read and ready to be interpreted.

    Attributes:
        category: Category being interpreted.
        ticker: Symbol the evidence belongs to.
        profile: What kind of instrument the asset was declared to be. What kind of
            thing an asset is decides which questions apply to it and which
            environments bear on it, so a sentence needs it beside the readings.
        sector: The part of the market the asset was declared to be in, or None when
            nobody has stated one. It decides which part of the market this asset is
            compared with, and an asset with none is compared with nothing.
        values: Every measurement that was retrieved, keyed by metric. It holds the
            asset's own measurements and the environment's, because a category's
            question is answered by both and a builder should not have to know which
            of the two it is asking about. A metric that is absent was not
            retrieved, and a builder must behave as though the clause it would have
            written does not exist.
        reading: What this category's own measurements read as.
        events: The forthcoming events, for the category that reads a calendar.
        moment: Moment the reading is taken against.
        rating: Where the category stood last time and how it has moved, or None
            when there is nothing to compare with.
    """

    category: Category
    ticker: str
    profile: AssetProfile
    sector: Sector | None
    values: Mapping[ReadableMetric, float]
    reading: CategoryReading
    events: tuple[CatalystEvent, ...]
    moment: datetime
    rating: CategoryRating | None

    def has(self, *metrics: ReadableMetric) -> bool:
        """Return whether every one of these measurements was retrieved."""
        return all(metric in self.values for metric in metrics)

    def has_any(self, *metrics: ReadableMetric) -> bool:
        """Return whether any one of these measurements was retrieved."""
        return any(metric in self.values for metric in metrics)

    def value(self, metric: ReadableMetric) -> float | None:
        """Return one measurement, or None when it was not retrieved."""
        return self.values.get(metric)

    def band(self, metric: ReadableMetric) -> Band | None:
        """Return the band a measurement reads in, or None when it was not read.

        A builder compares bands rather than raw numbers, so the thresholds stay in
        one table and a sentence cannot drift away from the grade beside it.
        """
        value = self.values.get(metric)
        return None if value is None else band_for(metric, value)

    def word(self, metric: ReadableMetric) -> str | None:
        """Return how a measurement is described, or None when it was not read."""
        band = self.band(metric)
        return None if band is None else band.word

    def score(self, metric: ReadableMetric) -> int | None:
        """Return how a measurement scores, or None when it is not scored."""
        value = self.values.get(metric)
        return None if value is None else score_for(metric, value)

    def is_absent(self, metric: ReadableMetric) -> bool:
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

    def is_at_least(self, metric: ReadableMetric, score: int) -> bool:
        """Return whether a measurement reads at or above a score.

        The score is the position of a band, so asking this way keeps the
        thresholds in the reading layer while letting a sentence choose its phrase.
        """
        value = self.score(metric)
        return value is not None and value >= score

    def is_at_most(self, metric: ReadableMetric, score: int) -> bool:
        """Return whether a measurement reads at or below a score."""
        value = self.score(metric)
        return value is not None and value <= score

    def moved(self, metric: ReadableMetric) -> bool:
        """Return whether a measurement was read and has changed.

        What counts as unchanged is the band the reading layer marks as flat, so a
        sentence that says something moved and the reading beside it cannot disagree
        about it. A measurement that was not read has not moved: a sentence must not
        claim a change nobody measured.
        """
        band = self.band(metric)
        return band is not None and not band.is_flat

    def rose(self, metric: ReadableMetric) -> bool:
        """Return whether a measurement moved, and moved upwards.

        The band says whether it moved at all and the value says which way, so a
        scale whose flat band is marked answers "did this change" without a second
        threshold being invented for it.
        """
        value = self.values.get(metric)
        return self.moved(metric) and value is not None and value > 0

    def fell(self, metric: ReadableMetric) -> bool:
        """Return whether a measurement moved, and moved downwards."""
        value = self.values.get(metric)
        return self.moved(metric) and value is not None and value < 0

    def reference(self, *metrics: ReadableMetric) -> tuple[str, ...]:
        """Return the evidence identifiers behind these measurements.

        A builder calls this with exactly the measurements its sentence was read
        from, so that the sentence carries the reason it can be said at all. Which
        item an identifier points at depends on whose measurement it is: the asset's
        own evidence carries its ticker, and the environment's carries none, because
        the fact belongs to the market rather than to this asset.
        """
        return tuple(
            _evidence_id(self.ticker, metric, self.sector)
            for metric in metrics
            if metric in self.values
        )

    def event_reference(self, event: CatalystEvent) -> str:
        """Return the evidence identifier of one dated event."""
        return CATALYST_EVIDENCE_ID.format(
            ticker=self.ticker, kind=event.kind.value, date=event.occurs_on
        )


def _evidence_id(ticker: str, metric: ReadableMetric, sector: Sector | None) -> str:
    """Return the evidence identifier of one measurement.

    Which item an identifier points at depends on whose measurement it is, and there
    are three answers: the asset's own evidence carries its ticker, the market's
    carries none because the fact belongs to the market, and a sector's carries the
    sector, because that is what makes it a different fact from the next sector's.
    """
    if metric is EnvironmentMetric.SECTOR_RELATIVE_MOVE:
        if sector is None:
            return ENVIRONMENT_EVIDENCE_ID.format(metric=metric.value)
        return ENVIRONMENT_SECTOR_EVIDENCE_ID.format(sector=sector.value)
    if isinstance(metric, EnvironmentMetric):
        return ENVIRONMENT_EVIDENCE_ID.format(metric=metric.value)
    return MARKET_EVIDENCE_ID.format(ticker=ticker, metric=metric.value)


def context_for(result: AnalysisResult, category: Category) -> InsightContext:
    """Return the interpretation context for one category of a result.

    The measurements offered are every one that was retrieved, and not only the
    ones the category's evaluator scores. The two sets are different on purpose: an
    evaluator must score only what answers its question, while an interpretation
    may need a second number to say what the first one means — a multiple means one
    thing beside a growing business and another beside a shrinking one. Every
    sentence still names the measurements it was read from, so the wider reach costs
    no traceability.

    The environment's measurements are offered the same way, because they are part
    of the evidence for one category and nothing else: what the market is doing is
    read beside what the asset is doing, and the sentence that comes out is about
    the asset. The sector reading is offered as a value like any other, taken from the
    reading rather than from a point, because the sector that matters is this asset's
    own and the environment holds one reading per sector rather than one for the
    market.
    """
    snapshot = result.market_data
    environment = result.environment
    sector = result.asset.sector
    reading = read_category(snapshot, category, environment=environment, sector=sector)
    values: dict[ReadableMetric, float] = {
        **(
            {}
            if snapshot is None
            else {
                point.metric: point.value
                for point in snapshot.available_points
                if point.value is not None
            }
        ),
        **(
            {}
            if environment is None
            else {
                point.metric: point.value
                for point in environment.available_points
                if point.value is not None
            }
        ),
    }
    move = reading.read(EnvironmentMetric.SECTOR_RELATIVE_MOVE)
    if move is not None:
        values[move.metric] = move.value
    return InsightContext(
        category=category,
        ticker=result.asset.ticker,
        profile=result.asset.profile,
        sector=sector,
        values=values,
        reading=reading,
        events=result.events,
        moment=_moment_for(result),
        rating=result.rating_for(category),
    )


def _moment_for(result: AnalysisResult) -> datetime:
    """Return the moment a reading is measured against."""
    snapshot = result.market_data
    return datetime.now() if snapshot is None else snapshot.retrieved_at
