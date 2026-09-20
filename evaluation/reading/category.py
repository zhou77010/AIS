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

from collections.abc import Iterable
from dataclasses import dataclass

from contracts.market_data_provider import MarketDataSnapshot
from contracts.market_environment import EnvironmentMetric, EnvironmentSnapshot
from evaluation.reading.bands import Band, ReadableMetric, band_for, score_for
from models.category import Category
from models.sector import Sector


@dataclass(frozen=True)
class MetricRead:
    """One measurement, and what it was read as.

    Attributes:
        metric: Measurement that was read.
        value: The value retrieved.
        band: The band it fell in.
        score: How it scored, or None when this measurement is only described.
    """

    metric: ReadableMetric
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

    def read(self, metric: ReadableMetric) -> MetricRead | None:
        """Return the reading of one measurement, or None when it was not read."""
        for read in self.reads:
            if read.metric is metric:
                return read
        return None

    def word(self, metric: ReadableMetric) -> str | None:
        """Return how one measurement of this category is described."""
        read = self.read(metric)
        return None if read is None else read.band.word


def read_category(
    snapshot: MarketDataSnapshot | None,
    category: Category,
    *,
    environment: EnvironmentSnapshot | None = None,
    sector: Sector | None = None,
) -> CategoryReading:
    """Read every measurement of one category that has a scale.

    A category is read from three places, and they are different in kind. The snapshot
    carries what the source reported about **this asset**. The environment carries what
    the market itself is doing, which is the same for every asset in it and is
    retrieved once. The sector carries how this asset's own part of the market is doing
    against the rest of it, which is the same for every asset in that sector and
    nothing like the same for an asset in another.

    All three are read here, together, because a category's question is answered by all
    of its measurements and not only by the ones that belong to the asset.

    Args:
        snapshot: Market data of the run, or None when no source was consulted.
        category: Category to read.
        environment: The environment the run was judged in, or None when none was
            retrieved.
        sector: The part of the market the asset is in, or None when nobody has stated
            one. Without it there is no sector to compare and the asset is told nothing
            about one.

    Returns:
        The reading, empty when no measurement of the category was retrieved.
    """
    reads = [
        *_entity_reads(snapshot, category),
        *_environment_reads(environment, category),
        *_sector_reads(environment, category, sector),
    ]
    return CategoryReading(category=category, reads=tuple(reads))


def _entity_reads(
    snapshot: MarketDataSnapshot | None, category: Category
) -> list[MetricRead]:
    """Return the readings of the asset's own measurements for one category."""
    if snapshot is None:
        return []
    return _reads(
        (
            (point.metric, point.value)
            for point in snapshot.available_points
            if point.value is not None
        ),
        category,
    )


def _environment_reads(
    environment: EnvironmentSnapshot | None, category: Category
) -> list[MetricRead]:
    """Return the readings of the environment's measurements for one category."""
    if environment is None:
        return []
    return _reads(
        (
            (point.metric, point.value)
            for point in environment.available_points
            if point.value is not None
        ),
        category,
    )


def _sector_reads(
    environment: EnvironmentSnapshot | None,
    category: Category,
    sector: Sector | None,
) -> list[MetricRead]:
    """Return the reading of the part of the market this asset is in.

    One reading, because there is one sector: the sector an asset belongs to is the
    comparison that matters to it, and the others are other people's comparisons.
    """
    move = None if environment is None else environment.sector_move(sector)
    if move is None:
        return []
    return _reads(
        ((EnvironmentMetric.SECTOR_RELATIVE_MOVE, move.value),),
        category,
    )


def _reads(
    measurements: Iterable[tuple[ReadableMetric, float | None]], category: Category
) -> list[MetricRead]:
    """Return one reading per measurement that has a scale and serves the category."""
    reads: list[MetricRead] = []
    for metric, value in measurements:
        if value is None or category not in metric.categories:
            continue
        band = band_for(metric, value)
        if band is None:
            continue
        reads.append(
            MetricRead(
                metric=metric,
                value=value,
                band=band,
                score=score_for(metric, value),
            )
        )
    return reads
