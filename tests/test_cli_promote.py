"""Tests for envchain.cli_promote."""

from __future__ import annotations

import argparse
import io

import pytest

from envchain.cli_promote import cmd_promote, build_promote_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name: str, vars_: dict):
        self.name = name
        self.vars = dict(vars_)


class _FakeRegistry:
    def __init__(self):
        self._chains: dict[str, _FakeChain] = {}

    def add(self, chain: _FakeChain):
        self._chains[chain.name] = chain

    def get(self, name: str):
        return self._chains.get(name)

    def update_vars(self, name: str, vars_: dict):
        self._chains[name].vars = dict(vars_)


def _make_registry():
    reg = _FakeRegistry()
    reg.add(_FakeChain("base", {"HOST": "localhost"}))
    reg.add(_FakeChain("dev", {"DEBUG": "true", "HOST": "dev.local"}))
    return reg


def _make_args(**kwargs):
    defaults = {
        "source": "dev",
        "target": "base",
        "keys": ["DEBUG"],
        "overwrite": False,
        "move": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cmd_promote_returns_0_on_success():
    reg = _make_registry()
    rc = cmd_promote(_make_args(), reg, out=io.StringIO(), err=io.StringIO())
    assert rc == 0


def test_cmd_promote_output_mentions_key():
    reg = _make_registry()
    out = io.StringIO()
    cmd_promote(_make_args(), reg, out=out, err=io.StringIO())
    assert "DEBUG" in out.getvalue()


def test_cmd_promote_output_mentions_chains():
    reg = _make_registry()
    out = io.StringIO()
    cmd_promote(_make_args(), reg, out=out, err=io.StringIO())
    assert "dev" in out.getvalue()
    assert "base" in out.getvalue()


def test_cmd_promote_returns_1_on_missing_source():
    reg = _make_registry()
    args = _make_args(source="ghost")
    err = io.StringIO()
    rc = cmd_promote(args, reg, out=io.StringIO(), err=err)
    assert rc == 1
    assert "Error" in err.getvalue()


def test_cmd_promote_returns_2_on_empty_keys():
    reg = _make_registry()
    args = _make_args(keys=[])
    err = io.StringIO()
    rc = cmd_promote(args, reg, out=io.StringIO(), err=err)
    assert rc == 2


def test_cmd_promote_move_flag_removes_from_source():
    reg = _make_registry()
    args = _make_args(move=True)
    cmd_promote(args, reg, out=io.StringIO(), err=io.StringIO())
    assert "DEBUG" not in reg.get("dev").vars


def test_cmd_promote_output_says_moved_when_move_flag():
    reg = _make_registry()
    out = io.StringIO()
    cmd_promote(_make_args(move=True), reg, out=out, err=io.StringIO())
    assert "Moved" in out.getvalue()


def test_build_promote_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_promote_parser(subs)
    args = root.parse_args(["promote", "dev", "base", "DEBUG"])
    assert args.source == "dev"
    assert args.target == "base"
    assert args.keys == ["DEBUG"]
