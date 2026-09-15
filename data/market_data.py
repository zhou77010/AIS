"""AIS market data provider selection.

The single place in AIS that decides which market data vendor the system talks
to.

Nothing outside the Data layer names a vendor. Every other component depends on
the :class:`~contracts.market_data_provider.MarketDataProvider` contract alone,
so adding or replacing a provider is a change here and nowhere else.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketDataProvider
from data.yahoo_market_data_provider import YahooMarketDataProvider


def build_market_data_provider() -> MarketDataProvider:
    """Return the market data provider AIS uses.

    The return type is the contract rather than the vendor implementation, so
    that a caller cannot depend on anything vendor specific.

    Returns:
        The market data provider AIS retrieves data from.
    """
    return YahooMarketDataProvider()
