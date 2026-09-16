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
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from config.logging_config import get_logger
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
    PriceBar,
    PriceHistory,
)
from data import indicators
from data.http import HttpTransport, UrllibTransport
from utils.exceptions import DataError

SOURCE_NAME = "Yahoo Finance"

_LOGGER_NAME = "market_data"
_COOKIE_URL = "https://fc.yahoo.com"
_TOKEN_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
_SUMMARY_URL = (
    "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    "?modules=summaryDetail,defaultKeyStatistics,financialData,calendarEvents"
    "&crumb={token}"
)
_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range={range}&interval=1d"
)

# One year of daily bars is enough for a 120 day average with room to spare.
_HISTORY_RANGE = "1y"
_MA_WINDOWS = (20, 60, 120)
_VOLUME_RECENT_DAYS = 5
_VOLUME_BASELINE_DAYS = 60
_VOLATILITY_WINDOW = 20
_VOLUME_AVERAGE_WINDOW = 60
_SECONDS_PER_DAY = 86_400
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

        Price history is retrieved alongside the summary because the two answer
        different questions: the summary says what the figures are now, and the
        history says how the price got here. When only one of them answers, the
        measurements the other would have produced report themselves as
        unavailable rather than borrowing from it.

        Args:
            symbol: Trading symbol to retrieve data for.

        Returns:
            Snapshot holding one point per metric.
        """
        retrieved_at = datetime.now()
        indicators = _indicator_points(self.fetch_history(symbol))

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
            points = _merge(_unavailable_points(reason), indicators)
            return self._snapshot(symbol, retrieved_at, points)

        return self._snapshot(
            symbol, retrieved_at, _merge(_points(summary, retrieved_at), indicators)
        )

    def fetch_history(self, symbol: str) -> PriceHistory:
        """Return the daily price history Yahoo Finance holds for a symbol.

        The call never raises. A source that cannot be reached, or that answers
        with something unusable, returns an empty history, and everything
        computed from it reports itself as unavailable.

        Args:
            symbol: Trading symbol to retrieve history for.

        Returns:
            History holding the daily bars the source provided, possibly none.
        """
        retrieved_at = datetime.now()
        url = _CHART_URL.format(symbol=quote(symbol, safe=""), range=_HISTORY_RANGE)
        try:
            payload = json.loads(self._transport.get(url))
            bars = _bars_from(payload)
        except Exception as error:  # noqa: BLE001 - the contract is to never raise
            self._logger.warning(
                "price history for %s unavailable from %s: %s",
                symbol,
                SOURCE_NAME,
                f"{type(error).__name__}: {error}",
            )
            bars = ()
        self._logger.info(
            "price history for %s: %d daily bars from %s",
            symbol,
            len(bars),
            SOURCE_NAME,
        )
        return PriceHistory(
            symbol=symbol,
            source=SOURCE_NAME,
            retrieved_at=retrieved_at,
            bars=bars,
        )

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


def _bars_from(payload: object) -> tuple[PriceBar, ...]:
    """Return the daily bars out of a chart response.

    A period missing any of its prices is dropped rather than repaired: a bar
    with a closing price and no high is not a bar, and inventing one of the two
    would put a price in the record that nobody traded at.
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

    timestamps = entry.get("timestamp")
    blocks = entry.get("indicators")
    quotes = blocks.get("quote") if isinstance(blocks, Mapping) else None
    if not isinstance(timestamps, list) or not isinstance(quotes, list) or not quotes:
        return ()
    quote = quotes[0]
    if not isinstance(quote, Mapping):
        return ()

    bars: list[PriceBar] = []
    for index, stamp in enumerate(timestamps):
        values = [_series_value(quote, field, index) for field in _BAR_FIELDS]
        if any(value is None for value in values):
            continue
        open_, high, low, close, volume = values
        bars.append(
            PriceBar(
                timestamp=datetime.fromtimestamp(stamp, tz=UTC),
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )
    return tuple(bars)


_BAR_FIELDS = ("open", "high", "low", "close", "volume")


def _series_value(quote: Mapping[str, Any], field: str, index: int) -> float | None:
    """Return one value out of a chart series, or None when it is not usable."""
    series = quote.get(field)
    if not isinstance(series, list) or index >= len(series):
        return None
    value = series[index]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _indicator_points(history: PriceHistory) -> tuple[MarketDataPoint, ...]:
    """Return one point per indicator computed from the price history."""
    closes = history.closes
    volumes = history.volumes
    latest = closes[-1] if closes else None

    return (
        _indicator_point(
            MarketMetric.TREND_MA20_GAP,
            indicators.relative_change(
                latest, indicators.simple_moving_average(closes, _MA_WINDOWS[0])
            ),
            "as the latest close against its 20 day average",
        ),
        _indicator_point(
            MarketMetric.TREND_MA60_GAP,
            indicators.relative_change(
                latest, indicators.simple_moving_average(closes, _MA_WINDOWS[1])
            ),
            "as the latest close against its 60 day average",
        ),
        _indicator_point(
            MarketMetric.TREND_MA120_GAP,
            indicators.relative_change(
                latest, indicators.simple_moving_average(closes, _MA_WINDOWS[2])
            ),
            "as the latest close against its 120 day average",
        ),
        _indicator_point(
            MarketMetric.TREND_MACD,
            _macd_share(closes),
            "as the MACD line less its signal line, over the latest close",
        ),
        _indicator_point(
            MarketMetric.TREND_RSI,
            indicators.relative_strength_index(closes),
            "from the last 14 daily closes",
        ),
        _indicator_point(
            MarketMetric.TREND_VOLUME_RATIO,
            indicators.relative_change(
                indicators.simple_moving_average(volumes, _VOLUME_RECENT_DAYS),
                indicators.simple_moving_average(volumes, _VOLUME_BASELINE_DAYS),
            ),
            "as the last 5 days' volume against the last 60 days'",
        ),
        _indicator_point(
            MarketMetric.RISK_VOLATILITY,
            indicators.annualised_volatility(closes, _VOLATILITY_WINDOW),
            "from the last 20 daily returns, scaled to a year",
        ),
        _indicator_point(
            MarketMetric.RISK_DRAWDOWN,
            indicators.maximum_drawdown(closes),
            "over the daily closes retrieved",
        ),
    )


def _macd_share(closes: tuple[float, ...]) -> float | None:
    """Return the MACD gap as a share of price, so it can be compared across assets."""
    if not closes:
        return None
    result = indicators.macd(closes)
    if result is None:
        return None
    _, _, histogram = result
    return indicators.relative_change(closes[-1] + histogram, closes[-1])


def _indicator_point(
    metric: MarketMetric, value: float | None, detail: str
) -> MarketDataPoint:
    """Build one indicator point, or record that the history was too short."""
    if value is None:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{metric.label} could not be computed: {SOURCE_NAME} did not "
                f"provide enough daily price history for this symbol."
            ),
        )
    return MarketDataPoint(
        metric=metric,
        value=value,
        reason=(
            f"{metric.label} {value} computed {detail}, from daily prices "
            f"reported by {SOURCE_NAME}."
        ),
    )


def _merge(
    summary_points: Sequence[MarketDataPoint],
    indicator_points: Sequence[MarketDataPoint],
) -> tuple[MarketDataPoint, ...]:
    """Combine the two sources of measurements, in one stable order.

    The indicator points win where both describe the same metric, because the
    history says more about how the price has behaved than the summary does.
    """
    by_metric = {point.metric: point for point in summary_points}
    by_metric.update({point.metric: point for point in indicator_points})
    return tuple(by_metric[metric] for metric in MarketMetric if metric in by_metric)


def _points(
    summary: Mapping[str, Any], retrieved_at: datetime
) -> tuple[MarketDataPoint, ...]:
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
        _point(
            MarketMetric.MARKET_DIRECTION,
            _raw(summary, "defaultKeyStatistics", "SandP52WeekChange"),
        ),
        _trend_range_position_point(
            _raw(summary, "financialData", "currentPrice"),
            _raw(summary, "summaryDetail", "fiftyTwoWeekLow"),
            _raw(summary, "summaryDetail", "fiftyTwoWeekHigh"),
        ),
        _point(
            MarketMetric.TREND_DIRECTION,
            _raw(summary, "defaultKeyStatistics", "52WeekChange"),
        ),
        _point(
            MarketMetric.EARNINGS_GROWTH,
            _raw(summary, "defaultKeyStatistics", "earningsQuarterlyGrowth"),
        ),
        _expected_earnings_change_point(
            _raw(summary, "defaultKeyStatistics", "forwardEps"),
            _raw(summary, "defaultKeyStatistics", "trailingEps"),
        ),
        _days_until_point(
            MarketMetric.NEXT_EARNINGS_DAYS,
            _epoch(summary, "calendarEvents", "earnings", "earningsDate"),
            retrieved_at,
            "the next quarterly earnings report",
        ),
        _days_until_point(
            MarketMetric.NEXT_EX_DIVIDEND_DAYS,
            _epoch(summary, "calendarEvents", "exDividendDate"),
            retrieved_at,
            "the next ex-dividend date",
        ),
        _point(
            MarketMetric.SHORT_PERCENT_OF_FLOAT,
            _raw(summary, "defaultKeyStatistics", "shortPercentOfFloat"),
        ),
        _point(
            MarketMetric.SHORT_RATIO,
            _raw(summary, "defaultKeyStatistics", "shortRatio"),
        ),
        _point(
            MarketMetric.INSTITUTIONAL_OWNERSHIP,
            _raw(summary, "defaultKeyStatistics", "heldPercentInstitutions"),
        ),
        _point(
            MarketMetric.INSIDER_OWNERSHIP,
            _raw(summary, "defaultKeyStatistics", "heldPercentInsiders"),
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


def _expected_earnings_change_point(
    forward_eps: float | None, trailing_eps: float | None
) -> MarketDataPoint:
    """Build the point describing what earnings are expected to do next.

    The expected change is the gap between what is expected next and what has
    been reported, as a share of what has been reported. It is a ratio rather
    than a field the source publishes, so the reason states the division.

    Reported earnings that are not positive carry no meaningful ratio: dividing
    by zero or by a loss produces a number that says nothing about the
    expectation. That case is reported as absent with the reason, never as a
    value.
    """
    metric = MarketMetric.EXPECTED_EARNINGS_CHANGE
    if forward_eps is None or trailing_eps is None or trailing_eps <= 0:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{metric.label} could not be computed: it needs both a forward "
                f"and a positive reported earnings per share from {SOURCE_NAME}, "
                f"and this symbol does not have them."
            ),
        )
    value = (forward_eps - trailing_eps) / trailing_eps
    return MarketDataPoint(
        metric=metric,
        value=value,
        reason=(
            f"{metric.label} {value} computed as the forward earnings per share "
            f"{forward_eps} less the reported {trailing_eps}, divided by the "
            f"reported figure, both from {SOURCE_NAME}."
        ),
    )


def _trend_range_position_point(
    price: float | None, low: float | None, high: float | None
) -> MarketDataPoint:
    """Build the point describing where the price sits in its 52 week range.

    The position is a ratio rather than a field the source publishes, so the
    reason spells out the division it comes from and keeps it traceable. A range
    that does not span anything carries no position, and is reported as absent
    rather than as the middle of an empty range.
    """
    metric = MarketMetric.TREND_RANGE_POSITION
    if price is None or low is None or high is None or high <= low:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{metric.label} could not be computed: {SOURCE_NAME} did not "
                f"report a price and a 52 week range that spans anything for "
                f"this symbol."
            ),
        )
    value = (price - low) / (high - low)
    return MarketDataPoint(
        metric=metric,
        value=value,
        reason=(
            f"{metric.label} {value} computed as the price {price} less the 52 "
            f"week low {low}, divided by the range from {low} to {high}, all "
            f"reported by {SOURCE_NAME}."
        ),
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


def _days_until_point(
    metric: MarketMetric,
    epoch: float | None,
    retrieved_at: datetime,
    detail: str,
) -> MarketDataPoint:
    """Build the point telling how far away a scheduled event is.

    The distance is what makes an event a catalyst, so it is the distance that
    is measured rather than the date: an event with no distance to it cannot be
    said to be coming. A date the source reports that has already passed is not
    a forthcoming event, and is reported as absent rather than as a negative
    distance that would read as an event behind us.
    """
    if epoch is None:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{metric.label} could not be determined: {SOURCE_NAME} did not "
                f"report {detail} for this symbol."
            ),
        )
    moment = datetime.fromtimestamp(epoch, tz=retrieved_at.tzinfo)
    days = round((moment - retrieved_at).total_seconds() / _SECONDS_PER_DAY)
    if days < 0:
        return MarketDataPoint(
            metric=metric,
            value=None,
            reason=(
                f"{metric.label} is not known: {detail} that {SOURCE_NAME} "
                f"reports, {moment:%Y-%m-%d}, has already passed."
            ),
        )
    return MarketDataPoint(
        metric=metric,
        value=float(days),
        reason=(
            f"{metric.label} {days} days, counted from {detail} on "
            f"{moment:%Y-%m-%d} reported by {SOURCE_NAME}."
        ),
    )


def _epoch(summary: Mapping[str, Any], module: str, *keys: str) -> float | None:
    """Return a timestamp field of a quote summary, as seconds since the epoch.

    Yahoo nests the earnings date one level deeper than the other calendar
    fields and returns it as a list, so the lookup walks the path it is given
    and treats a list as the first entry that is there.
    """
    entry: Any = summary.get(module)
    for key in keys:
        if isinstance(entry, list):
            entry = entry[0] if entry else None
        entry = entry.get(key) if isinstance(entry, Mapping) else None
    if isinstance(entry, list):
        entry = entry[0] if entry else None
    if isinstance(entry, Mapping):
        entry = entry.get("raw")
    return _finite(entry)


def _finite(value: object) -> float | None:
    """Return the value as a finite number, or None when it is not one."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


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
    return _finite(entry)
