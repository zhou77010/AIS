"""AIS asset domain model.

An asset is the identity of something AIS can reason about. Identity only:
market data, scores, and valuation are not part of it.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.asset_profile import AssetProfile


@dataclass(frozen=True)
class Asset:
    """Fundamental identity of a tradable instrument.

    Attributes:
        ticker: Trading symbol that identifies the instrument.
        name: Human readable name of the instrument or issuer.
        exchange: Exchange the instrument is listed on.
        currency: Currency the instrument is quoted and traded in.
        profile: Kind of instrument the asset is.
    """

    ticker: str
    name: str
    exchange: str
    currency: str
    profile: AssetProfile
