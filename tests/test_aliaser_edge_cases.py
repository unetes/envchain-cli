"""Edge-case tests for envchain.aliaser."""

import pytest

from envchain.aliaser import (
    AliasError,
    AliasIndex,
    add_alias,
    aliases_for_chain,
    list_aliases,
    remove_alias,
    resolve_alias,
)


def test_multiple_aliases_same_chain():
    idx = AliasIndex()
    add_alias(idx, "a", "shared")
    add_alias(idx, "b", "shared")
    add_alias(idx, "c", "shared")
    assert aliases_for_chain(idx, "shared") == ["a", "b", "c"]


def test_overwrite_does_not_create_duplicate_key():
    idx = AliasIndex()
    add_alias(idx, "prod", "production")
    add_alias(idx, "prod", "staging", overwrite=True)
    assert len(idx.to_dict()) == 1


def test_from_dict_preserves_all_entries():
    data = {"x": "chain-x", "y": "chain-y", "z": "chain-z"}
    idx = AliasIndex.from_dict(data)
    assert idx.to_dict() == data


def test_to_dict_returns_copy():
    idx = AliasIndex()
    add_alias(idx, "prod", "production")
    d = idx.to_dict()
    d["extra"] = "tampered"
    assert "extra" not in idx.to_dict()


def test_list_aliases_stable_sort():
    idx = AliasIndex()
    for name in ["gamma", "alpha", "beta"]:
        add_alias(idx, name, f"chain-{name}")
    names = [a for a, _ in list_aliases(idx)]
    assert names == sorted(names)


def test_remove_then_re_add():
    idx = AliasIndex()
    add_alias(idx, "prod", "production")
    remove_alias(idx, "prod")
    add_alias(idx, "prod", "production-v2")
    assert resolve_alias(idx, "prod") == "production-v2"


def test_aliases_for_chain_no_match_returns_empty():
    idx = AliasIndex()
    add_alias(idx, "dev", "development")
    assert aliases_for_chain(idx, "nonexistent") == []


def test_add_alias_whitespace_name_is_accepted():
    """Whitespace-only alias is technically non-empty; behaviour is permissive."""
    idx = AliasIndex()
    # Should not raise — validation of meaningful names is caller's responsibility.
    add_alias(idx, "  ", "production")
    assert resolve_alias(idx, "  ") == "production"
