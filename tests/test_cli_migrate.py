"""Tests for envchain.cli_migrate."""

import argparse
import pytest
from envchain.cli_migrate import cmd_migrate, build_migrate_parser


class _FakeChain:
    def __init__(self, name, vars_):
        self.name = name
        self.vars = dict(vars_)


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)


def _make_registry():
    src = _FakeChain("src", {"FOO": "bar", "BAZ": "qux"})
    dst = _FakeChain("dst", {})
    return _FakeRegistry([src, dst])


def _make_args(**kwargs):
    defaults = dict(
        source="src",
        dest="dst",
        keys=[],
        remap=None,
        overwrite=False,
        move=False,
        format="text",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_migrate_returns_0_on_success():
    reg = _make_registry()
    args = _make_args()
    assert cmd_migrate(args, reg) == 0


def test_cmd_migrate_keys_present_in_dest():
    reg = _make_registry()
    args = _make_args()
    cmd_migrate(args, reg)
    assert reg.get("dst").vars.get("FOO") == "bar"


def test_cmd_migrate_text_output(capsys):
    reg = _make_registry()
    args = _make_args()
    cmd_migrate(args, reg)
    out = capsys.readouterr().out
    assert "src" in out
    assert "dst" in out


def test_cmd_migrate_json_output(capsys):
    import json
    reg = _make_registry()
    args = _make_args(format="json")
    cmd_migrate(args, reg)
    data = json.loads(capsys.readouterr().out)
    assert "moved" in data
    assert "skipped" in data


def test_cmd_migrate_returns_1_on_missing_source():
    reg = _make_registry()
    args = _make_args(source="ghost")
    assert cmd_migrate(args, reg) == 1


def test_cmd_migrate_returns_1_on_bad_remap():
    reg = _make_registry()
    args = _make_args(remap=["INVALID_NO_COLON"])
    assert cmd_migrate(args, reg) == 1


def test_cmd_migrate_move_removes_from_source():
    reg = _make_registry()
    args = _make_args(keys=["FOO"], move=True)
    cmd_migrate(args, reg)
    assert "FOO" not in reg.get("src").vars


def test_cmd_migrate_remap_applies_new_key():
    reg = _make_registry()
    args = _make_args(keys=["FOO"], remap=["FOO:RENAMED"])
    cmd_migrate(args, reg)
    assert "RENAMED" in reg.get("dst").vars
    assert "FOO" not in reg.get("dst").vars


def test_build_migrate_parser_returns_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = build_migrate_parser(sub)
    assert p is not None
