"""Contract for the portfolio engine.

The portfolio engine sizes positions and transforms portfolios. Position
sizing belongs here. This module defines the interface only and holds no logic.
"""

from __future__ import annotations

from typing import Protocol

from models.portfolio import Portfolio
from models.recommendation import Recommendation


class PortfolioEngine(Protocol):
    """Contract for the component that sizes positions and transforms portfolios."""

    def allocate(
        self, portfolio: Portfolio, recommendation: Recommendation
    ) -> Portfolio:
        """Transform the portfolio by sizing the position for a recommendation.

        Args:
            portfolio: Portfolio to transform.
            recommendation: Recommendation for the asset.

        Returns:
            Portfolio with the sized position applied.
        """
