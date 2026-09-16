"""Market data readings taken from an evidence collection.

Every category evaluator takes its measurements from the evidence, and the
evidence is where a missing measurement is explained. This module is the single
place that knows how a market metric is written into the evidence and how it is
read back, so no evaluator reimplements the lookup.
"""

from __future__ import annotations

from dataclasses import dataclass

from contracts.market_data_provider import (
    METRIC_METADATA_KEY,
    VALUE_METADATA_KEY,
    MarketMetric,
)
from evidence.evidence_collection import EvidenceCollection


@dataclass(frozen=True)
class MetricReading:
    """One market metric as the evidence records it.

    Attributes:
        value: Retrieved value, or None when the metric could not be retrieved.
        reason: Where the value came from, or why it is missing.
        evidence_id: Identifier of the evidence item carrying the reading.
    """

    value: float | None
    reason: str
    evidence_id: str


def read_metric(
    evidence: EvidenceCollection, metric: MarketMetric
) -> MetricReading | None:
    """Return the reading the evidence holds for one market metric.

    Args:
        evidence: Evidence collected for the asset.
        metric: Metric to look up.

    Returns:
        The recorded reading, or None when the collection carries no market data
        at all, which is how a collection built without a market data source
        looks. A reading whose value is None means the source was asked and did
        not provide the metric; its reason states why.
    """
    for item in evidence.items:
        if item.metadata.get(METRIC_METADATA_KEY) != metric.value:
            continue
        return MetricReading(
            value=_to_float(item.metadata.get(VALUE_METADATA_KEY)),
            reason=item.description,
            evidence_id=item.id,
        )
    return None


def _to_float(raw: str | None) -> float | None:
    """Return the value recorded in evidence metadata, or None when it holds none.

    Evidence metadata is text by contract, so a retrieved number is stored in
    its round-trippable form and parsed back here.
    """
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
