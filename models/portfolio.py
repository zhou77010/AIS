"""AIS portfolio domain models.

These models describe portfolio state only. They hold no allocation,
position sizing, or any other behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.asset import Asset


@dataclass(frozen=True)
class Position:
    """A single holding inside a portfolio.

    Attributes:
        asset: Asset that is held.
        weight: Share of the portfolio held in the asset, from 0.0 to 1.0.
    """

    asset: Asset
    weight: float


@dataclass(frozen=True)
class Portfolio:
    """State of a portfolio: the positions it holds and how it is reported.

    Attributes:
        name: Name that identifies the portfolio.
        base_currency: Currency the portfolio is measured in.
        positions: Positions currently held by the portfolio.
    """

    name: str
    base_currency: str
    positions: tuple[Position, ...]
