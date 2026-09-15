"""Contract for market data providers.

A market data provider is any source of raw market data. This module defines
the interface only and holds no implementation and no vendor specifics.
"""

from __future__ import annotations

from typing import Protocol


class MarketDataProvider(Protocol):
    """Contract for any market data source."""

    def fetch(self, symbol: str) -> str:
        """Return the raw market data payload for a symbol.

        Args:
            symbol: Trading symbol the data is requested for.

        Returns:
            Raw data payload in the provider's native format.
        """
