"""Tests for envchain.cli_profile."""

import pytest
from types import SimpleNamespace
from envchain.profiler import ProfileIndex, add_to_profile
from envchain.cli_profile import (
    cmd_profile_add,
    cmd_profile_remove,
    cmd_profile_list,
    cmd_profile_delete,
)


def _make_args(**kwargs):
    return SimpleNamespace(**kwargs)


@pytest.fixture
def idx():
    return ProfileIndex()


def test_cmd_add_returns_0_on_success(idx):
    args = _make_args(profile="dev", chain="app")
    assert cmd_profile_add(args, idx) == 0


def test_cmd_add_stores_chain(idx):
    args = _make_args(profile="dev", chain="app")
    cmd_profile_add(args, idx)
    assert "app" in idx._data["dev"]


def test_cmd_add_empty_profile_returns_1(idx):
    args = _make_args(profile="", chain="app")
    assert cmd_profile_add(args, idx) == 1


def test_cmd_remove_returns_0_on_success(idx):
    add_to_profile(idx, "dev", "app")
    args = _make_args(profile="dev", chain="app")
    assert cmd_profile_remove(args, idx) == 0


def test_cmd_remove_returns_1_when_missing(idx):
    args = _make_args(profile="dev", chain="ghost")
    assert cmd_profile_remove(args, idx) == 1


def test_cmd_list_no_profiles_returns_0(idx, capsys):
    args = _make_args(profile=None)
    rc = cmd_profile_list(args, idx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No profiles" in out


def test_cmd_list_profiles_shows_names(idx, capsys):
    add_to_profile(idx, "dev", "app")
    args = _make_args(profile=None)
    cmd_profile_list(args, idx)
    out = capsys.readouterr().out
    assert "dev" in out


def test_cmd_list_profile_chains(idx, capsys):
    add_to_profile(idx, "dev", "app")
    args = _make_args(profile="dev")
    cmd_profile_list(args, idx)
    out = capsys.readouterr().out
    assert "app" in out


def test_cmd_list_empty_profile_message(idx, capsys):
    args = _make_args(profile="staging")
    cmd_profile_list(args, idx)
    out = capsys.readouterr().out
    assert "empty" in out or "does not exist" in out


def test_cmd_delete_returns_0_on_success(idx):
    add_to_profile(idx, "dev", "app")
    args = _make_args(profile="dev")
    assert cmd_profile_delete(args, idx) == 0


def test_cmd_delete_removes_profile(idx):
    add_to_profile(idx, "dev", "app")
    args = _make_args(profile="dev")
    cmd_profile_delete(args, idx)
    assert "dev" not in idx._data


def test_cmd_delete_missing_returns_1(idx):
    args = _make_args(profile="ghost")
    assert cmd_profile_delete(args, idx) == 1
