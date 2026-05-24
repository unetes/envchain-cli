"""Tests for envchain.scoper."""

import pytest

from envchain.scoper import (
    ScopeError,
    ScopeIndex,
    ScopeRule,
    apply_scope,
    get_scope,
    list_scopes,
    remove_scope,
    set_scope,
)


@pytest.fixture()
def idx() -> ScopeIndex:
    return ScopeIndex()


def test_set_scope_returns_scope_rule(idx):
    rule = set_scope(idx, "prod", ["DB_URL", "API_KEY"])
    assert isinstance(rule, ScopeRule)


def test_set_scope_stores_rule(idx):
    set_scope(idx, "prod", ["DB_URL"])
    assert get_scope(idx, "prod") is not None


def test_set_scope_empty_chain_raises(idx):
    with pytest.raises(ScopeError):
        set_scope(idx, "", ["KEY"])


def test_set_scope_replaces_existing(idx):
    set_scope(idx, "prod", ["OLD_KEY"])
    set_scope(idx, "prod", ["NEW_KEY"])
    rule = get_scope(idx, "prod")
    assert rule.allowed_keys == ["NEW_KEY"]


def test_get_scope_returns_none_for_unknown(idx):
    assert get_scope(idx, "unknown") is None


def test_remove_scope_removes_rule(idx):
    set_scope(idx, "dev", ["DEBUG"])
    remove_scope(idx, "dev")
    assert get_scope(idx, "dev") is None


def test_remove_scope_raises_when_missing(idx):
    with pytest.raises(ScopeError):
        remove_scope(idx, "ghost")


def test_apply_scope_filters_vars(idx):
    set_scope(idx, "prod", ["DB_URL", "PORT"])
    result = apply_scope(idx, "prod", {"DB_URL": "x", "PORT": "5432", "SECRET": "s"})
    assert "SECRET" not in result
    assert "DB_URL" in result
    assert "PORT" in result


def test_apply_scope_no_rule_returns_all(idx):
    vars_ = {"A": "1", "B": "2"}
    result = apply_scope(idx, "unscoped", vars_)
    assert result == vars_


def test_apply_scope_empty_allowed_keys_returns_empty(idx):
    set_scope(idx, "strict", [])
    result = apply_scope(idx, "strict", {"A": "1", "B": "2"})
    assert result == {}


def test_list_scopes_sorted(idx):
    set_scope(idx, "z_chain", [])
    set_scope(idx, "a_chain", [])
    names = [r.chain for r in list_scopes(idx)]
    assert names == sorted(names)


def test_scope_rule_roundtrip():
    rule = ScopeRule(chain="prod", allowed_keys=["KEY_A", "KEY_B"])
    restored = ScopeRule.from_dict(rule.to_dict())
    assert restored.chain == rule.chain
    assert restored.allowed_keys == sorted(rule.allowed_keys)


def test_scope_index_roundtrip(idx):
    set_scope(idx, "prod", ["DB_URL"])
    set_scope(idx, "dev", ["DEBUG", "LOG_LEVEL"])
    restored = ScopeIndex.from_dict(idx.to_dict())
    assert get_scope(restored, "prod").allowed_keys == ["DB_URL"]
    assert "DEBUG" in get_scope(restored, "dev").allowed_keys
