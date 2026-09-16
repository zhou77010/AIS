"""A dated event that could change the investment case for an asset.

A catalyst is not a measurement. It is something that has not happened yet, on a
date, that could change what the market expects. That makes it a different kind
of fact from a price or a ratio, and it is modelled separately for that reason:
an event has a kind, a date, a source and a confidence in the date, and none of
those fit a number.

**Classification is AIS's, not the source's.** A provider reports what it knows:
that a company reports results on a date, that a central bank meets on a date.
Which layer of the investment case that event belongs to is AIS's reading, and it
is made here, in one table, for every event from every source. A provider that
decided this would be making a judgement, and providers return facts.

**Adding a kind does not change the evaluator.** The evaluator reads events and
asks how near the nearest one is. It does not care which kind it is, so a new
kind is a new member of the enumeration and a row in the tables beside it, and
no evaluation logic changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class CatalystEventScope(StrEnum):
    """Which layer of the investment case an event bears on.

    The three layers are the three ways an event can change a view: it can change
    what is known about the company, about the industry the company competes in,
    or about the conditions everything is valued under.
    """

    COMPANY = "company"
    INDUSTRY = "industry"
    MACRO = "macro"


class CatalystEventKind(StrEnum):
    """What kind of event it is.

    The list is deliberately open: an event kind is a fact about the world and
    there are many of them. Nothing outside the tables in this module and in the
    report's labels needs to know the list.
    """

    EARNINGS = "earnings"
    EX_DIVIDEND = "ex_dividend"
    DIVIDEND = "dividend"
    SPLIT = "split"
    INVESTOR_DAY = "investor_day"
    PRODUCT_LAUNCH = "product_launch"
    LAUNCH_WINDOW = "launch_window"
    REGULATORY = "regulatory"
    SHAREHOLDER_MEETING = "shareholder_meeting"
    INDUSTRY_POLICY = "industry_policy"
    COMPETITION = "competition"
    INDUSTRY_NEWS = "industry_news"
    FOMC = "fomc"
    INFLATION = "inflation"
    EMPLOYMENT = "employment"
    GROWTH = "growth"
    RATES = "rates"
    FISCAL_POLICY = "fiscal_policy"
    TARIFF = "tariff"
    CURRENCY = "currency"


# Which layer each kind belongs to. This is AIS classifying, and it is the only
# place the mapping is made: a provider never states it, so a provider cannot
# change how AIS reads its own event set.
CATALYST_EVENT_SCOPE: dict[CatalystEventKind, CatalystEventScope] = {
    CatalystEventKind.EARNINGS: CatalystEventScope.COMPANY,
    CatalystEventKind.EX_DIVIDEND: CatalystEventScope.COMPANY,
    CatalystEventKind.DIVIDEND: CatalystEventScope.COMPANY,
    CatalystEventKind.SPLIT: CatalystEventScope.COMPANY,
    CatalystEventKind.INVESTOR_DAY: CatalystEventScope.COMPANY,
    CatalystEventKind.PRODUCT_LAUNCH: CatalystEventScope.COMPANY,
    CatalystEventKind.LAUNCH_WINDOW: CatalystEventScope.COMPANY,
    CatalystEventKind.REGULATORY: CatalystEventScope.COMPANY,
    CatalystEventKind.SHAREHOLDER_MEETING: CatalystEventScope.COMPANY,
    CatalystEventKind.INDUSTRY_POLICY: CatalystEventScope.INDUSTRY,
    CatalystEventKind.COMPETITION: CatalystEventScope.INDUSTRY,
    CatalystEventKind.INDUSTRY_NEWS: CatalystEventScope.INDUSTRY,
    CatalystEventKind.FOMC: CatalystEventScope.MACRO,
    CatalystEventKind.INFLATION: CatalystEventScope.MACRO,
    CatalystEventKind.EMPLOYMENT: CatalystEventScope.MACRO,
    CatalystEventKind.GROWTH: CatalystEventScope.MACRO,
    CatalystEventKind.RATES: CatalystEventScope.MACRO,
    CatalystEventKind.FISCAL_POLICY: CatalystEventScope.MACRO,
    CatalystEventKind.TARIFF: CatalystEventScope.MACRO,
    CatalystEventKind.CURRENCY: CatalystEventScope.MACRO,
}


# Events that change the price rather than what the market expects. Going
# ex-dividend moves the price by the dividend by construction, and paying one
# settles a decision already taken; both are worth reporting and neither is a
# reason to change a view. They are excluded from the catalyst reading, and they
# are still shown, so the reader sees them and sees that they were not counted.
#
# A kind that is not listed here counts. A new kind is therefore a change to this
# table when it is mechanical and no change at all when it is not, which is why
# the evaluator never names a kind.
CATALYST_MECHANICAL_KINDS: frozenset[CatalystEventKind] = frozenset(
    {CatalystEventKind.EX_DIVIDEND, CatalystEventKind.DIVIDEND}
)


@dataclass(frozen=True)
class CatalystEvent:
    """One dated event that could change the investment case.

    Attributes:
        kind: What kind of event it is. The layer it belongs to is read from it.
        occurs_on: Date the event falls on.
        source: Who states that this event is happening, named for the reader.
        confirmed: Whether the source presents the date as settled. An estimated
            date is still a catalyst, and a reader is owed the difference between
            a scheduled meeting and a rumoured product launch.
        description: What the event is, stated by the source and not rewritten.
        symbol: Asset the event belongs to, or None for an event that bears on
            every asset measured under the same conditions.
    """

    kind: CatalystEventKind
    occurs_on: date
    source: str
    confirmed: bool
    description: str
    symbol: str | None = None

    @property
    def scope(self) -> CatalystEventScope:
        """Return which layer of the investment case this event bears on."""
        return CATALYST_EVENT_SCOPE[self.kind]

    @property
    def is_mechanical(self) -> bool:
        """Return whether the event moves the price without moving a view."""
        return self.kind in CATALYST_MECHANICAL_KINDS

    def days_from(self, moment: datetime) -> int:
        """Return how many days away the event is from a moment.

        Args:
            moment: Moment to measure from.

        Returns:
            Whole days until the event; negative once the date has passed.
        """
        return (self.occurs_on - moment.date()).days

    def is_upcoming(self, moment: datetime) -> bool:
        """Return whether the event is still ahead of the moment."""
        return self.days_from(moment) >= 0
