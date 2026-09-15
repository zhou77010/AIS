"""Contract for market data providers.

A market data provider is any source of raw market data. This module defines the
interface and the value objects exchanged across the boundary, and holds no
implementation and no vendor specifics.

The value objects live here because they are produced by the Data layer and
consumed by the Core Engine, and this contract layer is the only place both may
depend on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

# Keys used in the metadata of the evidence items that carry a market metric.
# They are defined once, here, because the pipeline writes them and the
# valuation rules read them.
METRIC_METADATA_KEY = "market_metric"
VALUE_METADATA_KEY = "market_value"


class MarketMetric(StrEnum):
    """A single market measurement the valuation rules consume."""

    PE = "pe"
    PEG = "peg"
    EV_EBITDA = "ev_ebitda"
    FCF_YIELD = "fcf_yield"
    DCF = "dcf"

    @property
    def label(self) -> str:
        """Return the human readable name of the metric."""
        return _METRIC_LABELS[self]


_METRIC_LABELS: dict[MarketMetric, str] = {
    MarketMetric.PE: "Trailing P/E",
    MarketMetric.PEG: "PEG ratio",
    MarketMetric.EV_EBITDA: "EV/EBITDA",
    MarketMetric.FCF_YIELD: "Free cash flow yield",
    MarketMetric.DCF: "DCF fair value",
}


@dataclass(frozen=True)
class MarketDataPoint:
    """One market metric as a source reported it, retrieved or not.

    A point with no value is not an error: it records that the source did not
    provide the metric, together with the reason, so that the absence stays
    traceable. A provider never invents a value to fill a gap.

    Attributes:
        metric: Metric the point is about.
        value: Retrieved value, or None when it could not be retrieved.
        reason: Where the value came from, or why it is missing.
    """

    metric: MarketMetric
    value: float | None
    reason: str


@dataclass(frozen=True)
class MarketDataSnapshot:
    """Every market metric retrieved for one symbol at one moment.

    The snapshot always carries one point per :class:`MarketMetric`, so that a
    metric the source could not provide is still visible and explained.

    Attributes:
        symbol: Symbol the data was retrieved for.
        source: Name of the source the data came from.
        retrieved_at: Moment the data was retrieved.
        points: One point per metric.
    """

    symbol: str
    source: str
    retrieved_at: datetime
    points: tuple[MarketDataPoint, ...]

    @property
    def available_points(self) -> tuple[MarketDataPoint, ...]:
        """Return the points that carry a retrieved value."""
        return tuple(point for point in self.points if point.value is not None)

    @property
    def missing_points(self) -> tuple[MarketDataPoint, ...]:
        """Return the points the source could not provide."""
        return tuple(point for point in self.points if point.value is None)

    @property
    def is_live(self) -> bool:
        """Return whether at least one metric was retrieved."""
        return bool(self.available_points)

    def point(self, metric: MarketMetric) -> MarketDataPoint:
        """Return the point recorded for one metric.

        Args:
            metric: Metric to look up.

        Returns:
            The point the snapshot holds for the metric.

        Raises:
            KeyError: When the snapshot holds no point for the metric.
        """
        for point in self.points:
            if point.metric is metric:
                return point
        raise KeyError(f"no market data point recorded for {metric.value}")


class MarketDataProvider(Protocol):
    """Contract for any market data source."""

    def fetch(self, symbol: str) -> MarketDataSnapshot:
        """Return the market data retrieved for a symbol.

        Implementations never raise and never invent a value: a metric the
        source cannot provide is returned as a point without a value that
        explains why, so a failing source degrades the analysis instead of
        stopping it.

        Args:
            symbol: Trading symbol the data is requested for.

        Returns:
            Snapshot holding one point per metric.
        """
