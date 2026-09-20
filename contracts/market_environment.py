"""Contract for the environment every asset in a pass is judged in.

The market data provider answers about one symbol. Some facts are not about a symbol
at all: how the equity futures are trading overnight, how turbulent the market is,
what the cost of money is doing. Those are the same number for every asset in the
same market, so fetching them per asset would be fetching one fact seven times, and
the seven copies could disagree.

So they are retrieved once and shared. This module defines the measurements, the
value object they arrive in, and the provider contract; the Data layer implements
it, and the Core Engine reads it.

**Shared evidence is still evidence.** What arrives here goes into the same evidence
stream as everything else, under the Market category, and is read through the same
reading layer. What is different is only that it belongs to no ticker, which is why
its evidence identifier has no ticker in it.

**A market fact is not a judgement about an asset.** A rising yield is not bad for
every asset and a falling one is not good for every asset. This contract carries
what the environment is doing; what it means for a particular asset is read from
that asset's own measurements beside it, and it is read in
:mod:`analysis.insight.market_insight`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from models.category import Category

# Keys used in the metadata of the evidence items that carry an environment
# measurement. They are the same keys the per-asset market data uses, because a
# reader of the evidence should not have to know which of the two it is looking at.
METRIC_METADATA_KEY = "market_metric"
VALUE_METADATA_KEY = "market_value"

# How the evidence for one environment measurement is identified. It carries no
# ticker: the fact belongs to the market, not to an asset.
ENVIRONMENT_EVIDENCE_ID = "environment.{metric}"


class EnvironmentMetric(StrEnum):
    """One measurement of the environment, rather than of one asset.

    The set is deliberately small. Each member earns its place by being a fact AIS
    can retrieve from a source it already reads, and by having something to say
    about an asset beside that asset's own measurements. A member that could not be
    interpreted for any asset would be a number in search of a sentence.
    """

    OVERNIGHT_EQUITY = "overnight_equity"
    OVERNIGHT_GROWTH = "overnight_growth"
    VOLATILITY = "volatility"
    VOLATILITY_CHANGE = "volatility_change"
    TEN_YEAR_YIELD_CHANGE = "ten_year_yield_change"

    @property
    def label(self) -> str:
        """Return the human readable name of the measurement."""
        return _LABELS[self]

    @property
    def categories(self) -> tuple[Category, ...]:
        """Return the categories whose question this measurement helps answer.

        Every environment measurement serves Market and nothing else. It says what
        the conditions are, not what any asset is worth in them.
        """
        return (Category.MARKET,)

    @property
    def primary_category(self) -> Category:
        """Return the category the evidence for this measurement is filed under."""
        return Category.MARKET


_LABELS: dict[EnvironmentMetric, str] = {
    EnvironmentMetric.OVERNIGHT_EQUITY: "S&P 500 futures since the last close",
    EnvironmentMetric.OVERNIGHT_GROWTH: "Nasdaq 100 futures since the last close",
    EnvironmentMetric.VOLATILITY: "Volatility index level",
    EnvironmentMetric.VOLATILITY_CHANGE: "Volatility index change",
    EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: "Ten year yield change in basis points",
}


@dataclass(frozen=True)
class EnvironmentPoint:
    """One environment measurement as the source reported it, retrieved or not.

    A point with no value is not an error: it records that the source did not
    provide the measurement, together with the reason, so the absence stays
    traceable. A provider never invents a value to fill a gap.

    Attributes:
        metric: Measurement the point is about.
        value: Retrieved value, or None when it could not be retrieved.
        reason: What the value is and how it was derived, or why it is missing.
    """

    metric: EnvironmentMetric
    value: float | None
    reason: str


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """Every environment measurement retrieved at one moment.

    The snapshot always carries one point per :class:`EnvironmentMetric`, so a
    measurement the source could not provide is still visible and explained.

    Attributes:
        source: Name of the source the measurements came from.
        retrieved_at: Moment they were retrieved.
        points: One point per measurement.
    """

    source: str
    retrieved_at: datetime
    points: tuple[EnvironmentPoint, ...]

    @property
    def available_points(self) -> tuple[EnvironmentPoint, ...]:
        """Return the points that carry a retrieved value."""
        return tuple(point for point in self.points if point.value is not None)

    @property
    def missing_points(self) -> tuple[EnvironmentPoint, ...]:
        """Return the points the source could not provide."""
        return tuple(point for point in self.points if point.value is None)

    @property
    def is_live(self) -> bool:
        """Return whether at least one measurement was retrieved."""
        return bool(self.available_points)

    def point(self, metric: EnvironmentMetric) -> EnvironmentPoint:
        """Return the point recorded for one measurement.

        Args:
            metric: Measurement to look up.

        Returns:
            The point the snapshot holds for the measurement.

        Raises:
            KeyError: When the snapshot holds no point for the measurement.
        """
        for point in self.points:
            if point.metric is metric:
                return point
        raise KeyError(f"no environment point recorded for {metric.value}")


class EnvironmentProvider(Protocol):
    """Contract for a source of environment measurements."""

    def fetch(self) -> EnvironmentSnapshot:
        """Return the environment as it is at the moment of the call.

        Implementations never raise and never invent a value: a measurement the
        source cannot provide is returned as a point without a value that explains
        why, so an unreachable source degrades the analysis instead of stopping it.

        Returns:
            Snapshot holding one point per measurement.
        """
