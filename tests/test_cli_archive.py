"""Tests for envchain.cli_archive."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from envchain.archiver import ARCHIVE_VERSION, serialise_archive, create_archive
from envchain.cli_archive import cmd_archive_save, cmd_archive_restore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name, parent=None, vars=None):
        self.name = name
        self.parent = parent
        self.vars = vars or {}


class _FakeRegistry:
    def __init__(self, chains=None):
        self._chains = {c.name: c for c in (chains or [])}

    def get(self, name):
        return self._chains.get(name)

    def add(self, name, parent=None, vars=None):
        self._chains[name] = _FakeChain(name, parent=parent, vars=vars or {})


def _make_registry():
    return _FakeRegistry([
        _FakeChain("base", vars={"KEY": "val"}),
        _FakeChain("dev", parent="base", vars={"DEBUG": "1"}),
    ])


def _make_save_args(tmp_path, chains, label=""):
    return types.SimpleNamespace(
        chains=chains,
        output=str(tmp_path / "archive.json"),
        label=label,
    )


def _make_restore_args(input_path, chains=None, overwrite=False):
    return types.SimpleNamespace(
        input=str(input_path),
        chains=chains or [],
        overwrite=overwrite,
    )


# ---------------------------------------------------------------------------
# cmd_archive_save
# ---------------------------------------------------------------------------

def test_save_returns_0_on_success(tmp_path):
    reg = _make_registry()
    args = _make_save_args(tmp_path, ["base"])
    assert cmd_archive_save(args, reg) == 0


def test_save_creates_file(tmp_path):
    reg = _make_registry()
    args = _make_save_args(tmp_path, ["base"])
    cmd_archive_save(args, reg)
    assert Path(args.output).exists()


def test_save_file_is_valid_json(tmp_path):
    reg = _make_registry()
    args = _make_save_args(tmp_path, ["base", "dev"])
    cmd_archive_save(args, reg)
    data = json.loads(Path(args.output).read_text())
    assert data["version"] == ARCHIVE_VERSION


def test_save_returns_1_for_unknown_chain(tmp_path):
    reg = _make_registry()
    args = _make_save_args(tmp_path, ["ghost"])
    assert cmd_archive_save(args, reg) == 1


def test_save_stores_label(tmp_path):
    reg = _make_registry()
    args = _make_save_args(tmp_path, ["base"], label="v2")
    cmd_archive_save(args, reg)
    data = json.loads(Path(args.output).read_text())
    assert data["label"] == "v2"


# ---------------------------------------------------------------------------
# cmd_archive_restore
# ---------------------------------------------------------------------------

def test_restore_returns_0_on_success(tmp_path):
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    archive_file = tmp_path / "archive.json"
    archive_file.write_text(serialise_archive(arch))

    empty_reg = _FakeRegistry()
    args = _make_restore_args(archive_file)
    assert cmd_archive_restore(args, empty_reg) == 0


def test_restore_creates_chain_in_registry(tmp_path):
    reg = _make_registry()
    arch = create_archive(reg, ["base", "dev"])
    archive_file = tmp_path / "archive.json"
    archive_file.write_text(serialise_archive(arch))

    empty_reg = _FakeRegistry()
    args = _make_restore_args(archive_file)
    cmd_archive_restore(args, empty_reg)
    assert empty_reg.get("base") is not None
    assert empty_reg.get("dev") is not None


def test_restore_returns_1_for_missing_file(tmp_path):
    args = _make_restore_args(tmp_path / "nonexistent.json")
    assert cmd_archive_restore(args, _FakeRegistry()) == 1


def test_restore_returns_1_when_chain_exists_no_overwrite(tmp_path):
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    archive_file = tmp_path / "archive.json"
    archive_file.write_text(serialise_archive(arch))

    args = _make_restore_args(archive_file)
    assert cmd_archive_restore(args, reg) == 1


def test_restore_overwrite_flag_returns_0(tmp_path):
    reg = _make_registry()
    arch = create_archive(reg, ["base"])
    archive_file = tmp_path / "archive.json"
    archive_file.write_text(serialise_archive(arch))

    args = _make_restore_args(archive_file, overwrite=True)
    assert cmd_archive_restore(args, reg) == 0


def test_restore_partial_selection(tmp_path):
    reg = _make_registry()
    arch = create_archive(reg, ["base", "dev"])
    archive_file = tmp_path / "archive.json"
    archive_file.write_text(serialise_archive(arch))

    empty_reg = _FakeRegistry()
    args = _make_restore_args(archive_file, chains=["base"])
    cmd_archive_restore(args, empty_reg)
    assert empty_reg.get("base") is not None
    assert empty_reg.get("dev") is None
