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

**Sectors are measured against the market, not on their own.** The provider is told
which sectors the watch universe is in, reads only those, and reports each one as its
own move less the broad market's over the same session. Reading all eleven sectors
would be requests for sectors nobody holds; reading one sector's own move would say
nothing, because the market moved too.

Nothing here is a judgement. The provider states what the market did and how it
derived it, and never whether that is good or bad for anything.

The provider never raises and never invents a value: a measurement that cannot be
retrieved is returned as a point without a value that states why.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from urllib.parse import quote

from config.logging_config import get_logger
from contracts.market_environment import (
    EnvironmentMetric,
    EnvironmentPoint,
    EnvironmentProvider,
    EnvironmentSnapshot,
    SectorMove,
)
from data.http import HttpTransport, UrllibTransport
from models.sector import Sector

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

# What measures each sector. A sector is stated by a person and measured by an
# instrument, and the instrument is a vendor's symbol, which is why the mapping lives
# in the Data layer beside the other symbols rather than in the model.
_SYMBOL_BY_SECTOR: dict[Sector, str] = {
    Sector.TECHNOLOGY: "XLK",
    Sector.COMMUNICATION: "XLC",
    Sector.CONSUMER_CYCLICAL: "XLY",
    Sector.CONSUMER_DEFENSIVE: "XLP",
    Sector.ENERGY: "XLE",
    Sector.FINANCIAL: "XLF",
    Sector.HEALTHCARE: "XLV",
    Sector.INDUSTRIALS: "XLI",
    Sector.MATERIALS: "XLB",
    Sector.REAL_ESTATE: "XLRE",
    Sector.UTILITIES: "XLU",
}

# What a sector is measured against. The comparison is with the broad market over the
# same session, which is the only way "this sector moved" says anything: everything
# moved.
_MARKET_SYMBOL = "SPY"

# The ten year yield is quoted in percent; a basis point is a hundredth of one.
_BASIS_POINTS = 100.0


class YahooEnvironmentProvider:
    """Retrieves the environment the market is in, from Yahoo Finance."""

    def __init__(
        self,
        sectors: Sequence[Sector] = (),
        transport: HttpTransport | None = None,
    ) -> None:
        """Create the provider.

        Args:
            sectors: The sectors the watch universe is in, in a stable order. Only
                these are measured, and each is measured against the market.
            transport: Transport to talk through. Defaults to the standard library
                transport; tests supply a stand-in.
        """
        self._sectors = tuple(dict.fromkeys(sectors))
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
            Snapshot holding one point per measurement, and one reading per sector.
        """
        retrieved_at = datetime.now()
        series: dict[str, tuple[float, ...] | None] = {}
        for symbol in self._symbols():
            series[symbol] = self._closes(symbol)

        points = tuple(
            _point(metric, series.get(symbol))
            for metric, symbol in _SYMBOL_BY_METRIC.items()
        )
        snapshot = EnvironmentSnapshot(
            source=SOURCE_NAME,
            retrieved_at=retrieved_at,
            points=points,
            sectors=self._sector_moves(series),
        )
        self._logger.info(
            "environment: %d of %d measurements and %d sector(s) retrieved from %s",
            len(snapshot.available_points),
            len(snapshot.points),
            len(snapshot.sectors),
            SOURCE_NAME,
        )
        return snapshot

    def _symbols(self) -> tuple[str, ...]:
        """Return every symbol this pass reads, each of them once."""
        symbols = list(_SYMBOL_BY_METRIC.values())
        if self._sectors:
            symbols.append(_MARKET_SYMBOL)
            symbols.extend(
                _SYMBOL_BY_SECTOR[sector]
                for sector in self._sectors
                if sector in _SYMBOL_BY_SECTOR
            )
        return tuple(dict.fromkeys(symbols))

    def _sector_moves(
        self, series: Mapping[str, tuple[float, ...] | None]
    ) -> tuple[SectorMove, ...]:
        """Return each sector's move against the market, in the order asked for."""
        if not self._sectors:
            return ()
        market = _session_move(series.get(_MARKET_SYMBOL))
        return tuple(
            _sector_move(sector, series.get(_SYMBOL_BY_SECTOR[sector]), market)
            for sector in self._sectors
            if sector in _SYMBOL_BY_SECTOR
        )

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


def _session_move(closes: tuple[float, ...] | None) -> float | None:
    """Return how far a series moved on its most recent session, or None.

    The move is the last close against the one before it, which is the session that
    has just happened: for the futures that is the session open right now, and for
    everything else it is the one that last closed.
    """
    if closes is None or len(closes) < 2:
        return None
    previous, latest = closes[-2], closes[-1]
    if not previous:
        return None
    return latest / previous - 1.0


def _sector_move(
    sector: Sector, closes: tuple[float, ...] | None, market: float | None
) -> SectorMove:
    """Return one sector's move against the market, and how it was derived."""
    symbol = _SYMBOL_BY_SECTOR[sector]
    move = _session_move(closes)
    if move is None or market is None:
        missing = (
            f"the {sector.value} sector series" if closes is None else "the market"
        )
        return SectorMove(
            sector=sector,
            value=None,
            reason=(
                f"{SOURCE_NAME} could not provide {missing}, so the {sector.value} "
                f"sector was not compared with the market."
            ),
        )
    relative = move - market
    return SectorMove(
        sector=sector,
        value=relative,
        reason=(
            f"{sector.value.capitalize()} ({symbol}) {relative:+.2%} against the "
            f"broad market on the most recent session: {move:+.2%} for the sector "
            f"against {market:+.2%} for {_MARKET_SYMBOL}."
        ),
    )


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


def build_environment_provider(
    sectors: Sequence[Sector] = (),
) -> EnvironmentProvider:
    """Return the environment provider AIS uses.

    The return type is the contract rather than the vendor implementation, so that a
    caller cannot depend on anything vendor specific.

    Args:
        sectors: The sectors the watch universe is in. Only these are measured
            against the market, because a pass should cost what the universe costs
            rather than what the whole market costs.

    Returns:
        The environment provider AIS reads the market's own measurements from.
    """
    return YahooEnvironmentProvider(sectors=sectors)
