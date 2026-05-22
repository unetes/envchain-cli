"""Tests for envchain.profiler."""

import pytest
from envchain.profiler import (
    ProfileError,
    ProfileIndex,
    add_to_profile,
    remove_from_profile,
    chains_for_profile,
    profiles_for_chain,
    list_profiles,
    delete_profile,
)


@pytest.fixture
def idx():
    return ProfileIndex()


def test_add_to_profile_creates_profile(idx):
    add_to_profile(idx, "dev", "app")
    assert "dev" in idx._data


def test_add_to_profile_stores_chain(idx):
    add_to_profile(idx, "dev", "app")
    assert "app" in idx._data["dev"]


def test_add_to_profile_no_duplicates(idx):
    add_to_profile(idx, "dev", "app")
    add_to_profile(idx, "dev", "app")
    assert idx._data["dev"].count("app") == 1


def test_add_to_profile_sorted(idx):
    add_to_profile(idx, "dev", "zebra")
    add_to_profile(idx, "dev", "alpha")
    assert idx._data["dev"] == ["alpha", "zebra"]


def test_add_empty_profile_raises(idx):
    with pytest.raises(ProfileError):
        add_to_profile(idx, "", "app")


def test_add_empty_chain_raises(idx):
    with pytest.raises(ProfileError):
        add_to_profile(idx, "dev", "")


def test_remove_from_profile_disassociates(idx):
    add_to_profile(idx, "dev", "app")
    remove_from_profile(idx, "dev", "app")
    assert "app" not in idx._data.get("dev", [])


def test_remove_deletes_empty_profile(idx):
    add_to_profile(idx, "dev", "app")
    remove_from_profile(idx, "dev", "app")
    assert "dev" not in idx._data


def test_remove_missing_chain_raises(idx):
    with pytest.raises(ProfileError):
        remove_from_profile(idx, "dev", "missing")


def test_chains_for_profile_returns_sorted(idx):
    add_to_profile(idx, "prod", "svc-b")
    add_to_profile(idx, "prod", "svc-a")
    assert chains_for_profile(idx, "prod") == ["svc-a", "svc-b"]


def test_chains_for_profile_unknown_returns_empty(idx):
    assert chains_for_profile(idx, "nonexistent") == []


def test_profiles_for_chain_returns_sorted(idx):
    add_to_profile(idx, "prod", "app")
    add_to_profile(idx, "dev", "app")
    assert profiles_for_chain(idx, "app") == ["dev", "prod"]


def test_profiles_for_chain_unknown_returns_empty(idx):
    assert profiles_for_chain(idx, "ghost") == []


def test_list_profiles_sorted(idx):
    add_to_profile(idx, "staging", "x")
    add_to_profile(idx, "dev", "x")
    assert list_profiles(idx) == ["dev", "staging"]


def test_delete_profile_removes_it(idx):
    add_to_profile(idx, "dev", "app")
    delete_profile(idx, "dev")
    assert "dev" not in idx._data


def test_delete_profile_missing_raises(idx):
    with pytest.raises(ProfileError):
        delete_profile(idx, "ghost")


def test_roundtrip_serialization(idx):
    add_to_profile(idx, "dev", "app")
    add_to_profile(idx, "prod", "app")
    restored = ProfileIndex.from_dict(idx.to_dict())
    assert chains_for_profile(restored, "dev") == ["app"]
    assert chains_for_profile(restored, "prod") == ["app"]
