"""Tests for the evidence pipeline (Sprint 5)."""

from __future__ import annotations

from datetime import datetime

from evidence.evidence_collection import EvidenceCollection
from evidence.evidence_item import EvidenceItem
from evidence.evidence_source import EvidenceSource
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from pipeline.evidence_builder import EvidenceBuilder
from pipeline.evidence_factory import EvidenceFactory
from pipeline.evidence_registry import EvidenceRegistry


def make_asset() -> Asset:
    """Return a fixed asset used across the tests."""
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def test_builder_build_returns_collection_for_the_asset() -> None:
    collection = EvidenceBuilder().build(make_asset())

    assert isinstance(collection, EvidenceCollection)
    assert collection.asset == make_asset()
    assert len(collection.items) == len(Category)


def test_builder_covers_every_category_exactly_once() -> None:
    collection = EvidenceBuilder().build(make_asset())

    categories = [item.category for item in collection.items]
    assert sorted(categories, key=lambda category: category.value) == sorted(
        Category, key=lambda category: category.value
    )
    assert len(set(categories)) == len(categories)


def test_builder_is_deterministic() -> None:
    builder = EvidenceBuilder()
    asset = make_asset()

    assert builder.build(asset) == builder.build(asset)


def test_builder_items_are_placeholder_and_traceable() -> None:
    asset = make_asset()
    collection = EvidenceBuilder().build(asset)

    assert {item.id for item in collection.items} == {
        f"{asset.ticker}.{category.value}" for category in Category
    }
    for item in collection.items:
        assert item.source is EvidenceSource.SYSTEM
        assert item.confidence == 1.0
        assert item.metadata == {}
        assert isinstance(item.timestamp, datetime)


def test_factory_creates_an_evidence_item() -> None:
    item = EvidenceFactory().create(
        id="ev-1",
        category=Category.MARKET,
        title="t",
        description="d",
        source=EvidenceSource.SYSTEM,
        timestamp=datetime(2000, 1, 1),
        confidence=0.5,
        metadata={},
    )

    assert isinstance(item, EvidenceItem)
    assert item.id == "ev-1"
    assert item.category is Category.MARKET
    assert item.metadata == {}


def test_registry_looks_up_by_category() -> None:
    registry = EvidenceRegistry(EvidenceBuilder().build(make_asset()))

    for category in Category:
        found = registry.by_category(category)
        assert len(found) == 1
        assert found[0].category is category


def test_registry_returns_empty_when_no_items_match() -> None:
    asset = make_asset()
    registry = EvidenceRegistry(EvidenceCollection(asset=asset, items=()))

    assert registry.by_category(Category.MARKET) == ()
