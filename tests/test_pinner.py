"""Tests for envchain.pinner module."""
import pytest
from envchain.pinner import PinIndex, PinError, apply_pins


@pytest.fixture
def idx():
    return PinIndex()


def test_pin_adds_key(idx):
    idx.pin("prod", "DB_URL")
    assert idx.is_pinned("prod", "DB_URL")


def test_unpin_removes_key(idx):
    idx.pin("prod", "DB_URL")
    idx.unpin("prod", "DB_URL")
    assert not idx.is_pinned("prod", "DB_URL")


def test_unpin_raises_when_not_pinned(idx):
    with pytest.raises(PinError, match="not pinned"):
        idx.unpin("prod", "MISSING_KEY")


def test_is_pinned_returns_false_for_unknown_chain(idx):
    assert not idx.is_pinned("nonexistent", "KEY")


def test_pinned_keys_returns_sorted_list(idx):
    idx.pin("prod", "Z_KEY")
    idx.pin("prod", "A_KEY")
    idx.pin("prod", "M_KEY")
    assert idx.pinned_keys("prod") == ["A_KEY", "M_KEY", "Z_KEY"]


def test_pinned_keys_empty_for_unknown_chain(idx):
    assert idx.pinned_keys("ghost") == []


def test_all_pins_excludes_empty_chains(idx):
    idx.pin("prod", "KEY")
    idx.pin("dev", "KEY")
    idx.unpin("dev", "KEY")
    result = idx.all_pins()
    assert "prod" in result
    assert "dev" not in result


def test_to_dict_roundtrip(idx):
    idx.pin("prod", "DB_URL")
    idx.pin("prod", "SECRET")
    data = idx.to_dict()
    restored = PinIndex.from_dict(data)
    assert restored.is_pinned("prod", "DB_URL")
    assert restored.is_pinned("prod", "SECRET")


def test_from_dict_empty():
    idx = PinIndex.from_dict({})
    assert idx.all_pins() == {}


def test_multiple_chains_independent(idx):
    idx.pin("prod", "KEY")
    idx.pin("staging", "OTHER")
    assert not idx.is_pinned("prod", "OTHER")
    assert not idx.is_pinned("staging", "KEY")


def test_apply_pins_returns_resolved_vars():
    pin_index = PinIndex()
    pin_index.pin("prod", "DB_URL")
    resolved = {"DB_URL": "prod-db", "PORT": "5432"}
    parent = {"DB_URL": "base-db"}
    result = apply_pins(resolved, "prod", pin_index, parent)
    assert result["DB_URL"] == "prod-db"
    assert result["PORT"] == "5432"


def test_apply_pins_raises_when_pinned_key_missing():
    pin_index = PinIndex()
    pin_index.pin("prod", "GHOST_KEY")
    with pytest.raises(PinError, match="Pinned key"):
        apply_pins({}, "prod", pin_index, {})
