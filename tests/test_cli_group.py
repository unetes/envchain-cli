"""Tests for envchain.cli_group."""

import argparse
import json
from pathlib import Path

import pytest

from envchain.cli_group import (
    cmd_group_add,
    cmd_group_create,
    cmd_group_delete,
    cmd_group_list,
    cmd_group_remove,
)
from envchain.grouper import GroupIndex


def _make_args(path: Path, **kwargs) -> argparse.Namespace:
    ns = argparse.Namespace(index_path=str(path), **kwargs)
    return ns


@pytest.fixture()
def idx_path(tmp_path) -> Path:
    return tmp_path / "groups.json"


def test_create_returns_0_on_success(idx_path):
    args = _make_args(idx_path, name="prod", description="")
    assert cmd_group_create(args) == 0


def test_create_persists_group(idx_path):
    args = _make_args(idx_path, name="prod", description="")
    cmd_group_create(args)
    data = json.loads(idx_path.read_text())
    assert "prod" in data


def test_create_duplicate_returns_1(idx_path, capsys):
    args = _make_args(idx_path, name="prod", description="")
    cmd_group_create(args)
    rc = cmd_group_create(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().out


def test_delete_returns_0_on_success(idx_path):
    cmd_group_create(_make_args(idx_path, name="prod", description=""))
    rc = cmd_group_delete(_make_args(idx_path, name="prod"))
    assert rc == 0


def test_delete_missing_returns_1(idx_path):
    rc = cmd_group_delete(_make_args(idx_path, name="ghost"))
    assert rc == 1


def test_add_chain_returns_0(idx_path):
    cmd_group_create(_make_args(idx_path, name="prod", description=""))
    rc = cmd_group_add(_make_args(idx_path, group="prod", chain="api"))
    assert rc == 0


def test_add_chain_persists(idx_path):
    cmd_group_create(_make_args(idx_path, name="prod", description=""))
    cmd_group_add(_make_args(idx_path, group="prod", chain="api"))
    data = json.loads(idx_path.read_text())
    assert "api" in data["prod"]["chains"]


def test_add_chain_missing_group_returns_1(idx_path):
    rc = cmd_group_add(_make_args(idx_path, group="ghost", chain="api"))
    assert rc == 1


def test_remove_chain_returns_0(idx_path):
    cmd_group_create(_make_args(idx_path, name="prod", description=""))
    cmd_group_add(_make_args(idx_path, group="prod", chain="api"))
    rc = cmd_group_remove(_make_args(idx_path, group="prod", chain="api"))
    assert rc == 0


def test_remove_chain_not_member_returns_1(idx_path):
    cmd_group_create(_make_args(idx_path, name="prod", description=""))
    rc = cmd_group_remove(_make_args(idx_path, group="prod", chain="api"))
    assert rc == 1


def test_list_empty_returns_0(idx_path, capsys):
    rc = cmd_group_list(_make_args(idx_path))
    assert rc == 0
    assert "No groups" in capsys.readouterr().out


def test_list_shows_group_names(idx_path, capsys):
    cmd_group_create(_make_args(idx_path, name="prod", description=""))
    cmd_group_create(_make_args(idx_path, name="dev", description=""))
    cmd_group_list(_make_args(idx_path))
    out = capsys.readouterr().out
    assert "prod" in out
    assert "dev" in out
