"""Tests for envchain.cli_freeze."""

import argparse
import pytest
from pathlib import Path

from envchain.freezer import FreezeIndex, freeze, save_freeze_index
from envchain.cli_freeze import cmd_freeze_add, cmd_freeze_remove, cmd_freeze_list


def _make_args(tmp_path: Path, **kwargs) -> argparse.Namespace:
    defaults = {"index_path": str(tmp_path / "freeze.json"), "reason": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_add_returns_0_on_success(tmp_path):
    args = _make_args(tmp_path, chain="prod")
    assert cmd_freeze_add(args) == 0


def test_cmd_add_persists_freeze(tmp_path):
    args = _make_args(tmp_path, chain="prod", reason="deploy")
    cmd_freeze_add(args)
    from envchain.freezer import load_freeze_index, is_frozen, freeze_reason
    idx = load_freeze_index(Path(args.index_path))
    assert is_frozen(idx, "prod")
    assert freeze_reason(idx, "prod") == "deploy"


def test_cmd_add_returns_1_when_already_frozen(tmp_path):
    args = _make_args(tmp_path, chain="prod")
    cmd_freeze_add(args)
    assert cmd_freeze_add(args) == 1


def test_cmd_remove_returns_0_on_success(tmp_path):
    add_args = _make_args(tmp_path, chain="prod")
    cmd_freeze_add(add_args)
    rm_args = _make_args(tmp_path, chain="prod")
    assert cmd_freeze_remove(rm_args) == 0


def test_cmd_remove_removes_freeze(tmp_path):
    add_args = _make_args(tmp_path, chain="prod")
    cmd_freeze_add(add_args)
    rm_args = _make_args(tmp_path, chain="prod")
    cmd_freeze_remove(rm_args)
    from envchain.freezer import load_freeze_index, is_frozen
    idx = load_freeze_index(Path(add_args.index_path))
    assert not is_frozen(idx, "prod")


def test_cmd_remove_returns_1_when_not_frozen(tmp_path):
    args = _make_args(tmp_path, chain="prod")
    assert cmd_freeze_remove(args) == 1


def test_cmd_list_returns_0_when_empty(tmp_path, capsys):
    args = _make_args(tmp_path)
    rc = cmd_freeze_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No chains" in out


def test_cmd_list_shows_frozen_chain(tmp_path, capsys):
    add_args = _make_args(tmp_path, chain="staging", reason="audit")
    cmd_freeze_add(add_args)
    list_args = _make_args(tmp_path)
    cmd_freeze_list(list_args)
    out = capsys.readouterr().out
    assert "staging" in out
    assert "audit" in out


def test_cmd_list_shows_multiple_chains_sorted(tmp_path, capsys):
    for chain in ["z-env", "a-env"]:
        cmd_freeze_add(_make_args(tmp_path, chain=chain))
    cmd_freeze_list(_make_args(tmp_path))
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    assert lines[0].startswith("a-env")
    assert lines[1].startswith("z-env")
