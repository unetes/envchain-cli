"""Tests for envchain.summariser."""
from __future__ import annotations

from typing import Dict, List, Optional

import pytest

from envchain.summariser import (
    ChainSummary,
    RegistrySummary,
    summarise_chain,
    summarise_registry,
)


class _FakeChain:
    def __init__(self, name: str, vars_: Dict, parent: Optional[str] = None, resolved: Optional[Dict] = None):
        self.name = name
        self.vars = vars_
        self.parent = parent
        self._resolved = resolved or vars_

    def resolve(self) -> Dict:
        return self._resolved


class _FakeRegistry:
    def __init__(self, chains: List[_FakeChain]):
        self._chains = {c.name: c for c in chains}

    def list(self) -> List[str]:
        return list(self._chains.keys())

    def get(self, name: str) -> Optional[_FakeChain]:
        return self._chains.get(name)


# --- ChainSummary ---

def test_chain_summary_total_keys_own_only():
    s = ChainSummary("dev", None, 3, keys=["A", "B", "C"])
    assert s.total_keys == 3


def test_chain_summary_total_keys_with_inherited():
    s = ChainSummary("dev", "base", 2, keys=["A", "B"], inherited_keys=["C", "D"])
    assert s.total_keys == 4


def test_chain_summary_to_dict_has_required_keys():
    s = ChainSummary("dev", "base", 1, keys=["X"], inherited_keys=["Y"])
    d = s.to_dict()
    assert d["chain"] == "dev"
    assert d["parent"] == "base"
    assert d["own_var_count"] == 1
    assert d["inherited_var_count"] == 1
    assert d["total_var_count"] == 2


def test_chain_summary_to_dict_keys_are_sorted():
    s = ChainSummary("dev", None, 3, keys=["C", "A", "B"])
    assert s.to_dict()["keys"] == ["A", "B", "C"]


# --- summarise_chain ---

def test_summarise_chain_no_parent():
    chain = _FakeChain("base", {"FOO": "1", "BAR": "2"})
    s = summarise_chain(chain)
    assert s.chain_name == "base"
    assert s.parent is None
    assert s.var_count == 2
    assert s.inherited_keys == []


def test_summarise_chain_with_parent_detects_inherited():
    chain = _FakeChain(
        "dev", {"DEV_KEY": "x"}, parent="base",
        resolved={"FOO": "1", "BAR": "2", "DEV_KEY": "x"}
    )
    s = summarise_chain(chain)
    assert s.var_count == 1
    assert set(s.inherited_keys) == {"FOO", "BAR"}


def test_summarise_chain_resolve_error_falls_back():
    class BadChain(_FakeChain):
        def resolve(self):
            raise RuntimeError("cycle")

    chain = BadChain("dev", {"KEY": "v"}, parent="base")
    s = summarise_chain(chain)
    assert s.var_count == 1
    assert s.inherited_keys == []


# --- summarise_registry ---

def test_summarise_registry_chain_count():
    reg = _FakeRegistry([
        _FakeChain("base", {"A": "1"}),
        _FakeChain("dev", {"B": "2"}),
    ])
    rs = summarise_registry(reg)
    assert rs.chain_count == 2


def test_summarise_registry_total_vars():
    reg = _FakeRegistry([
        _FakeChain("base", {"A": "1", "B": "2"}),
        _FakeChain("dev", {"C": "3"}),
    ])
    rs = summarise_registry(reg)
    assert rs.total_vars == 3


def test_summarise_registry_to_dict_structure():
    reg = _FakeRegistry([_FakeChain("base", {"X": "1"})])
    d = summarise_registry(reg).to_dict()
    assert "chain_count" in d
    assert "total_own_vars" in d
    assert isinstance(d["chains"], list)
    assert d["chains"][0]["chain"] == "base"


def test_summarise_registry_chains_sorted():
    reg = _FakeRegistry([
        _FakeChain("z_chain", {}),
        _FakeChain("a_chain", {}),
    ])
    rs = summarise_registry(reg)
    names = [s.chain_name for s in rs.chain_summaries]
    assert names == sorted(names)
