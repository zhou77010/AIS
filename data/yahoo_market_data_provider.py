"""AIS Yahoo Finance market data provider.

Retrieves live market data from Yahoo Finance through its public endpoints. No
API key, no account and no third party package are required: the standard
library is enough.

The provider never raises and never invents a value. A metric that cannot be
retrieved is returned as a point without a value that states why, so a failing
source degrades the analysis instead of stopping it.

Design notes:

* Yahoo requires a session cookie plus a token derived from it. Both are
  obtained once per provider instance and reused for later requests.
* Free cash flow yield is not published as such; it is computed from the free
  cash flow and the market capitalisation the source reports, and the reason
  recorded with the point states that derivation.
* A discounted cash flow fair value is not a datum any market data source can
  publish, so it is always reported as unavailable rather than approximated.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from urllib.parse import quote

from config.logging_config import get_logger
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from data.http import HttpTransport, UrllibTransport
from utils.exceptions import DataError

SOURCE_NAME = "Yahoo Finance"

_LOGGER_NAME = "market_data"
_COOKIE_URL = "https://fc.yahoo.com"
_TOKEN_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
_SUMMARY_URL = (
    "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    "?modules=summaryDetail,defaultKeyStatistics,financialData&crumb={token}"
)
_DCF_REASON = (
    f"{MarketMetric.DCF.label} is not retrieved: it is the output of a valuation "
    f"model, not a datum a market data source publishes, and AIS has not defined "
    f"the model parameters. No value is invented to fill the gap."
)


class YahooMarketDataProvider:
    """Retrieves live market data from Yahoo Finance."""

    def __init__(self, transport: HttpTransport | None = None) -> None:
        """Create the provider.

        Args:
            transport: Transport to talk through. Defaults to the standard
                library transport; tests supply a stand-in.
        """
        self._transport: HttpTransport = (
            transport if transport is not None else UrllibTransport()
        )
        self._token: str | None = None
        self._logger = get_logger(_LOGGER_NAME)

    def fetch(self, symbol: str) -> MarketDataSnapshot:
        """Return the market data Yahoo Finance holds for a symbol.

        The call never raises. When the source cannot be reached, or answers
        with something unusable, the returned snapshot carries one point per
        metric without a value, each stating why it is missing.

        Args:
            symbol: Trading symbol to retrieve data for.

        Returns:
            Snapshot holding one point per metric.
        """
        retrieved_at = datetime.now()
        try:
            summary = self._request_summary(symbol)
        except Exception as error:  # noqa: BLE001 - the contract is to never raise
            detail = f"{type(error).__name__}: {error}"
            self._logger.warning(
                "market data for %s unavailable from %s: %s",
                symbol,
                SOURCE_NAME,
                detail,
            )
            reason = (
                f"{SOURCE_NAME} could not provide this metric, so it was not "
                f"retrieved ({detail})."
            )
            return self._snapshot(symbol, retrieved_at, _unavailable_points(reason))
        return self._snapshot(symbol, retrieved_at, _points(summary))

    def _snapshot(
        self,
        symbol: str,
        retrieved_at: datetime,
        points: tuple[MarketDataPoint, ...],
    ) -> MarketDataSnapshot:
        """Assemble a snapshot and log every metric that stayed unavailable."""
        snapshot = MarketDataSnapshot(
            symbol=symbol,
            source=SOURCE_NAME,
            retrieved_at=retrieved_at,
            points=points,
        )
        self._logger.info(
            "market data for %s: %d of %d metrics retrieved from %s",
            symbol,
            len(snapshot.available_points),
            len(snapshot.points),
            SOURCE_NAME,
        )
        return snapshot

    def _request_summary(self, symbol: str) -> Mapping[str, Any]:
        """Return the quote summary Yahoo answers with for a symbol."""
        url = _SUMMARY_URL.format(
            symbol=quote(symbol, safe=""),
            token=quote(self._access_token(), safe=""),
        )
        payload = json.loads(self._transport.get(url))
        if not isinstance(payload, Mapping):
            raise DataError(f"{SOURCE_NAME} answered with an unexpected payload")
        section = payload.get("quoteSummary")
        result = section.get("result") if isinstance(section, Mapping) else None
        if not isinstance(result, list) or not result:
            raise DataError(f"{SOURCE_NAME} returned no summary for {symbol}")
        summary = result[0]
        if not isinstance(summary, Mapping):
            raise DataError(f"{SOURCE_NAME} returned an unreadable summary")
        return summary

    def _access_token(self) -> str:
        """Return the token Yahoo requires, requesting it once."""
        if self._token is None:
            self._prime_session()
            token = self._transport.get(_TOKEN_URL).strip()
            if not token:
                raise DataError(f"{SOURCE_NAME} did not hand out an access token")
            self._token = token
        return self._token

    def _prime_session(self) -> None:
        """Ask Yahoo for the session cookie the access token belongs to.

        Yahoo answers this endpoint with an error status on purpose. The cookie
        set along the way is what the token request needs, so the status is
        recorded and ignored.
        """
        try:
            self._transport.get(_COOKIE_URL)
        except DataError as error:
            self._logger.debug("%s session priming answered %s", SOURCE_NAME, error)


def _points(summary: Mapping[str, Any]) -> tuple[MarketDataPoint, ...]:
    """Build one point per metric from a quote summary."""
    market_cap = _raw(summary, "summaryDetail", "marketCap")
    free_cash_flow = _raw(summary, "financialData", "freeCashflow")
    return (
        _point(MarketMetric.PE, _raw(summary, "summaryDetail", "trailingPE")),
        _point(MarketMetric.PEG, _raw(summary, "defaultKeyStatistics", "pegRatio")),
        _point(
            MarketMetric.EV_EBITDA,
            _raw(summary, "defaultKeyStatistics", "enterpriseToEbitda"),
        ),
        _fcf_yield_point(free_cash_flow, market_cap),
        _point(MarketMetric.DCF, None),
        _point(MarketMetric.BETA, _raw(summary, "summaryDetail", "beta")),
        _point(
            MarketMetric.DEBT_TO_EQUITY,
            _raw(summary, "financialData", "debtToEquity"),
        ),
        _point(
            MarketMetric.CURRENT_RATIO,
            _raw(summary, "financialData", "currentRatio"),
        ),
        _point(
            MarketMetric.AVERAGE_VOLUME,
            _raw(summary, "summaryDetail", "averageVolume"),
        ),
        _point(
            MarketMetric.FLOAT_SHARES,
            _raw(summary, "defaultKeyStatistics", "floatShares"),
        ),
        _point(
            MarketMetric.PROFIT_MARGIN,
            _raw(summary, "financialData", "profitMargins"),
        ),
        _point(
            MarketMetric.RETURN_ON_EQUITY,
            _raw(summary, "financialData", "returnOnEquity"),
        ),
        _free_cash_flow_margin_point(
            free_cash_flow, _raw(summary, "financialData", "totalRevenue")
        ),
    )


def _unavailable_points(reason: str) -> tuple[MarketDataPoint, ...]:
    """Build one point per metric, all stating the same reason.

    The DCF point keeps its own reason: it is unavailable whatever the state of
    the source is, so reporting a connection failure for it would be wrong.
    """
    return tuple(
        MarketDataPoint(
            metric=metric,
            value=None,
            reason=_DCF_REASON if metric is MarketMetric.DCF else reason,
        )
        for metric in MarketMetric
    )


def _point(metric: MarketMetric, value: float | None) -> MarketDataPoint:
    """Build one point from a retrieved value, or record that it is missing."""
    if metric is MarketMetric.DCF:
        return MarketDataPoint(metric=metric, value=None, reason=_DCF_REASON)
    if value is None:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{SOURCE_NAME} did not report {metric.label} for this symbol, so "
                f"it was not retrieved."
            ),
        )
    return MarketDataPoint(
        metric=metric,
        value=value,
        reason=f"{metric.label} {value} retrieved from {SOURCE_NAME}.",
    )


def _free_cash_flow_margin_point(
    free_cash_flow: float | None, revenue: float | None
) -> MarketDataPoint:
    """Build the free cash flow margin point from the two inputs it needs.

    Free cash flow margin is a ratio rather than a field the source publishes,
    so the reason spells out the division it comes from and keeps it traceable.
    """
    metric = MarketMetric.FREE_CASH_FLOW_MARGIN
    if free_cash_flow is None or not revenue:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{metric.label} could not be computed: {SOURCE_NAME} did not "
                f"report both free cash flow and revenue for this symbol."
            ),
        )
    value = free_cash_flow / revenue
    return MarketDataPoint(
        metric=metric,
        value=value,
        reason=(
            f"{metric.label} {value} computed as free cash flow {free_cash_flow} "
            f"divided by revenue {revenue}, both reported by {SOURCE_NAME}."
        ),
    )


def _fcf_yield_point(
    free_cash_flow: float | None, market_cap: float | None
) -> MarketDataPoint:
    """Build the free cash flow yield point from the two inputs it needs.

    Free cash flow yield is a ratio rather than a field the source publishes, so
    the reason spells out the division it comes from and keeps it traceable.
    """
    metric = MarketMetric.FCF_YIELD
    if free_cash_flow is None or not market_cap:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{metric.label} could not be computed: {SOURCE_NAME} did not "
                f"report both free cash flow and market capitalisation for this "
                f"symbol."
            ),
        )
    value = free_cash_flow / market_cap
    return MarketDataPoint(
        metric=metric,
        value=value,
        reason=(
            f"{metric.label} {value} computed as free cash flow {free_cash_flow} "
            f"divided by market capitalisation {market_cap}, both reported by "
            f"{SOURCE_NAME}."
        ),
    )


def _raw(summary: Mapping[str, Any], module: str, key: str) -> float | None:
    """Return one numeric field of a quote summary module.

    Yahoo wraps most numbers in a ``{"raw": ..., "fmt": ...}`` object but
    sometimes returns a bare number, and it reports anything it does not know as
    a null or a non numeric value. Every case other than a usable finite number
    is reported as missing.
    """
    section = summary.get(module)
    if not isinstance(section, Mapping):
        return None
    entry = section.get(key)
    if isinstance(entry, Mapping):
        entry = entry.get("raw")
    if isinstance(entry, bool) or not isinstance(entry, (int, float)):
        return None
    value = float(entry)
    return value if math.isfinite(value) else None
