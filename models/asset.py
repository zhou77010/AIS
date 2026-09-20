"""AIS asset domain model.

An asset is the identity of something AIS can reason about. Identity only:
market data, scores, and valuation are not part of it.

Two labels are part of that identity, and both are stated rather than inferred: what
kind of instrument it is, which decides which questions apply to it, and which part of
the market it is in, which decides what it is compared against. Both are left absent
when nobody has stated them, because a guessed label changes what AIS is able to say
and the change is invisible in the output.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.asset_profile import AssetProfile
from models.sector import Sector


@dataclass(frozen=True)
class Asset:
    """Fundamental identity of a tradable instrument.

    Attributes:
        ticker: Trading symbol that identifies the instrument.
        name: Human readable name of the instrument or issuer.
        exchange: Exchange the instrument is listed on.
        currency: Currency the instrument is quoted and traded in.
        profile: Kind of instrument the asset is.
        sector: Part of the market the asset competes in, or None when nobody has
            stated one. An exchange-traded fund holds a style rather than a sector,
            and a business nobody has classified is simply not classified: both are
            told nothing about their sector rather than something plausible.
    """

    ticker: str
    name: str
    exchange: str
    currency: str
    profile: AssetProfile
    sector: Sector | None = None
