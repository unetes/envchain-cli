"""Tests for envchain.promoter."""

from __future__ import annotations

import pytest

from envchain.promoter import PromoteError, promote_keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name: str, vars_: dict, parent: str | None = None):
        self.name = name
        self.vars = dict(vars_)
        self.parent = parent


class _FakeRegistry:
    def __init__(self):
        self._chains: dict[str, _FakeChain] = {}
        self._updated: dict[str, dict] = {}

    def add(self, chain: _FakeChain):
        self._chains[chain.name] = chain

    def get(self, name: str):
        return self._chains.get(name)

    def update_vars(self, name: str, vars_: dict):
        self._chains[name].vars = dict(vars_)
        self._updated[name] = dict(vars_)


def _make_registry():
    reg = _FakeRegistry()
    reg.add(_FakeChain("base", {"HOST": "localhost", "PORT": "5432"}))
    reg.add(_FakeChain("dev", {"HOST": "dev.local", "DEBUG": "1"}, parent="base"))
    return reg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_promote_returns_promoted_mapping():
    reg = _make_registry()
    result = promote_keys(reg, "dev", "base", ["DEBUG"])
    assert result == {"DEBUG": "1"}


def test_promote_adds_key_to_target():
    reg = _make_registry()
    promote_keys(reg, "dev", "base", ["DEBUG"])
    assert reg.get("base").vars["DEBUG"] == "1"


def test_promote_multiple_keys():
    reg = _make_registry()
    promote_keys(reg, "dev", "base", ["DEBUG", "HOST"], overwrite=True)
    assert reg.get("base").vars["DEBUG"] == "1"
    assert reg.get("base").vars["HOST"] == "dev.local"


def test_promote_raises_when_source_missing():
    reg = _make_registry()
    with pytest.raises(PromoteError, match="Source chain"):
        promote_keys(reg, "ghost", "base", ["DEBUG"])


def test_promote_raises_when_target_missing():
    reg = _make_registry()
    with pytest.raises(PromoteError, match="Target chain"):
        promote_keys(reg, "dev", "ghost", ["DEBUG"])


def test_promote_raises_when_key_missing_in_source():
    reg = _make_registry()
    with pytest.raises(PromoteError, match="Key 'MISSING'"):
        promote_keys(reg, "dev", "base", ["MISSING"])


def test_promote_raises_on_conflict_without_overwrite():
    reg = _make_registry()
    with pytest.raises(PromoteError, match="already exists"):
        promote_keys(reg, "dev", "base", ["HOST"])


def test_promote_overwrite_replaces_value():
    reg = _make_registry()
    promote_keys(reg, "dev", "base", ["HOST"], overwrite=True)
    assert reg.get("base").vars["HOST"] == "dev.local"


def test_promote_remove_from_source():
    reg = _make_registry()
    promote_keys(reg, "dev", "base", ["DEBUG"], remove_from_source=True)
    assert "DEBUG" not in reg.get("dev").vars


def test_promote_source_unchanged_when_not_removing():
    reg = _make_registry()
    promote_keys(reg, "dev", "base", ["DEBUG"])
    assert "DEBUG" in reg.get("dev").vars
