"""The aspects of the environment a Market judgement is about.

The Constitution asks one question of this category — what is the environment
in which this asset is being judged — and names no aspects of it. Unlike the risk
dimensions, this set is therefore not fixed by the Constitution.

It is recorded here because coverage has to be measured against something. A
category with one measurement and one aspect would report complete coverage
while having examined almost nothing, and that is the failure mode this set
exists to prevent. The aspects are this implementation's reading of the
Constitution's question, and they are open to ratification.

Reading the question as three aspects:

* **Direction** — where the market the asset trades in has been going.
* **Volatility** — how turbulent that market has been.
* **Rates** — the cost of money the environment sets, which prices every asset
  in it.

Only direction is measured today. The other two are listed so that the gap is
visible in the report rather than hidden by a fraction that reads as complete.
"""

from __future__ import annotations

from enum import StrEnum


class MarketAspect(StrEnum):
    """An aspect of the environment an asset is judged in."""

    DIRECTION = "direction"
    VOLATILITY = "volatility"
    RATES = "rates"
