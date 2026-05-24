"""Tests for envchain.migrator."""

import pytest
from envchain.migrator import MigrateError, MigrateReport, migrate_keys


class _FakeChain:
    def __init__(self, name: str, vars_: dict):
        self.name = name
        self.vars = dict(vars_)


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)


def _make_registry():
    src = _FakeChain("src", {"A": "1", "B": "2", "C": "3"})
    dst = _FakeChain("dst", {"X": "9"})
    return _FakeRegistry([src, dst])


def test_migrate_moves_all_keys_by_default():
    reg = _make_registry()
    report = migrate_keys(reg, "src", "dst")
    assert set(report.moved) == {"A", "B", "C"}


def test_migrate_dest_contains_moved_keys():
    reg = _make_registry()
    migrate_keys(reg, "src", "dst")
    dst = reg.get("dst")
    assert dst.vars["A"] == "1"
    assert dst.vars["B"] == "2"


def test_migrate_subset_of_keys():
    reg = _make_registry()
    report = migrate_keys(reg, "src", "dst", keys=["A"])
    assert report.moved == ["A"]
    assert "B" not in reg.get("dst").vars


def test_migrate_with_remap():
    reg = _make_registry()
    report = migrate_keys(reg, "src", "dst", keys=["A"], remap={"A": "ALPHA"})
    assert "ALPHA" in reg.get("dst").vars
    assert reg.get("dst").vars["ALPHA"] == "1"
    assert report.remapped == {"A": "ALPHA"}


def test_migrate_skip_existing_without_overwrite():
    reg = _make_registry()
    reg.get("dst").vars["A"] = "old"
    report = migrate_keys(reg, "src", "dst", keys=["A"])
    assert "A" in report.skipped
    assert reg.get("dst").vars["A"] == "old"


def test_migrate_overwrite_replaces_existing():
    reg = _make_registry()
    reg.get("dst").vars["A"] = "old"
    report = migrate_keys(reg, "src", "dst", keys=["A"], overwrite=True)
    assert "A" in report.moved
    assert reg.get("dst").vars["A"] == "1"


def test_migrate_remove_source_deletes_keys():
    reg = _make_registry()
    migrate_keys(reg, "src", "dst", keys=["A"], remove_source=True)
    assert "A" not in reg.get("src").vars
    assert "B" in reg.get("src").vars


def test_migrate_raises_on_missing_source_chain():
    reg = _make_registry()
    with pytest.raises(MigrateError, match="Source chain"):
        migrate_keys(reg, "ghost", "dst")


def test_migrate_raises_on_missing_dest_chain():
    reg = _make_registry()
    with pytest.raises(MigrateError, match="Destination chain"):
        migrate_keys(reg, "src", "nowhere")


def test_migrate_raises_on_missing_key_in_source():
    reg = _make_registry()
    with pytest.raises(MigrateError, match="Key 'Z' not found"):
        migrate_keys(reg, "src", "dst", keys=["Z"])


def test_report_summary_contains_counts():
    reg = _make_registry()
    report = migrate_keys(reg, "src", "dst")
    summary = report.summary()
    assert "3" in summary
    assert "src" in summary
    assert "dst" in summary


def test_report_total_moved():
    reg = _make_registry()
    report = migrate_keys(reg, "src", "dst", keys=["A", "B"])
    assert report.total_moved == 2
