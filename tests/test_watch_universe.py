"""Tests for the watch universe and the watchlist it is read from.

The universe is a set of membership sets. An asset belongs to as many as apply, a
theme watchlist is derived from the theme mapping rather than listed beside it, and
only three of the five sets may be declared at all: what AIS holds is the broker's
business and what the calendar has brought into view is the runtime's.

These tests describe those boundaries, and describe what happens when the file
cannot be trusted: the configured tickers are used instead, and no asset goes
missing quietly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from config.watchlist import load_watch_universe, universe_from_tickers
from models.asset_profile import AssetProfile
from models.sector import Sector
from models.watch_universe import (
    DECLARABLE_SETS,
    DERIVED_SETS,
    WatchSet,
    WatchUniverse,
)


def _write(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "watchlist.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _member(symbol: str, **overrides: object) -> dict[str, object]:
    return {"symbol": symbol, **overrides}


# --------------------------------------------------------------------------
# The model
# --------------------------------------------------------------------------


def test_the_five_sets_are_split_into_what_may_be_declared_and_what_may_not() -> None:
    # A file may state what a person chose to watch. It may not state what is held
    # or what the calendar brought into view.
    assert set(WatchSet) == DECLARABLE_SETS | DERIVED_SETS
    assert set() == DECLARABLE_SETS & DERIVED_SETS
    assert WatchSet.PORTFOLIO in DERIVED_SETS
    assert WatchSet.TEMPORARY in DERIVED_SETS
    assert WatchSet.THEME in DERIVED_SETS


def test_a_universe_built_from_tickers_watches_the_core_list() -> None:
    universe = universe_from_tickers(("AAPL", "RKLB"))

    assert universe.tickers == ("AAPL", "RKLB")
    assert universe.sets_of("AAPL") == frozenset({WatchSet.CORE})


# --------------------------------------------------------------------------
# The part of the market an asset is in
# --------------------------------------------------------------------------


def test_a_member_states_the_part_of_the_market_it_is_in(tmp_path: Path) -> None:
    # It is stated, not inferred: which sector an asset is in decides what it is
    # compared against, and therefore which sentence the report can write about it.
    path = _write(
        tmp_path,
        {"members": [_member("AAPL", sector="technology")]},
    )

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.assets[0].sector is Sector.TECHNOLOGY
    assert universe.sectors == (Sector.TECHNOLOGY,)


def test_a_sector_nobody_stated_is_left_absent(tmp_path: Path) -> None:
    path = _write(tmp_path, {"members": [_member("CGDV")]})

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.assets[0].sector is None
    assert universe.sectors == ()


def test_a_sector_that_cannot_be_recognised_is_not_guessed_at(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path, {"members": [_member("AAPL", sector="semiconductors")]})

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.assets[0].sector is None


def test_the_universe_reports_each_sector_it_holds_once(tmp_path: Path) -> None:
    # What the environment is asked to measure: a pass should cost what the universe
    # costs, and a sector nobody holds is not worth a request.
    path = _write(
        tmp_path,
        {
            "members": [
                _member("AAPL", sector="technology"),
                _member("MSFT", sector="technology"),
                _member("HSBC", sector="financial"),
            ]
        },
    )

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.sectors == (Sector.TECHNOLOGY, Sector.FINANCIAL)


def test_a_ticker_with_no_watchlist_knows_nothing_about_itself() -> None:
    # Filling these in would mean guessing what kind of asset each one is, and a
    # guess about that changes what the report is able to say.
    asset = universe_from_tickers(("AAPL",)).assets[0]

    assert asset.name == "AAPL"
    assert asset.exchange == "UNKNOWN"
    assert asset.currency == "USD"
    assert asset.profile is AssetProfile.UNKNOWN


def test_a_universe_with_nothing_in_it_says_so() -> None:
    assert WatchUniverse().is_empty is True
    assert universe_from_tickers(()).is_empty is True


def test_an_asset_may_belong_to_several_sets(tmp_path: Path) -> None:
    # The reason sets replaced tiers: being in the core watchlist and being a growth
    # name are two facts about one asset, and both are true at once.
    path = _write(tmp_path, {"members": [_member("NVDA", sets=["core", "growth"])]})

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.sets_of("NVDA") == frozenset({WatchSet.CORE, WatchSet.GROWTH})
    assert universe.by_set(WatchSet.CORE) == universe.by_set(WatchSet.GROWTH)


# --------------------------------------------------------------------------
# The theme set is derived
# --------------------------------------------------------------------------


def test_the_theme_watchlist_is_derived_from_the_mapping(tmp_path: Path) -> None:
    # Listing the members a second time is how the mapping and the watchlist drift
    # apart, so the set is computed from the mapping and nothing else.
    path = _write(
        tmp_path,
        {
            "members": [_member("NVDA"), _member("AAPL")],
            "themes": {"ai": ["NVDA", "AMD"], "space": ["RKLB"]},
        },
    )

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.themes_for("NVDA") == ("ai",)
    assert WatchSet.THEME in universe.sets_of("NVDA")
    assert WatchSet.THEME not in universe.sets_of("AAPL")
    assert [asset.ticker for asset in universe.by_set(WatchSet.THEME)] == ["NVDA"]


def test_a_theme_may_name_an_asset_that_is_not_a_member(tmp_path: Path) -> None:
    # A theme is a reason to look at something, and looking is what the universe
    # decides. A representative that is not watched represents the theme and is not
    # thereby watched.
    path = _write(
        tmp_path,
        {"members": [_member("AAPL")], "themes": {"ai": ["NVDA"]}},
    )

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.tickers == ("AAPL",)
    assert universe.themes_for("NVDA") == ("ai",)
    assert universe.sets_of("NVDA") == frozenset()


# --------------------------------------------------------------------------
# What the file may and may not say
# --------------------------------------------------------------------------


def test_a_watchlist_is_read(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        {
            "members": [
                _member(
                    "AAPL",
                    name="Apple Inc.",
                    exchange="NASDAQ",
                    currency="USD",
                    profile="mature_tech",
                    sets=["core"],
                ),
                _member("RKLB", profile="high_growth", sets=["growth"]),
            ]
        },
    )

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.tickers == ("AAPL", "RKLB")
    apple = universe.entry("AAPL")
    assert apple is not None
    assert apple.asset.name == "Apple Inc."
    assert apple.asset.exchange == "NASDAQ"
    assert apple.asset.profile is AssetProfile.MATURE_TECH
    assert universe.sets_of("RKLB") == frozenset({WatchSet.GROWTH})


def test_an_entry_that_states_no_set_belongs_to_the_core_list(tmp_path: Path) -> None:
    universe = load_watch_universe(_write(tmp_path, {"members": [_member("AAPL")]}))

    assert universe is not None
    assert universe.sets_of("AAPL") == frozenset({WatchSet.CORE})


def test_a_file_may_not_state_what_is_held(tmp_path: Path) -> None:
    # Whether a position is held is decided by a broker. A file that could state it
    # would be a second copy of a fact, and nothing would correct it.
    path = _write(tmp_path, {"members": [_member("AAPL", sets=["portfolio"])]})

    assert load_watch_universe(path) is None


def test_a_file_may_not_state_what_the_calendar_brought_into_view(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path, {"members": [_member("AAPL", sets=["temporary"])]})

    assert load_watch_universe(path) is None


def test_a_file_may_not_state_the_theme_set_either(tmp_path: Path) -> None:
    path = _write(tmp_path, {"members": [_member("AAPL", sets=["theme"])]})

    assert load_watch_universe(path) is None


def test_an_unknown_set_name_is_refused(tmp_path: Path) -> None:
    path = _write(tmp_path, {"members": [_member("AAPL", sets=["favourite"])]})

    assert load_watch_universe(path) is None


def test_one_symbol_appears_once(tmp_path: Path) -> None:
    # Two entries for one symbol would be two copies of its name, exchange,
    # currency and profile, and the two could disagree.
    path = _write(
        tmp_path, {"members": [_member("AAPL", name="Apple"), _member("aapl")]}
    )

    assert load_watch_universe(path) is None


def test_an_unknown_profile_is_left_unknown_rather_than_guessed(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path, {"members": [_member("AAPL", profile="consumer_staples")]})

    universe = load_watch_universe(path)

    assert universe is not None
    entry = universe.entry("AAPL")
    assert entry is not None
    assert entry.asset.profile is AssetProfile.UNKNOWN


def test_an_entry_without_a_name_or_an_exchange_still_loads(tmp_path: Path) -> None:
    universe = load_watch_universe(_write(tmp_path, {"members": [_member("AAPL")]}))

    assert universe is not None
    entry = universe.entry("AAPL")
    assert entry is not None
    assert entry.asset.name == "AAPL"
    assert entry.asset.exchange == "UNKNOWN"
    assert entry.asset.currency == "USD"


# --------------------------------------------------------------------------
# A file that cannot be trusted is not used
# --------------------------------------------------------------------------


def test_an_absent_watchlist_is_not_an_error(tmp_path: Path) -> None:
    assert load_watch_universe(tmp_path / "missing.json") is None


def test_an_empty_watchlist_is_not_used(tmp_path: Path) -> None:
    # An empty file would silently mean "watch nothing", which is not something a
    # missing edit should be able to say.
    assert load_watch_universe(_write(tmp_path, {"members": []})) is None


def test_a_watchlist_that_cannot_be_parsed_is_not_used(tmp_path: Path) -> None:
    path = tmp_path / "watchlist.json"
    path.write_text("{not json", encoding="utf-8")

    assert load_watch_universe(path) is None


def test_a_watchlist_that_is_not_an_object_is_not_used(tmp_path: Path) -> None:
    assert load_watch_universe(_write(tmp_path, ["AAPL"])) is None


def test_a_member_with_no_symbol_is_skipped(tmp_path: Path) -> None:
    path = _write(tmp_path, {"members": [{"name": "Apple"}, _member("RKLB")]})

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.tickers == ("RKLB",)


def test_symbols_are_upper_cased(tmp_path: Path) -> None:
    universe = load_watch_universe(_write(tmp_path, {"members": [_member("aapl")]}))

    assert universe is not None
    assert universe.tickers == ("AAPL",)


def test_the_universe_is_deterministic(tmp_path: Path) -> None:
    path = _write(tmp_path, {"members": [_member("AAPL"), _member("RKLB")]})

    assert load_watch_universe(path) == load_watch_universe(path)


@pytest.mark.parametrize("sets", [["core"], ["growth"], ["core", "growth"]])
def test_every_declarable_set_can_be_declared(tmp_path: Path, sets: list[str]) -> None:
    path = _write(tmp_path, {"members": [_member("AAPL", sets=sets)]})

    universe = load_watch_universe(path)

    assert universe is not None
    assert universe.sets_of("AAPL") == frozenset(WatchSet(name) for name in sets)
