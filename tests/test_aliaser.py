"""Tests for envchain.aliaser."""

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


@pytest.fixture()
def idx() -> AliasIndex:
    return AliasIndex()


def test_add_alias_stores_mapping(idx):
    add_alias(idx, "prod", "production")
    assert idx.to_dict()["prod"] == "production"


def test_resolve_alias_returns_chain_name(idx):
    add_alias(idx, "dev", "development")
    assert resolve_alias(idx, "dev") == "development"


def test_resolve_alias_raises_when_missing(idx):
    with pytest.raises(AliasError, match="does not exist"):
        resolve_alias(idx, "ghost")


def test_add_alias_raises_on_duplicate_without_overwrite(idx):
    add_alias(idx, "prod", "production")
    with pytest.raises(AliasError, match="already exists"):
        add_alias(idx, "prod", "production-v2")


def test_add_alias_overwrite_replaces_target(idx):
    add_alias(idx, "prod", "production")
    add_alias(idx, "prod", "production-v2", overwrite=True)
    assert resolve_alias(idx, "prod") == "production-v2"


def test_add_alias_raises_on_empty_alias(idx):
    with pytest.raises(AliasError, match="empty"):
        add_alias(idx, "", "production")


def test_add_alias_raises_on_empty_chain_name(idx):
    with pytest.raises(AliasError, match="empty"):
        add_alias(idx, "prod", "")


def test_add_alias_raises_when_alias_equals_chain(idx):
    with pytest.raises(AliasError, match="itself"):
        add_alias(idx, "prod", "prod")


def test_remove_alias_deletes_entry(idx):
    add_alias(idx, "prod", "production")
    remove_alias(idx, "prod")
    assert "prod" not in idx.to_dict()


def test_remove_alias_raises_when_missing(idx):
    with pytest.raises(AliasError, match="does not exist"):
        remove_alias(idx, "ghost")


def test_list_aliases_returns_sorted_pairs(idx):
    add_alias(idx, "z", "zebra")
    add_alias(idx, "a", "alpha")
    result = list_aliases(idx)
    assert result == [("a", "alpha"), ("z", "zebra")]


def test_list_aliases_empty(idx):
    assert list_aliases(idx) == []


def test_aliases_for_chain_returns_matching(idx):
    add_alias(idx, "prod", "production")
    add_alias(idx, "live", "production")
    add_alias(idx, "dev", "development")
    result = aliases_for_chain(idx, "production")
    assert result == ["live", "prod"]


def test_aliases_for_chain_empty_when_none(idx):
    add_alias(idx, "dev", "development")
    assert aliases_for_chain(idx, "production") == []


def test_roundtrip_via_dict(idx):
    add_alias(idx, "prod", "production")
    add_alias(idx, "dev", "development")
    restored = AliasIndex.from_dict(idx.to_dict())
    assert list_aliases(restored) == list_aliases(idx)
