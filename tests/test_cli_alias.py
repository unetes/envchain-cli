"""Tests for envchain.cli_alias."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envchain.cli_alias import cmd_alias_add, cmd_alias_list, cmd_alias_remove
from envchain.aliaser import AliasIndex


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"overwrite": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def idx_path(tmp_path) -> Path:
    return tmp_path / "aliases.json"


def test_add_returns_0_on_success(idx_path):
    args = _make_args(alias="prod", chain="production", index_path=idx_path)
    assert cmd_alias_add(args) == 0


def test_add_persists_entry(idx_path):
    args = _make_args(alias="prod", chain="production", index_path=idx_path)
    cmd_alias_add(args)
    data = json.loads(idx_path.read_text())
    assert data["prod"] == "production"


def test_add_duplicate_returns_1(idx_path):
    args = _make_args(alias="prod", chain="production", index_path=idx_path)
    cmd_alias_add(args)
    args2 = _make_args(alias="prod", chain="production-v2", index_path=idx_path)
    assert cmd_alias_add(args2) == 1


def test_add_overwrite_succeeds(idx_path):
    args = _make_args(alias="prod", chain="production", index_path=idx_path)
    cmd_alias_add(args)
    args2 = _make_args(alias="prod", chain="production-v2", overwrite=True, index_path=idx_path)
    assert cmd_alias_add(args2) == 0
    data = json.loads(idx_path.read_text())
    assert data["prod"] == "production-v2"


def test_remove_returns_0_on_success(idx_path):
    add_args = _make_args(alias="dev", chain="development", index_path=idx_path)
    cmd_alias_add(add_args)
    rm_args = _make_args(alias="dev", index_path=idx_path)
    assert cmd_alias_remove(rm_args) == 0


def test_remove_deletes_from_file(idx_path):
    add_args = _make_args(alias="dev", chain="development", index_path=idx_path)
    cmd_alias_add(add_args)
    rm_args = _make_args(alias="dev", index_path=idx_path)
    cmd_alias_remove(rm_args)
    data = json.loads(idx_path.read_text())
    assert "dev" not in data


def test_remove_missing_returns_1(idx_path):
    args = _make_args(alias="ghost", index_path=idx_path)
    assert cmd_alias_remove(args) == 1


def test_list_returns_0_when_empty(idx_path, capsys):
    args = _make_args(chain=None, index_path=idx_path)
    assert cmd_alias_list(args) == 0
    out = capsys.readouterr().out
    assert "No aliases" in out


def test_list_shows_aliases(idx_path, capsys):
    cmd_alias_add(_make_args(alias="prod", chain="production", index_path=idx_path))
    cmd_alias_add(_make_args(alias="dev", chain="development", index_path=idx_path))
    args = _make_args(chain=None, index_path=idx_path)
    cmd_alias_list(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "production" in out
    assert "dev" in out


def test_list_filter_by_chain(idx_path, capsys):
    cmd_alias_add(_make_args(alias="prod", chain="production", index_path=idx_path))
    cmd_alias_add(_make_args(alias="live", chain="production", index_path=idx_path))
    cmd_alias_add(_make_args(alias="dev", chain="development", index_path=idx_path))
    args = _make_args(chain="production", index_path=idx_path)
    cmd_alias_list(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "live" in out
    assert "dev" not in out
