"""Reading the watchlist AIS is configured to follow.

The watchlist lives here rather than in the Data layer because it is AIS's own
statement about what to look at. It is configuration, not a fact about the world,
and the Data layer collects facts about the world.

**The file may not state a fact.** It declares the core and growth watchlists and
the mapping from a theme to its representative assets. It may not declare what AIS
holds or what the calendar has brought into view: those have owners, and a file that
could state them would become a second copy that nothing corrects.

**A file that cannot be trusted is not used.** A watchlist that cannot be parsed, is
empty, or declares a set a file may not declare is refused as a whole rather than
read in part, and the caller falls back to the configured tickers. A watchlist that
is silently halved is worse than one that is not used at all, because the assets
that went missing are missing quietly.

The shape::

    {
      "members": [
        {
          "symbol": "AAPL",
          "name": "Apple Inc.",
          "exchange": "NASDAQ",
          "currency": "USD",
          "profile": "mature_tech",
          "sets": ["core"]
        }
      ],
      "themes": {"ai": ["NVDA", "AMD", "AVGO", "MSFT"]}
    }

``symbol`` is the only required field. An entry that states no set belongs to the
core watchlist. A profile that cannot be recognised is left as unknown rather than
guessed at, because guessing a kind of asset would change what AIS is able to say
about it.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from logging import Logger
from pathlib import Path
from typing import Any

from config.logging_config import get_logger
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.watch_universe import (
    DECLARABLE_SETS,
    Theme,
    WatchEntry,
    WatchSet,
    WatchUniverse,
)

_LOGGER_NAME = "config"
_MEMBERS_KEY = "members"
_THEMES_KEY = "themes"

_DEFAULT_SETS = frozenset({WatchSet.CORE})
_DEFAULT_EXCHANGE = "UNKNOWN"
_DEFAULT_CURRENCY = "USD"


def load_watch_universe(path: Path) -> WatchUniverse | None:
    """Return the universe a watchlist file describes, or None when it cannot be used.

    Args:
        path: File to read. It may not exist.

    Returns:
        The universe, or None when the file is absent, empty, unreadable, or
        declares something a watchlist may not declare. None means the caller
        should fall back rather than continue with a partial universe.
    """
    logger = get_logger(_LOGGER_NAME)
    if not path.exists():
        logger.info("no watchlist at %s; falling back to the configured tickers", path)
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        logger.warning(
            "watchlist at %s could not be read: %s",
            path,
            f"{type(error).__name__}: {error}",
        )
        return None
    if not isinstance(payload, Mapping):
        logger.warning("watchlist at %s is not an object", path)
        return None

    members = payload.get(_MEMBERS_KEY)
    if not isinstance(members, list) or not members:
        logger.warning("watchlist at %s holds no members", path)
        return None

    entries = _entries(members, logger)
    if entries is None:
        return None
    themes = _themes(payload.get(_THEMES_KEY), logger)
    if themes is None:
        return None
    return WatchUniverse(entries=entries, themes=themes)


def universe_from_tickers(tickers: Sequence[str]) -> WatchUniverse:
    """Return a core-only universe built from a list of symbols.

    This is the fallback, and it is deliberately indistinguishable from a watchlist
    file that lists the same symbols under the core set: a run with no file and a
    run with a file that says the same thing produce the same universe.

    Nothing is known about these assets beyond their symbols, so their names,
    exchanges, currencies and profiles are left as the placeholders they were
    before a watchlist existed. Filling them in would mean guessing what kind of
    asset each one is, and a guess about that changes what the report is able to
    say.

    Args:
        tickers: Symbols to watch.

    Returns:
        A universe whose only set is the core watchlist.
    """
    return WatchUniverse(
        entries=tuple(
            WatchEntry(
                asset=Asset(
                    ticker=symbol,
                    name=symbol,
                    exchange=_DEFAULT_EXCHANGE,
                    currency=_DEFAULT_CURRENCY,
                    profile=AssetProfile.UNKNOWN,
                ),
                sets=_DEFAULT_SETS,
            )
            for symbol in tickers
        )
    )


def _entries(members: list[Any], logger: Logger) -> tuple[WatchEntry, ...] | None:
    """Return one entry per member, or None when the list cannot be trusted."""
    entries: list[WatchEntry] = []
    seen: set[str] = set()
    for member in members:
        if not isinstance(member, Mapping):
            logger.warning("ignoring unusable watchlist member: %r", member)
            continue
        symbol = member.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            logger.warning("ignoring watchlist member with no symbol: %r", member)
            continue
        ticker = symbol.strip().upper()
        if ticker in seen:
            # One symbol, one entry. Two entries would be two copies of its name,
            # exchange, currency and profile, and the two could disagree.
            logger.warning(
                "watchlist lists %s more than once; the file is not used", ticker
            )
            return None
        declared = _sets(member.get("sets"), ticker, logger)
        if declared is None:
            return None
        seen.add(ticker)
        entries.append(
            WatchEntry(
                asset=Asset(
                    ticker=ticker,
                    name=_text(member.get("name")) or ticker,
                    exchange=_text(member.get("exchange")) or _DEFAULT_EXCHANGE,
                    currency=_text(member.get("currency")) or _DEFAULT_CURRENCY,
                    profile=_profile(member.get("profile"), ticker, logger),
                ),
                sets=declared,
            )
        )
    return tuple(entries) if entries else None


def _sets(raw: Any, ticker: str, logger: Logger) -> frozenset[WatchSet] | None:
    """Return the sets one member declares, or None when it declares a forbidden one.

    An entry that states no set belongs to the core watchlist. An entry that states
    a set only the broker or the runtime may fill is a misunderstanding of the
    model, and the file is refused rather than halved: ignoring the set would leave
    the file looking as though it had worked.
    """
    if raw is None:
        return _DEFAULT_SETS
    if not isinstance(raw, list):
        logger.warning("watchlist member %s has an unreadable set list", ticker)
        return None
    declared: set[WatchSet] = set()
    for name in raw:
        try:
            watch_set = WatchSet(name)
        except (ValueError, TypeError):
            logger.warning("watchlist member %s names an unknown set %r", ticker, name)
            return None
        if watch_set not in DECLARABLE_SETS:
            logger.warning(
                "watchlist member %s declares %r, which a watchlist may not state: "
                "it is a fact its owner decides, not a choice",
                ticker,
                watch_set.value,
            )
            return None
        declared.add(watch_set)
    return frozenset(declared)


def _profile(raw: Any, ticker: str, logger: Logger) -> AssetProfile:
    """Return the kind of asset a member states, or unknown when it states none.

    A profile that cannot be recognised is left unknown. Guessing which kind of
    asset something is would decide what AIS is able to say about it, and being
    unable to say is the honest answer to not knowing.
    """
    if raw is None:
        return AssetProfile.UNKNOWN
    try:
        return AssetProfile(str(raw).lower())
    except ValueError:
        logger.warning("watchlist member %s names an unknown profile %r", ticker, raw)
        return AssetProfile.UNKNOWN


def _themes(raw: Any, logger: Logger) -> tuple[Theme, ...] | None:
    """Return the themes a watchlist holds, or None when they cannot be read."""
    if raw is None:
        return ()
    if not isinstance(raw, Mapping):
        logger.warning("watchlist themes are not an object; the file is not used")
        return None
    themes: list[Theme] = []
    for name, members in raw.items():
        if not isinstance(name, str) or not isinstance(members, list):
            logger.warning("ignoring unusable theme %r", name)
            continue
        themes.append(
            Theme(
                name=name,
                members=tuple(
                    member.strip().upper()
                    for member in members
                    if isinstance(member, str) and member.strip()
                ),
            )
        )
    return tuple(themes)


def _text(raw: Any) -> str | None:
    """Return a non-empty string, or None when the value is not one."""
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None
