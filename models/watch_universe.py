"""The set of things AIS watches.

AIS watches one universe, and the universe is made of **membership sets** rather
than tiers. A tier is an ordered, exclusive thing, and what AIS actually has is
membership: NVDA is in the core watchlist, in AI and in semiconductor at the same
time, and asking which tier it is in is a question with no good answer.

**A set is a relation, not an attribute.** An asset does not have a set; it belongs
to some. So there is one entry per asset carrying the sets it belongs to, and the
same symbol may not appear twice — two entries for one symbol would be two copies
of its name, exchange, currency and profile, and the two could disagree.

**Five sets, and only three of them can be declared.** Whether a position is held is
decided by a broker and whether an event is near is decided by a calendar. A file
that could state either would be a second copy of a fact, written by hand, drifting
away from the real one with nothing to correct it. So a universe holds:

* what a person chose to watch — the core and growth watchlists;
* what a theme implies — derived from the theme mapping, never listed beside it;
* and, when their owners exist, what AIS holds and what the calendar has brought
  into view. Until then those two are empty, and being empty is the truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from models.asset import Asset
from models.sector import Sector


class WatchSet(StrEnum):
    """A membership set of the watch universe.

    The sets are unordered and may overlap. A member of one is not a non-member of
    another, and nothing is more important than anything else by belonging to a
    different set: importance is a judgement about attention, and it is not made
    here.
    """

    PORTFOLIO = "portfolio"
    CORE = "core"
    GROWTH = "growth"
    THEME = "theme"
    TEMPORARY = "temporary"


# The sets a configuration file may declare. The other two have owners that are not
# a file: the portfolio layer says what is held, and the runtime says what the
# calendar has brought into view.
DECLARABLE_SETS: frozenset[WatchSet] = frozenset({WatchSet.CORE, WatchSet.GROWTH})

# Sets whose membership is a fact rather than a choice, and which a file may
# therefore never state.
DERIVED_SETS: frozenset[WatchSet] = frozenset(
    {WatchSet.PORTFOLIO, WatchSet.TEMPORARY, WatchSet.THEME}
)


@dataclass(frozen=True)
class Theme:
    """An investment logic, and the assets that represent it.

    A theme is not a list of stocks. It is a reason to look at some stocks — AI
    points at NVDA, AMD, AVGO and MSFT because they are ways to own the same idea.
    The theme watchlist is the union of these, derived rather than listed, because
    two lists of the same members do not stay equal.

    Attributes:
        name: What the theme is called.
        members: Symbols that represent it, in the order they were given.
    """

    name: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class WatchEntry:
    """One asset of the universe, and the sets it belongs to.

    Attributes:
        asset: The asset itself, carrying its own name, exchange, currency, profile
            and sector so that nothing downstream has to invent them.
        sets: Sets the asset was declared to belong to. The theme set is not here:
            it is derived from the theme mapping, so that adding a theme to an asset
            cannot leave the two out of step.
    """

    asset: Asset
    sets: frozenset[WatchSet] = field(default_factory=frozenset)


@dataclass(frozen=True)
class WatchUniverse:
    """Everything AIS watches, and which sets each thing belongs to.

    Attributes:
        entries: One entry per asset. No symbol appears twice.
        themes: The themes held, each with its representative assets.
    """

    entries: tuple[WatchEntry, ...] = ()
    themes: tuple[Theme, ...] = ()

    @property
    def is_empty(self) -> bool:
        """Return whether nothing is watched."""
        return not self.entries

    @property
    def assets(self) -> tuple[Asset, ...]:
        """Return every watched asset, in the order the universe holds them."""
        return tuple(entry.asset for entry in self.entries)

    @property
    def tickers(self) -> tuple[str, ...]:
        """Return every watched symbol, in order."""
        return tuple(entry.asset.ticker for entry in self.entries)

    def entry(self, ticker: str) -> WatchEntry | None:
        """Return the entry for a symbol, or None when it is not watched."""
        wanted = ticker.upper()
        for entry in self.entries:
            if entry.asset.ticker.upper() == wanted:
                return entry
        return None

    def themes_for(self, ticker: str) -> tuple[str, ...]:
        """Return the themes a symbol represents, in the order held."""
        wanted = ticker.upper()
        return tuple(
            theme.name
            for theme in self.themes
            if wanted in {member.upper() for member in theme.members}
        )

    def sets_of(self, ticker: str) -> frozenset[WatchSet]:
        """Return every set a symbol belongs to, including the derived ones."""
        entry = self.entry(ticker)
        if entry is None:
            return frozenset()
        derived = {WatchSet.THEME} if self.themes_for(ticker) else set()
        return entry.sets | derived

    @property
    def sectors(self) -> tuple[Sector, ...]:
        """Return every part of the market the universe is in, each once.

        It is what the environment is asked to measure: a pass should cost what the
        universe costs, and a sector nobody holds is not worth a request. The order
        is the order the universe holds them, so the same watchlist produces the same
        requests in the same order.
        """
        return tuple(
            dict.fromkeys(
                entry.asset.sector
                for entry in self.entries
                if entry.asset.sector is not None
            )
        )

    def by_set(self, watch_set: WatchSet) -> tuple[Asset, ...]:
        """Return every asset that belongs to one set, in universe order.

        A symbol in several sets appears in each of them. That is the whole point
        of sets over tiers: the questions "what do I watch closely" and "what
        represents AI" are different questions, and one asset may answer both.
        """
        return tuple(
            entry.asset
            for entry in self.entries
            if watch_set in self.sets_of(entry.asset.ticker)
        )
