"""Tests for envchain.copier."""

import pytest

from envchain.copier import CopyError, copy_chain
from envchain.registry import ChainRegistry


def _make_registry():
    reg = ChainRegistry()
    reg.add("base", vars={"HOST": "localhost", "PORT": "5432", "DEBUG": "false"})
    reg.add("child", vars={"DEBUG": "true"}, parent="base")
    return reg


def test_copy_chain_creates_new_chain():
    reg = _make_registry()
    copy_chain(reg, "base", "base_copy")
    assert reg.get("base_copy") is not None


def test_copy_chain_vars_match_source():
    reg = _make_registry()
    copy_chain(reg, "base", "base_copy")
    assert reg.get("base_copy")["vars"] == {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"}


def test_copy_chain_inherits_parent_by_default():
    reg = _make_registry()
    copy_chain(reg, "child", "child_copy")
    assert reg.get("child_copy")["parent"] == "base"


def test_copy_chain_no_inherit_parent():
    reg = _make_registry()
    copy_chain(reg, "child", "child_copy", inherit_parent=False)
    assert reg.get("child_copy").get("parent") is None


def test_copy_chain_include_keys():
    reg = _make_registry()
    copy_chain(reg, "base", "base_partial", include_keys=["HOST", "PORT"])
    assert reg.get("base_partial")["vars"] == {"HOST": "localhost", "PORT": "5432"}


def test_copy_chain_exclude_keys():
    reg = _make_registry()
    copy_chain(reg, "base", "base_no_debug", exclude_keys=["DEBUG"])
    assert "DEBUG" not in reg.get("base_no_debug")["vars"]
    assert reg.get("base_no_debug")["vars"]["HOST"] == "localhost"


def test_copy_chain_raises_when_src_missing():
    reg = _make_registry()
    with pytest.raises(CopyError, match="does not exist"):
        copy_chain(reg, "nonexistent", "new_chain")


def test_copy_chain_raises_when_dst_exists_no_overwrite():
    reg = _make_registry()
    with pytest.raises(CopyError, match="already exists"):
        copy_chain(reg, "base", "child")


def test_copy_chain_overwrite_replaces_dst():
    reg = _make_registry()
    copy_chain(reg, "base", "child", overwrite=True)
    assert reg.get("child")["vars"] == {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"}


def test_copy_chain_invalid_dst_name_raises():
    from envchain.validator import ValidationError
    reg = _make_registry()
    with pytest.raises(ValidationError):
        copy_chain(reg, "base", "123-invalid")


def test_copy_chain_does_not_mutate_source():
    reg = _make_registry()
    copy_chain(reg, "base", "base_copy")
    reg.get("base_copy")["vars"]["NEW_KEY"] = "surprise"
    assert "NEW_KEY" not in reg.get("base")["vars"]
