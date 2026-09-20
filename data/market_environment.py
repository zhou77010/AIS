"""AIS Yahoo Finance environment provider.

Retrieves the measurements that belong to the market rather than to an asset, from
the same vendor the asset data comes from and through the same endpoint. They are
retrieved once per pass and shared by every asset in it.

**What is derived, and how.** Each measurement is read from a short daily bar series,
as the most recent close against the one before it. That is the most recent session's
move, and for the futures it is the session that is open right now — overnight and
pre-market, which is the move a reader of a morning report is asking about. The
vendor also publishes a `chartPreviousClose`, and it is deliberately not used: it is
the close before the requested range began rather than the previous session, so
reading it as "the previous close" would report a week's move as an overnight one.

Nothing here is a judgement. The provider states what the market did and how it
derived it, and never whether that is good or bad for anything.

The provider never raises and never invents a value: a measurement that cannot be
retrieved is returned as a point without a value that states why.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from urllib.parse import quote

from config.logging_config import get_logger
from contracts.market_environment import (
    EnvironmentMetric,
    EnvironmentPoint,
    EnvironmentProvider,
    EnvironmentSnapshot,
)
from data.http import HttpTransport, UrllibTransport

SOURCE_NAME = "Yahoo Finance"

_LOGGER_NAME = "market_data"
_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range={range}&interval=1d"
)

# Five daily bars: two are needed for a change, and the rest is room for a session
# the vendor has not stamped yet.
_SERIES_RANGE = "5d"

# Which symbol carries which measurement. Two measurements share a symbol, and the
# series is therefore retrieved once for both.
_SYMBOL_BY_METRIC: dict[EnvironmentMetric, str] = {
    EnvironmentMetric.OVERNIGHT_EQUITY: "ES=F",
    EnvironmentMetric.OVERNIGHT_GROWTH: "NQ=F",
    EnvironmentMetric.VOLATILITY: "^VIX",
    EnvironmentMetric.VOLATILITY_CHANGE: "^VIX",
    EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: "^TNX",
}

_SYMBOL_NAMES: dict[str, str] = {
    "ES=F": "S&P 500 futures",
    "NQ=F": "Nasdaq 100 futures",
    "^VIX": "Volatility index",
    "^TNX": "Ten year yield",
}

# The ten year yield is quoted in percent; a basis point is a hundredth of one.
_BASIS_POINTS = 100.0


class YahooEnvironmentProvider:
    """Retrieves the environment the market is in, from Yahoo Finance."""

    def __init__(self, transport: HttpTransport | None = None) -> None:
        """Create the provider.

        Args:
            transport: Transport to talk through. Defaults to the standard library
                transport; tests supply a stand-in.
        """
        self._transport: HttpTransport = (
            transport if transport is not None else UrllibTransport()
        )
        self._logger = get_logger(_LOGGER_NAME)

    def fetch(self) -> EnvironmentSnapshot:
        """Return the environment as Yahoo Finance reports it at this moment.

        The call never raises. Each symbol is read once, and a symbol that cannot be
        read produces a point without a value for every measurement it carries,
        stating why, so one unreachable symbol degrades one part of the environment
        instead of all of it.

        Returns:
            Snapshot holding one point per measurement.
        """
        retrieved_at = datetime.now()
        series: dict[str, tuple[float, ...] | None] = {}
        for symbol in dict.fromkeys(_SYMBOL_BY_METRIC.values()):
            series[symbol] = self._closes(symbol)

        points = tuple(
            _point(metric, series.get(symbol))
            for metric, symbol in _SYMBOL_BY_METRIC.items()
        )
        snapshot = EnvironmentSnapshot(
            source=SOURCE_NAME,
            retrieved_at=retrieved_at,
            points=points,
        )
        self._logger.info(
            "environment: %d of %d measurements retrieved from %s",
            len(snapshot.available_points),
            len(snapshot.points),
            SOURCE_NAME,
        )
        return snapshot

    def _closes(self, symbol: str) -> tuple[float, ...] | None:
        """Return the daily closes of one symbol, or None when it could not be read."""
        url = _CHART_URL.format(symbol=quote(symbol, safe=""), range=_SERIES_RANGE)
        try:
            payload = json.loads(self._transport.get(url))
            closes = _closes_from(payload)
        except Exception as error:  # noqa: BLE001 - the contract is to never raise
            self._logger.warning(
                "environment series for %s unavailable from %s: %s",
                symbol,
                SOURCE_NAME,
                f"{type(error).__name__}: {error}",
            )
            return None
        if not closes:
            self._logger.warning(
                "environment series for %s came back empty from %s", symbol, SOURCE_NAME
            )
            return None
        return closes


def _point(
    metric: EnvironmentMetric, closes: tuple[float, ...] | None
) -> EnvironmentPoint:
    """Return one measurement, read from the series that carries it."""
    symbol = _SYMBOL_BY_METRIC[metric]
    name = _SYMBOL_NAMES.get(symbol, symbol)
    if closes is None:
        return EnvironmentPoint(
            metric=metric,
            value=None,
            reason=(
                f"{SOURCE_NAME} could not provide this measurement, so it was not "
                f"retrieved ({name} {symbol} series unavailable)."
            ),
        )
    if len(closes) < 2:
        return EnvironmentPoint(
            metric=metric,
            value=None,
            reason=(
                f"{SOURCE_NAME} returned one session of {name} {symbol} and a "
                f"measurement of the change needs two, so it was not computed."
            ),
        )

    previous, latest = closes[-2], closes[-1]
    if metric is EnvironmentMetric.VOLATILITY:
        return EnvironmentPoint(
            metric=metric,
            value=latest,
            reason=f"{name} {symbol} at {latest:,.2f} on the most recent session.",
        )
    if metric is EnvironmentMetric.TEN_YEAR_YIELD_CHANGE:
        change = (latest - previous) * _BASIS_POINTS
        return EnvironmentPoint(
            metric=metric,
            value=change,
            reason=(
                f"{name} {symbol} {change:+.1f} basis points on the most recent "
                f"session, from {previous:.3f} to {latest:.3f} percent."
            ),
        )
    if metric is EnvironmentMetric.VOLATILITY_CHANGE:
        change = latest - previous
        return EnvironmentPoint(
            metric=metric,
            value=change,
            reason=(
                f"{name} {symbol} {change:+.2f} points on the most recent session, "
                f"from {previous:,.2f} to {latest:,.2f}."
            ),
        )

    move = (latest / previous - 1.0) if previous else None
    if move is None:
        return EnvironmentPoint(
            metric=metric,
            value=None,
            reason=(
                f"{name} {symbol} closed at zero on the previous session, so a "
                f"change against it was not computed."
            ),
        )
    return EnvironmentPoint(
        metric=metric,
        value=move,
        reason=(
            f"{name} {symbol} {move:+.2%} on the most recent session, from "
            f"{previous:,.2f} to {latest:,.2f}."
        ),
    )


def _closes_from(payload: object) -> tuple[float, ...]:
    """Return the daily closes out of a chart response, oldest first.

    A session with no close is dropped rather than repaired: a session nobody
    priced is not a close, and carrying the previous one forward would turn a gap
    into a flat move.
    """
    if not isinstance(payload, Mapping):
        return ()
    chart = payload.get("chart")
    if not isinstance(chart, Mapping):
        return ()
    results = chart.get("result")
    if not isinstance(results, list) or not results:
        return ()
    entry = results[0]
    if not isinstance(entry, Mapping):
        return ()
    blocks = entry.get("indicators")
    quotes = blocks.get("quote") if isinstance(blocks, Mapping) else None
    if not isinstance(quotes, list) or not quotes:
        return ()
    quote = quotes[0]
    if not isinstance(quote, Mapping):
        return ()
    closes = quote.get("close")
    if not isinstance(closes, list):
        return ()
    return tuple(
        float(close)
        for close in closes
        if isinstance(close, (int, float)) and not isinstance(close, bool)
    )


def build_environment_provider() -> EnvironmentProvider:
    """Return the environment provider AIS uses.

    The return type is the contract rather than the vendor implementation, so that a
    caller cannot depend on anything vendor specific.

    Returns:
        The environment provider AIS reads the market's own measurements from.
    """
    return YahooEnvironmentProvider()
