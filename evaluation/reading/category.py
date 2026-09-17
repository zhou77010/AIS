"""What one category's measurements mean, read together.

The scales say what a single number means. This says what a category's
measurements mean together, and it is the only place that reduction happens. A
grade is the mean of the readings; a sentence uses their words; an opportunity
condition reads the mean and the weakest reading both. None of the three decides
again for itself, which is what stops them disagreeing.

**The mean is not the whole reading, and it never was.** A category whose average
looks good can hold a measurement that disqualifies it — a valuation with a
negative cash flow yield averages out to attractive if the multiples are generous
enough. That is why a reading carries its weakest member as well as its mean, and
why the opportunity judgement asks about both.
"""

from __future__ import annotations

from dataclasses import dataclass

from contracts.market_data_provider import MarketDataSnapshot, MarketMetric
from evaluation.reading.bands import Band, band_for, score_for
from models.category import Category


@dataclass(frozen=True)
class MetricRead:
    """One measurement, and what it was read as.

    Attributes:
        metric: Measurement that was read.
        value: The value retrieved.
        band: The band it fell in.
        score: How it scored, or None when this measurement is only described.
    """

    metric: MarketMetric
    value: float
    band: Band
    score: int | None


@dataclass(frozen=True)
class CategoryReading:
    """Every measurement of one category, read together.

    Attributes:
        category: Category that was read.
        reads: One entry per measurement that has a scale, in the order the
            snapshot holds them.
    """

    category: Category
    reads: tuple[MetricRead, ...]

    @property
    def is_empty(self) -> bool:
        """Return whether nothing about this category could be read."""
        return not self.reads

    @property
    def scored(self) -> tuple[int, ...]:
        """Return the scores of the measurements that carry one."""
        return tuple(read.score for read in self.reads if read.score is not None)

    @property
    def mean_score(self) -> int | None:
        """Return the rounded mean of the scored readings, or None when none are.

        None means nothing was read rather than that the reading was poor, so a
        caller shows no grade instead of the lowest one.
        """
        scores = self.scored
        if not scores:
            return None
        return max(1, min(5, round(sum(scores) / len(scores))))

    @property
    def weakest_score(self) -> int | None:
        """Return the lowest score among the readings, or None when none are scored."""
        scores = self.scored
        return min(scores) if scores else None

    @property
    def weakest(self) -> MetricRead | None:
        """Return the measurement that reads worst, or None when none are scored."""
        scored = [read for read in self.reads if read.score is not None]
        if not scored:
            return None
        return min(scored, key=lambda read: read.score or 0)

    def read(self, metric: MarketMetric) -> MetricRead | None:
        """Return the reading of one measurement, or None when it was not read."""
        for read in self.reads:
            if read.metric is metric:
                return read
        return None

    def word(self, metric: MarketMetric) -> str | None:
        """Return how one measurement of this category is described."""
        read = self.read(metric)
        return None if read is None else read.band.word


def read_category(
    snapshot: MarketDataSnapshot | None, category: Category
) -> CategoryReading:
    """Read every measurement of one category that has a scale.

    Args:
        snapshot: Market data of the run, or None when no source was consulted.
        category: Category to read.

    Returns:
        The reading, empty when no measurement of the category was retrieved.
    """
    if snapshot is None:
        return CategoryReading(category=category, reads=())
    reads: list[MetricRead] = []
    for point in snapshot.available_points:
        if category not in point.metric.categories or point.value is None:
            continue
        band = band_for(point.metric, point.value)
        if band is None:
            continue
        reads.append(
            MetricRead(
                metric=point.metric,
                value=point.value,
                band=band,
                score=score_for(point.metric, point.value),
            )
        )
    return CategoryReading(category=category, reads=tuple(reads))
