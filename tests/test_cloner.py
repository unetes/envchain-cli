"""Tests for envchain.cloner."""

import pytest

from envchain.cloner import CloneError, clone_chain
from envchain.registry import ChainRegistry


def _make_registry() -> ChainRegistry:
    reg = ChainRegistry()
    reg.add("base", vars={"HOST": "localhost", "PORT": "5432"})
    reg.add("child", vars={"PORT": "9999", "DEBUG": "1"}, parent="base")
    return reg


def test_clone_creates_new_chain():
    reg = _make_registry()
    clone_chain(reg, "base", "base_clone")
    assert reg.get("base_clone") is not None


def test_clone_vars_match_source():
    reg = _make_registry()
    clone_chain(reg, "base", "base_clone")
    assert reg.get("base_clone").vars == {"HOST": "localhost", "PORT": "5432"}


def test_clone_inherits_source_parent_by_default():
    reg = _make_registry()
    clone_chain(reg, "child", "child_clone")
    assert reg.get("child_clone").parent == "base"


def test_clone_no_keep_parent_creates_root_chain():
    reg = _make_registry()
    clone_chain(reg, "child", "child_root", keep_parent=False)
    assert reg.get("child_root").parent is None


def test_clone_new_parent_overrides_source_parent():
    reg = _make_registry()
    reg.add("other", vars={"X": "1"})
    clone_chain(reg, "child", "child_reparented", new_parent="other")
    assert reg.get("child_reparented").parent == "other"


def test_clone_raises_when_source_missing():
    reg = _make_registry()
    with pytest.raises(CloneError, match="does not exist"):
        clone_chain(reg, "nonexistent", "dest")


def test_clone_raises_when_dest_exists_no_overwrite():
    reg = _make_registry()
    with pytest.raises(CloneError, match="already exists"):
        clone_chain(reg, "base", "child")


def test_clone_overwrite_replaces_existing():
    reg = _make_registry()
    clone_chain(reg, "base", "child", overwrite=True)
    assert reg.get("child").vars == {"HOST": "localhost", "PORT": "5432"}


def test_clone_raises_when_dest_equals_source():
    reg = _make_registry()
    with pytest.raises(CloneError, match="must differ"):
        clone_chain(reg, "base", "base")


def test_clone_raises_when_new_parent_missing():
    reg = _make_registry()
    with pytest.raises(CloneError, match="parent chain 'ghost' does not exist"):
        clone_chain(reg, "base", "base_clone", new_parent="ghost")


def test_clone_does_not_mutate_source_vars():
    reg = _make_registry()
    clone_chain(reg, "base", "base_clone")
    reg.get("base_clone").vars["NEW_KEY"] = "value"
    assert "NEW_KEY" not in reg.get("base").vars
