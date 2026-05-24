"""Edge-case tests for envchain.migrator."""

import pytest
from envchain.migrator import MigrateError, MigrateReport, migrate_keys


class _FakeChain:
    def __init__(self, name, vars_):
        self.name = name
        self.vars = dict(vars_)


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)


def test_migrate_empty_source_produces_empty_report():
    src = _FakeChain("src", {})
    dst = _FakeChain("dst", {})
    reg = _FakeRegistry([src, dst])
    report = migrate_keys(reg, "src", "dst")
    assert report.moved == []
    assert report.skipped == []


def test_migrate_preserves_existing_dest_keys_not_in_source():
    src = _FakeChain("src", {"A": "1"})
    dst = _FakeChain("dst", {"Z": "99"})
    reg = _FakeRegistry([src, dst])
    migrate_keys(reg, "src", "dst")
    assert dst.vars["Z"] == "99"


def test_migrate_remap_collision_without_overwrite_skips():
    src = _FakeChain("src", {"A": "1"})
    dst = _FakeChain("dst", {"B": "existing"})
    reg = _FakeRegistry([src, dst])
    report = migrate_keys(reg, "src", "dst", keys=["A"], remap={"A": "B"})
    assert "A" in report.skipped
    assert dst.vars["B"] == "existing"


def test_migrate_remap_collision_with_overwrite_replaces():
    src = _FakeChain("src", {"A": "new"})
    dst = _FakeChain("dst", {"B": "old"})
    reg = _FakeRegistry([src, dst])
    migrate_keys(reg, "src", "dst", keys=["A"], remap={"A": "B"}, overwrite=True)
    assert dst.vars["B"] == "new"


def test_migrate_report_summary_mentions_remap():
    src = _FakeChain("src", {"A": "1"})
    dst = _FakeChain("dst", {})
    reg = _FakeRegistry([src, dst])
    report = migrate_keys(reg, "src", "dst", keys=["A"], remap={"A": "ALPHA"})
    assert "ALPHA" in report.summary()


def test_migrate_multiple_remaps():
    src = _FakeChain("src", {"A": "1", "B": "2"})
    dst = _FakeChain("dst", {})
    reg = _FakeRegistry([src, dst])
    report = migrate_keys(reg, "src", "dst", remap={"A": "ALPHA", "B": "BETA"})
    assert "ALPHA" in dst.vars
    assert "BETA" in dst.vars
    assert len(report.remapped) == 2


def test_migrate_partial_keys_leaves_others_in_source():
    src = _FakeChain("src", {"A": "1", "B": "2"})
    dst = _FakeChain("dst", {})
    reg = _FakeRegistry([src, dst])
    migrate_keys(reg, "src", "dst", keys=["A"], remove_source=True)
    assert "A" not in src.vars
    assert "B" in src.vars
