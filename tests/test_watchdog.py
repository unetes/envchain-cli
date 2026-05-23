"""Tests for envchain.watchdog."""

import time
import pytest

from envchain.watchdog import (
    WatchEntry,
    WatchIndex,
    DriftResult,
    check_drift,
)


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name, vars_, parent=None):
        self.name = name
        self.vars = vars_
        self.parent = parent


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)


# ---------------------------------------------------------------------------
# WatchEntry
# ---------------------------------------------------------------------------

def test_watch_entry_roundtrip():
    e = WatchEntry(chain_name="prod", key="API_KEY", expected_value="secret")
    restored = WatchEntry.from_dict(e.to_dict())
    assert restored.chain_name == "prod"
    assert restored.key == "API_KEY"
    assert restored.expected_value == "secret"


def test_watch_entry_recorded_at_defaults_to_now():
    before = time.time()
    e = WatchEntry(chain_name="x", key="K", expected_value="v")
    assert e.recorded_at >= before


# ---------------------------------------------------------------------------
# WatchIndex
# ---------------------------------------------------------------------------

def test_add_and_entries_for():
    idx = WatchIndex()
    idx.add(WatchEntry("prod", "KEY", "val"))
    entries = idx.entries_for("prod")
    assert len(entries) == 1
    assert entries[0].key == "KEY"


def test_entries_for_unknown_chain_returns_empty():
    idx = WatchIndex()
    assert idx.entries_for("ghost") == []


def test_remove_entry():
    idx = WatchIndex()
    idx.add(WatchEntry("prod", "KEY", "val"))
    idx.remove("prod", "KEY")
    assert idx.entries_for("prod") == []


def test_remove_nonexistent_raises():
    idx = WatchIndex()
    with pytest.raises(KeyError):
        idx.remove("prod", "MISSING")


def test_all_entries_sorted_by_chain_then_key():
    idx = WatchIndex()
    idx.add(WatchEntry("z_chain", "B", "1"))
    idx.add(WatchEntry("a_chain", "Z", "2"))
    idx.add(WatchEntry("a_chain", "A", "3"))
    names = [(e.chain_name, e.key) for e in idx.all_entries()]
    assert names == [("a_chain", "A"), ("a_chain", "Z"), ("z_chain", "B")]


def test_index_roundtrip():
    idx = WatchIndex()
    idx.add(WatchEntry("prod", "TOKEN", "abc"))
    restored = WatchIndex.from_dict(idx.to_dict())
    entries = restored.entries_for("prod")
    assert entries[0].expected_value == "abc"


# ---------------------------------------------------------------------------
# DriftResult
# ---------------------------------------------------------------------------

def test_drift_result_missing():
    dr = DriftResult("prod", "KEY", "val", None)
    assert dr.is_missing
    assert "MISSING" in str(dr)


def test_drift_result_changed():
    dr = DriftResult("prod", "KEY", "old", "new")
    assert not dr.is_missing
    assert "old" in str(dr)
    assert "new" in str(dr)


# ---------------------------------------------------------------------------
# check_drift
# ---------------------------------------------------------------------------

def test_check_drift_no_drift():
    chain = _FakeChain("prod", {"API": "secret"})
    registry = _FakeRegistry([chain])
    idx = WatchIndex()
    idx.add(WatchEntry("prod", "API", "secret"))
    assert check_drift(idx, registry) == []


def test_check_drift_detects_changed_value():
    chain = _FakeChain("prod", {"API": "new_secret"})
    registry = _FakeRegistry([chain])
    idx = WatchIndex()
    idx.add(WatchEntry("prod", "API", "old_secret"))
    results = check_drift(idx, registry)
    assert len(results) == 1
    assert results[0].actual == "new_secret"


def test_check_drift_detects_missing_key():
    chain = _FakeChain("prod", {})
    registry = _FakeRegistry([chain])
    idx = WatchIndex()
    idx.add(WatchEntry("prod", "GONE", "value"))
    results = check_drift(idx, registry)
    assert results[0].is_missing


def test_check_drift_missing_chain():
    registry = _FakeRegistry([])
    idx = WatchIndex()
    idx.add(WatchEntry("ghost", "KEY", "val"))
    results = check_drift(idx, registry)
    assert results[0].is_missing
