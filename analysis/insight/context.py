"""What a category's evidence is read against when it is interpreted.

An insight builder needs three things: the measurements the category collected,
the dated events if it is Catalyst, and a way to name the evidence a sentence was
read from. This module holds all three, so no builder reimplements the lookup and
no builder has to know how an evidence identifier is spelled.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from analysis.analysis_result import AnalysisResult
from contracts.catalyst_event_provider import CATALYST_EVIDENCE_ID
from contracts.market_data_provider import MARKET_EVIDENCE_ID, MarketMetric
from models.catalyst_event import CatalystEvent
from models.category import Category
from models.category_rating import CategoryRating


@dataclass(frozen=True)
class InsightContext:
    """One category's evidence, ready to be interpreted.

    Attributes:
        category: Category being interpreted.
        ticker: Symbol the evidence belongs to.
        values: The measurements that were retrieved, keyed by metric. A metric
            that is absent was not retrieved, and a builder must behave as
            though the clause it would have written does not exist.
        events: The forthcoming events, for the category that reads a calendar.
        moment: Moment the reading is taken against.
        rating: Where the category stood last time and how it has moved, or None
            when there is nothing to compare with.
    """

    category: Category
    ticker: str
    values: Mapping[MarketMetric, float]
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
    ones the category's evaluator scores. The two sets are different on purpose:
    an evaluator must score only what answers its question, which is what a
    measurement's declared categories are for, while an interpretation may need a
    second number to say what the first one means — a multiple means one thing
    beside a growing business and another beside a shrinking one. Every sentence
    still names the measurements it was read from, so the wider reach costs no
    traceability.
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
        events=result.events,
        moment=_moment_for(result),
        rating=result.rating_for(category),
    )


def _moment_for(result: AnalysisResult) -> datetime:
    """Return the moment a reading is measured against."""
    snapshot = result.market_data
    return datetime.now() if snapshot is None else snapshot.retrieved_at
