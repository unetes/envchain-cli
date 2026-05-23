"""Tests for envchain.pruner."""

from __future__ import annotations

import pytest

from envchain.pruner import PruneError, PruneReport, prune_chain, prune_empty_values


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name: str, vars_: dict):
        self.name = name
        self.vars = dict(vars_)


class _FakeRegistry:
    def __init__(self, chains: dict):
        self._chains = {name: _FakeChain(name, v) for name, v in chains.items()}

    def get(self, name):
        return self._chains.get(name)


def _make_registry(**chains):
    return _FakeRegistry(chains)


# ---------------------------------------------------------------------------
# prune_empty_values
# ---------------------------------------------------------------------------

def test_prune_empty_values_identifies_blank():
    report = prune_empty_values({"A": "hello", "B": "", "C": "   "})
    assert sorted(report.removed_keys) == ["B", "C"]


def test_prune_empty_values_keeps_non_blank():
    report = prune_empty_values({"A": "hello", "B": "world"})
    assert report.removed_keys == []
    assert sorted(report.kept_keys) == ["A", "B"]


def test_prune_empty_values_all_empty():
    report = prune_empty_values({"X": "", "Y": ""})
    assert sorted(report.removed_keys) == ["X", "Y"]
    assert report.kept_keys == []


# ---------------------------------------------------------------------------
# PruneReport.summary
# ---------------------------------------------------------------------------

def test_prune_report_summary_nothing_removed():
    r = PruneReport(chain_name="dev", removed_keys=[], kept_keys=["A"])
    assert "nothing to prune" in r.summary()


def test_prune_report_summary_shows_removed_keys():
    r = PruneReport(chain_name="dev", removed_keys=["B", "C"], kept_keys=["A"])
    assert "B" in r.summary()
    assert "C" in r.summary()
    assert r.total_removed == 2


# ---------------------------------------------------------------------------
# prune_chain – remove_empty
# ---------------------------------------------------------------------------

def test_prune_chain_removes_empty_by_default():
    reg = _make_registry(dev={"HOST": "localhost", "TOKEN": ""})
    report = prune_chain(reg, "dev")
    assert "TOKEN" in report.removed_keys
    assert "HOST" not in report.removed_keys


def test_prune_chain_mutates_chain_vars():
    reg = _make_registry(dev={"HOST": "localhost", "TOKEN": ""})
    prune_chain(reg, "dev")
    assert "TOKEN" not in reg.get("dev").vars


def test_prune_chain_dry_run_does_not_mutate():
    reg = _make_registry(dev={"HOST": "localhost", "TOKEN": ""})
    report = prune_chain(reg, "dev", dry_run=True)
    assert "TOKEN" in report.removed_keys
    assert "TOKEN" in reg.get("dev").vars  # unchanged


# ---------------------------------------------------------------------------
# prune_chain – explicit keys
# ---------------------------------------------------------------------------

def test_prune_chain_explicit_keys_removes_them():
    reg = _make_registry(prod={"A": "1", "B": "2", "C": "3"})
    report = prune_chain(reg, "prod", keys=["A", "C"])
    assert sorted(report.removed_keys) == ["A", "C"]
    assert reg.get("prod").vars == {"B": "2"}


def test_prune_chain_explicit_keys_missing_raises():
    reg = _make_registry(prod={"A": "1"})
    with pytest.raises(PruneError, match="Keys not found"):
        prune_chain(reg, "prod", keys=["Z"])


# ---------------------------------------------------------------------------
# prune_chain – error cases
# ---------------------------------------------------------------------------

def test_prune_chain_unknown_chain_raises():
    reg = _make_registry()
    with pytest.raises(PruneError, match="not found"):
        prune_chain(reg, "ghost")


def test_prune_chain_no_empty_vars_returns_empty_removed():
    reg = _make_registry(dev={"HOST": "localhost", "PORT": "5432"})
    report = prune_chain(reg, "dev")
    assert report.removed_keys == []
    assert report.total_removed == 0
