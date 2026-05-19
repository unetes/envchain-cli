"""Tests for Chain resolution and ChainRegistry."""

import pytest

from envchain.chain import Chain
from envchain.registry import ChainRegistry


# ---------------------------------------------------------------------------
# Chain.resolve tests
# ---------------------------------------------------------------------------


def _make_registry(*chains: Chain) -> dict:
    return {c.name: c for c in chains}


def test_chain_no_parent_returns_own_vars():
    chain = Chain(name="base", variables={"FOO": "bar", "BAZ": "qux"})
    assert chain.resolve({"base": chain}) == {"FOO": "bar", "BAZ": "qux"}


def test_chain_inherits_parent_vars():
    parent = Chain(name="base", variables={"FOO": "from_base", "SHARED": "base_val"})
    child = Chain(name="dev", variables={"SHARED": "dev_val"}, parent="base")
    registry = _make_registry(parent, child)
    resolved = child.resolve(registry)
    assert resolved["FOO"] == "from_base"          # inherited
    assert resolved["SHARED"] == "dev_val"          # overridden


def test_chain_multi_level_inheritance():
    root = Chain(name="root", variables={"A": "1", "B": "2"})
    mid = Chain(name="mid", variables={"B": "mid_b", "C": "3"}, parent="root")
    leaf = Chain(name="leaf", variables={"C": "leaf_c"}, parent="mid")
    registry = _make_registry(root, mid, leaf)
    resolved = leaf.resolve(registry)
    assert resolved == {"A": "1", "B": "mid_b", "C": "leaf_c"}


def test_chain_raises_on_circular_inheritance():
    a = Chain(name="a", variables={}, parent="b")
    b = Chain(name="b", variables={}, parent="a")
    registry = _make_registry(a, b)
    with pytest.raises(ValueError, match="Circular"):
        a.resolve(registry)


def test_chain_raises_on_missing_parent():
    child = Chain(name="child", variables={}, parent="ghost")
    with pytest.raises(ValueError, match="does not exist"):
        child.resolve({"child": child})


# ---------------------------------------------------------------------------
# ChainRegistry tests
# ---------------------------------------------------------------------------


def test_registry_add_and_get():
    reg = ChainRegistry()
    chain = Chain(name="prod", variables={"ENV": "production"})
    reg.add(chain)
    assert reg.get("prod") is chain


def test_registry_add_duplicate_raises():
    reg = ChainRegistry()
    reg.add(Chain(name="dup"))
    with pytest.raises(ValueError, match="already exists"):
        reg.add(Chain(name="dup"))


def test_registry_get_missing_raises():
    reg = ChainRegistry()
    with pytest.raises(KeyError):
        reg.get("nope")


def test_registry_remove():
    reg = ChainRegistry()
    reg.add(Chain(name="tmp"))
    reg.remove("tmp")
    assert len(reg) == 0


def test_registry_list_names_sorted():
    reg = ChainRegistry()
    for name in ["zebra", "alpha", "mango"]:
        reg.add(Chain(name=name))
    assert reg.list_names() == ["alpha", "mango", "zebra"]


def test_registry_resolve_delegates_correctly():
    reg = ChainRegistry()
    reg.add(Chain(name="base", variables={"X": "1"}))
    reg.add(Chain(name="child", variables={"Y": "2"}, parent="base"))
    assert reg.resolve("child") == {"X": "1", "Y": "2"}
