"""The aspects of the environment a Market judgement is about.

The Constitution asks one question of this category — what is the environment
in which this asset is being judged — and names no aspects of it. Unlike the risk
dimensions, this set is therefore not fixed by the Constitution.

It is recorded here because coverage has to be measured against something. A
category with one measurement and one aspect would report complete coverage
while having examined almost nothing, and that is the failure mode this set
exists to prevent. The aspects are this implementation's reading of the
Constitution's question, and they are open to ratification.

Reading the question as four aspects:

* **Direction** — where the market the asset trades in has been going.
* **Risk appetite** — what the market is doing about risk right now: whether the
  tape is being bought or sold overnight, and whether the price of protection is
  rising.
* **Volatility** — how turbulent that market is.
* **Rates** — the cost of money the environment sets, which prices every asset
  in it.

All four are measured now. Volatility and rates used to be listed here while being
unmeasured, which is why they appeared in the report as gaps; the aspects did not
change when the evidence arrived, and neither did the question.
"""

from __future__ import annotations

from enum import StrEnum


class MarketAspect(StrEnum):
    """An aspect of the environment an asset is judged in."""

    DIRECTION = "direction"
    RISK_APPETITE = "risk_appetite"
    VOLATILITY = "volatility"
    RATES = "rates"
