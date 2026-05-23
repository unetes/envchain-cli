"""Tests for envchain.archiver."""

from __future__ import annotations

import json
import time
import pytest

from envchain.archiver import (
    ArchiveError,
    create_archive,
    deserialise_archive,
    restore_archive,
    serialise_archive,
    ARCHIVE_VERSION,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name, parent=None, vars=None):
        self.name = name
        self.parent = parent
        self.vars = vars or {}


class _FakeRegistry:
    def __init__(self, chains=None):
        self._chains = {c.name: c for c in (chains or [])}

    def get(self, name):
        return self._chains.get(name)

    def add(self, name, parent=None, vars=None):
        self._chains[name] = _FakeChain(name, parent=parent, vars=vars or {})


def _make_registry():
    return _FakeRegistry([
        _FakeChain("base", vars={"HOST": "localhost", "PORT": "5432"}),
        _FakeChain("prod", parent="base", vars={"PORT": "5433", "ENV": "prod"}),
    ])


# ---------------------------------------------------------------------------
# create_archive
# ---------------------------------------------------------------------------

def test_create_archive_includes_all_chains():
    reg = _make_registry()
    arch = create_archive(reg, ["base", "prod"])
    assert "base" in arch["chains"]
    assert "prod" in arch["chains"]


def test_create_archive_version_is_set():
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    assert arch["version"] == ARCHIVE_VERSION


def test_create_archive_timestamp_is_recent():
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    assert abs(arch["created_at"] - time.time()) < 5


def test_create_archive_stores_vars():
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    assert arch["chains"]["base"]["vars"] == {"HOST": "localhost", "PORT": "5432"}


def test_create_archive_stores_parent():
    reg = _make_registry()
    arch = create_archive(reg, ["prod"])
    assert arch["chains"]["prod"]["parent"] == "base"


def test_create_archive_custom_label():
    reg = _make_registry()
    arch = create_archive(reg, ["base"], label="release-1.0")
    assert arch["label"] == "release-1.0"


def test_create_archive_raises_for_empty_list():
    reg = _make_registry()
    with pytest.raises(ArchiveError, match="No chains"):
        create_archive(reg, [])


def test_create_archive_raises_for_unknown_chain():
    reg = _make_registry()
    with pytest.raises(ArchiveError, match="not found"):
        create_archive(reg, ["ghost"])


# ---------------------------------------------------------------------------
# serialise / deserialise
# ---------------------------------------------------------------------------

def test_serialise_produces_valid_json():
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    raw = serialise_archive(arch)
    parsed = json.loads(raw)
    assert parsed["version"] == ARCHIVE_VERSION


def test_deserialise_round_trips():
    reg = _make_registry()
    arch = create_archive(reg, ["base", "prod"])
    raw = serialise_archive(arch)
    recovered = deserialise_archive(raw)
    assert recovered["chains"].keys() == arch["chains"].keys()


def test_deserialise_raises_on_bad_json():
    with pytest.raises(ArchiveError, match="Invalid archive JSON"):
        deserialise_archive("{not valid json")


def test_deserialise_raises_on_wrong_version():
    raw = json.dumps({"version": 99, "chains": {}})
    with pytest.raises(ArchiveError, match="Unsupported archive version"):
        deserialise_archive(raw)


def test_deserialise_raises_on_missing_chains_key():
    raw = json.dumps({"version": ARCHIVE_VERSION, "label": ""})
    with pytest.raises(ArchiveError, match="missing 'chains'"):
        deserialise_archive(raw)


# ---------------------------------------------------------------------------
# restore_archive
# ---------------------------------------------------------------------------

def test_restore_archive_creates_chains():
    reg = _make_registry()
    arch = create_archive(reg, ["base", "prod"])
    empty_reg = _FakeRegistry()
    restore_archive(arch, empty_reg)
    assert empty_reg.get("base") is not None
    assert empty_reg.get("prod") is not None


def test_restore_archive_returns_restored_names():
    reg = _make_registry()
    arch = create_archive(reg, ["base", "prod"])
    empty_reg = _FakeRegistry()
    restored = restore_archive(arch, empty_reg)
    assert set(restored) == {"base", "prod"}


def test_restore_archive_partial_selection():
    reg = _make_registry()
    arch = create_archive(reg, ["base", "prod"])
    empty_reg = _FakeRegistry()
    restored = restore_archive(arch, empty_reg, chain_names=["base"])
    assert restored == ["base"]
    assert empty_reg.get("prod") is None


def test_restore_archive_raises_when_chain_exists_no_overwrite():
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    with pytest.raises(ArchiveError, match="already exists"):
        restore_archive(arch, reg)


def test_restore_archive_overwrites_when_flag_set():
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    # Modify the registry copy then restore over it
    restored = restore_archive(arch, reg, overwrite=True)
    assert "base" in restored


def test_restore_archive_raises_for_unknown_chain_in_archive():
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    empty_reg = _FakeRegistry()
    with pytest.raises(ArchiveError, match="not found in archive"):
        restore_archive(arch, empty_reg, chain_names=["ghost"])
