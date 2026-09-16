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

from models.category import Category

# Keys used in the metadata of the evidence items that carry a market metric.
# They are defined once, here, because the pipeline writes them and the
# valuation rules read them.
METRIC_METADATA_KEY = "market_metric"
VALUE_METADATA_KEY = "market_value"


class MarketMetric(StrEnum):
    """A single market measurement AIS consumes.

    A measurement is evidence. It never defines the category it serves, and it
    may serve more than one: the same fact can support two categories when they
    ask different questions. What is forbidden is one fact answering the same
    question twice under two names, not one fact being read twice.
    """

    PE = "pe"
    PEG = "peg"
    EV_EBITDA = "ev_ebitda"
    FCF_YIELD = "fcf_yield"
    DCF = "dcf"
    BETA = "beta"
    DEBT_TO_EQUITY = "debt_to_equity"
    CURRENT_RATIO = "current_ratio"
    AVERAGE_VOLUME = "average_volume"
    FLOAT_SHARES = "float_shares"
    PROFIT_MARGIN = "profit_margin"
    RETURN_ON_EQUITY = "return_on_equity"
    FREE_CASH_FLOW_MARGIN = "free_cash_flow_margin"
    MARKET_DIRECTION = "market_direction"

    @property
    def label(self) -> str:
        """Return the human readable name of the metric."""
        return _METRIC_LABELS[self]

    @property
    def categories(self) -> tuple[Category, ...]:
        """Return the categories whose question this measurement helps answer.

        The first entry is the primary category, which is where the evidence
        item is filed and how a renderer groups it. The rest are the categories
        that also read the measurement.
        """
        return _METRIC_CATEGORIES[self]

    @property
    def primary_category(self) -> Category:
        """Return the category the evidence for this measurement is filed under."""
        return self.categories[0]


_METRIC_LABELS: dict[MarketMetric, str] = {
    MarketMetric.PE: "Trailing P/E",
    MarketMetric.PEG: "PEG ratio",
    MarketMetric.EV_EBITDA: "EV/EBITDA",
    MarketMetric.FCF_YIELD: "Free cash flow yield",
    MarketMetric.DCF: "DCF fair value",
    MarketMetric.BETA: "Beta",
    MarketMetric.DEBT_TO_EQUITY: "Debt to equity",
    MarketMetric.CURRENT_RATIO: "Current ratio",
    MarketMetric.AVERAGE_VOLUME: "Average volume",
    MarketMetric.FLOAT_SHARES: "Shares in float",
    MarketMetric.PROFIT_MARGIN: "Net profit margin",
    MarketMetric.RETURN_ON_EQUITY: "Return on equity",
    MarketMetric.FREE_CASH_FLOW_MARGIN: "Free cash flow margin",
    MarketMetric.MARKET_DIRECTION: "Broad market 52 week change",
}

# Debt to equity and the current ratio are read by Risk and by Fundamental.
# Risk asks how exposed a thesis is to the state of the balance sheet;
# Fundamental asks what that state is. One measurement, two questions.
_METRIC_CATEGORIES: dict[MarketMetric, tuple[Category, ...]] = {
    MarketMetric.PE: (Category.VALUATION,),
    MarketMetric.PEG: (Category.VALUATION,),
    MarketMetric.EV_EBITDA: (Category.VALUATION,),
    MarketMetric.FCF_YIELD: (Category.VALUATION,),
    MarketMetric.DCF: (Category.VALUATION,),
    MarketMetric.BETA: (Category.RISK,),
    MarketMetric.DEBT_TO_EQUITY: (Category.RISK, Category.FUNDAMENTAL),
    MarketMetric.CURRENT_RATIO: (Category.RISK, Category.FUNDAMENTAL),
    MarketMetric.AVERAGE_VOLUME: (Category.RISK,),
    MarketMetric.FLOAT_SHARES: (Category.RISK,),
    MarketMetric.PROFIT_MARGIN: (Category.FUNDAMENTAL,),
    MarketMetric.RETURN_ON_EQUITY: (Category.FUNDAMENTAL,),
    MarketMetric.FREE_CASH_FLOW_MARGIN: (Category.FUNDAMENTAL,),
    MarketMetric.MARKET_DIRECTION: (Category.MARKET,),
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
