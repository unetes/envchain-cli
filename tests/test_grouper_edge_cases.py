"""Edge-case tests for envchain.grouper."""

import pytest

from envchain.grouper import (
    ChainGroup,
    GroupError,
    GroupIndex,
    add_chain_to_group,
    create_group,
    get_group,
    list_groups,
    remove_chain_from_group,
)


@pytest.fixture()
def idx() -> GroupIndex:
    return GroupIndex()


def test_get_group_returns_none_for_unknown(idx):
    assert get_group(idx, "nope") is None


def test_to_dict_chains_are_sorted(idx):
    create_group(idx, "g")
    add_chain_to_group(idx, "g", "z_chain")
    add_chain_to_group(idx, "g", "a_chain")
    d = idx.to_dict()
    assert d["g"]["chains"] == ["a_chain", "z_chain"]


def test_from_dict_empty_preserves_empty_chains():
    data = {"g": {"name": "g", "chains": [], "description": ""}}
    idx = GroupIndex.from_dict(data)
    assert get_group(idx, "g").chains == []


def test_multiple_groups_independent(idx):
    create_group(idx, "a")
    create_group(idx, "b")
    add_chain_to_group(idx, "a", "api")
    assert "api" not in get_group(idx, "b").chains


def test_list_groups_empty_returns_empty_list(idx):
    assert list_groups(idx) == []


def test_group_str_shows_chain_count(idx):
    create_group(idx, "prod")
    add_chain_to_group(idx, "prod", "api")
    add_chain_to_group(idx, "prod", "worker")
    s = str(get_group(idx, "prod"))
    assert "2" in s


def test_roundtrip_empty_index():
    idx = GroupIndex()
    restored = GroupIndex.from_dict(idx.to_dict())
    assert list_groups(restored) == []


def test_chain_group_from_dict_missing_description():
    g = ChainGroup.from_dict({"name": "x", "chains": ["a"]})
    assert g.description == ""


def test_add_then_remove_leaves_empty_list(idx):
    create_group(idx, "g")
    add_chain_to_group(idx, "g", "api")
    remove_chain_from_group(idx, "g", "api")
    assert get_group(idx, "g").chains == []
