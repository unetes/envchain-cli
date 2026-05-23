"""Tests for envchain.grouper."""

import pytest

from envchain.grouper import (
    ChainGroup,
    GroupError,
    GroupIndex,
    add_chain_to_group,
    create_group,
    delete_group,
    get_group,
    list_groups,
    remove_chain_from_group,
)


@pytest.fixture()
def idx() -> GroupIndex:
    return GroupIndex()


def test_create_group_returns_chain_group(idx):
    g = create_group(idx, "prod")
    assert isinstance(g, ChainGroup)
    assert g.name == "prod"


def test_create_group_stores_description(idx):
    g = create_group(idx, "staging", description="Staging envs")
    assert g.description == "Staging envs"


def test_create_group_raises_on_duplicate(idx):
    create_group(idx, "prod")
    with pytest.raises(GroupError, match="already exists"):
        create_group(idx, "prod")


def test_delete_group_removes_it(idx):
    create_group(idx, "prod")
    delete_group(idx, "prod")
    assert get_group(idx, "prod") is None


def test_delete_group_raises_when_missing(idx):
    with pytest.raises(GroupError, match="does not exist"):
        delete_group(idx, "ghost")


def test_add_chain_to_group_stores_chain(idx):
    create_group(idx, "prod")
    add_chain_to_group(idx, "prod", "api")
    assert "api" in get_group(idx, "prod").chains


def test_add_chain_no_duplicates(idx):
    create_group(idx, "prod")
    add_chain_to_group(idx, "prod", "api")
    add_chain_to_group(idx, "prod", "api")
    assert get_group(idx, "prod").chains.count("api") == 1


def test_add_chain_raises_when_group_missing(idx):
    with pytest.raises(GroupError):
        add_chain_to_group(idx, "ghost", "api")


def test_remove_chain_from_group(idx):
    create_group(idx, "prod")
    add_chain_to_group(idx, "prod", "api")
    remove_chain_from_group(idx, "prod", "api")
    assert "api" not in get_group(idx, "prod").chains


def test_remove_chain_raises_when_not_member(idx):
    create_group(idx, "prod")
    with pytest.raises(GroupError, match="not in group"):
        remove_chain_from_group(idx, "prod", "api")


def test_list_groups_sorted(idx):
    create_group(idx, "z_group")
    create_group(idx, "a_group")
    names = [g.name for g in list_groups(idx)]
    assert names == sorted(names)


def test_group_str_contains_name(idx):
    create_group(idx, "prod")
    add_chain_to_group(idx, "prod", "api")
    assert "prod" in str(get_group(idx, "prod"))


def test_roundtrip_to_from_dict(idx):
    create_group(idx, "prod", description="Production")
    add_chain_to_group(idx, "prod", "api")
    add_chain_to_group(idx, "prod", "worker")
    restored = GroupIndex.from_dict(idx.to_dict())
    g = get_group(restored, "prod")
    assert g is not None
    assert "api" in g.chains
    assert g.description == "Production"
