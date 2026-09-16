"""Tests for the Yahoo Finance market data provider (Sprint 13).

The provider is exercised through a stand-in transport, so the tests describe
what the provider does with an answer rather than depending on the network.
Three cases are covered: a source that answers, a source that answers without
some metrics, and a source that cannot be reached.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from contracts.market_data_provider import MarketDataSnapshot, MarketMetric
from data.yahoo_market_data_provider import SOURCE_NAME, YahooMarketDataProvider
from utils.exceptions import DataError

_SYMBOL = "AAPL"


class _FakeTransport:
    """Stand-in transport that answers from a fixed table.

    A table entry is matched against the requested URL by fragment, and an entry
    holding an exception is raised instead of returned.
    """

    def __init__(self, answers: dict[str, str | Exception]) -> None:
        self._answers = answers
        self.requested: list[str] = []

    def get(self, url: str) -> str:
        self.requested.append(url)
        for fragment, answer in self._answers.items():
            if fragment in url:
                if isinstance(answer, Exception):
                    raise answer
                return answer
        raise DataError(f"unexpected request to {url}")

    def calls_to(self, fragment: str) -> int:
        """Return how many requests contained a fragment."""
        return sum(1 for url in self.requested if fragment in url)


def _summary(**modules: dict[str, object]) -> str:
    """Return a quote summary payload built from the given modules."""
    return json.dumps({"quoteSummary": {"result": [modules]}})


def _full_summary() -> str:
    """Return a quote summary with every published metric present."""
    return _summary(
        summaryDetail={
            "trailingPE": {"raw": 32.29},
            "marketCap": {"raw": 5.11e12},
        },
        defaultKeyStatistics={
            "pegRatio": {"raw": 1.45},
            "enterpriseToEbitda": {"raw": 24.6},
        },
        financialData={"freeCashflow": {"raw": 6.0e10}},
    )


def _transport(summary: str | Exception) -> _FakeTransport:
    """Return a transport answering the session handshake and a summary."""
    return _FakeTransport(
        {
            "fc.yahoo.com": DataError("HTTP 404 from fc.yahoo.com"),
            "getcrumb": "token-1",
            "quoteSummary": summary,
        }
    )


def _fetch(summary: str | Exception) -> MarketDataSnapshot:
    """Fetch a symbol through a transport answering with the given summary."""
    return YahooMarketDataProvider(_transport(summary)).fetch(_SYMBOL)


def _values(snapshot: MarketDataSnapshot) -> dict[MarketMetric, float | None]:
    """Return the retrieved value of every metric in a snapshot."""
    return {point.metric: point.value for point in snapshot.points}


def test_provider_success_returns_every_published_metric() -> None:
    snapshot = _fetch(_full_summary())
    values = _values(snapshot)

    assert snapshot.symbol == _SYMBOL
    assert snapshot.source == SOURCE_NAME
    assert isinstance(snapshot.retrieved_at, datetime)
    assert snapshot.is_live is True
    assert set(values) == set(MarketMetric)

    assert values[MarketMetric.PE] == pytest.approx(32.29)
    assert values[MarketMetric.PEG] == pytest.approx(1.45)
    assert values[MarketMetric.EV_EBITDA] == pytest.approx(24.6)
    assert values[MarketMetric.FCF_YIELD] == pytest.approx(6.0e10 / 5.11e12)


def test_provider_records_why_a_metric_could_not_be_retrieved() -> None:
    snapshot = _fetch(_full_summary())

    for point in snapshot.points:
        assert point.reason, f"{point.metric.value} carries no reason"

    dcf = snapshot.point(MarketMetric.DCF)
    assert dcf.value is None
    assert "valuation model" in dcf.reason
    assert len(snapshot.available_points) == 4
    # Every risk measurement is absent from this summary, and so is the DCF
    # fair value, which no source can supply.
    assert len(snapshot.missing_points) == len(MarketMetric) - 4


def test_provider_reuses_the_access_token_across_requests() -> None:
    transport = _transport(_full_summary())
    provider = YahooMarketDataProvider(transport)

    provider.fetch(_SYMBOL)
    provider.fetch(_SYMBOL)

    assert transport.calls_to("getcrumb") == 1
    assert transport.calls_to("quoteSummary") == 2


def test_provider_missing_data_leaves_the_metric_empty_and_explains_it() -> None:
    summary = _summary(
        summaryDetail={"trailingPE": {"raw": 32.29}},
        defaultKeyStatistics={},
        financialData={},
    )
    snapshot = _fetch(summary)
    values = _values(snapshot)

    assert values[MarketMetric.PE] == pytest.approx(32.29)

    peg = snapshot.point(MarketMetric.PEG)
    assert peg.value is None
    assert "did not report" in peg.reason

    fcf_yield = snapshot.point(MarketMetric.FCF_YIELD)
    assert fcf_yield.value is None
    assert "could not be computed" in fcf_yield.reason

    assert snapshot.is_live is True
    assert len(snapshot.missing_points) == len(MarketMetric) - 1


def test_provider_failure_is_reported_and_never_raises() -> None:
    snapshot = _fetch(DataError("HTTP 429 from query1.finance.yahoo.com"))

    assert snapshot.symbol == _SYMBOL
    assert snapshot.source == SOURCE_NAME
    assert snapshot.is_live is False
    assert len(snapshot.points) == len(MarketMetric)
    assert len(snapshot.missing_points) == len(MarketMetric)

    for point in snapshot.points:
        assert point.value is None
        assert point.reason

    pe = snapshot.point(MarketMetric.PE)
    assert "could not provide" in pe.reason

    # The DCF metric is unavailable whatever the state of the source is, so its
    # reason still states the real cause rather than the connection failure.
    dcf = snapshot.point(MarketMetric.DCF)
    assert "valuation model" in dcf.reason
