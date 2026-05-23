"""Tests for envchain.cli_score."""
from __future__ import annotations

import argparse
import json

import pytest

from envchain.cli_score import cmd_score, build_score_parser


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name, vars_=None, parent=None):
        self.name = name
        self.vars = vars_ or {}
        self.parent = parent


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)

    def all_names(self):
        return list(self._chains)


def _make_args(**kwargs):
    defaults = dict(chains=[], format="text", fail_below=None)
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    return ns


def _make_registry():
    return _FakeRegistry([
        _FakeChain("base", {"DB_HOST": "localhost", "DB_PORT": "5432",
                            "APP_ENV": "dev", "LOG_LEVEL": "info",
                            "SECRET_KEY": "abc"}),
        _FakeChain("child", {"EXTRA": "1"}, parent="base"),
    ])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cmd_score_returns_0_on_success():
    reg = _make_registry()
    args = _make_args(chains=["base"])
    assert cmd_score(args, reg) == 0


def test_cmd_score_all_chains_when_no_names_given():
    reg = _make_registry()
    args = _make_args(chains=[])
    assert cmd_score(args, reg) == 0


def test_cmd_score_returns_2_for_unknown_chain():
    reg = _make_registry()
    args = _make_args(chains=["nonexistent"])
    assert cmd_score(args, reg) == 2


def test_cmd_score_returns_1_for_empty_registry():
    reg = _FakeRegistry([])
    args = _make_args(chains=[])
    assert cmd_score(args, reg) == 1


def test_cmd_score_json_format_is_valid(capsys):
    reg = _make_registry()
    args = _make_args(chains=["base"], format="json")
    cmd_score(args, reg)
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert parsed[0]["chain"] == "base"


def test_cmd_score_json_has_score_and_grade(capsys):
    reg = _make_registry()
    args = _make_args(chains=["base"], format="json")
    cmd_score(args, reg)
    out = capsys.readouterr().out
    row = json.loads(out)[0]
    assert "score" in row
    assert "grade" in row


def test_cmd_score_text_output_contains_chain_name(capsys):
    reg = _make_registry()
    args = _make_args(chains=["base"])
    cmd_score(args, reg)
    out = capsys.readouterr().out
    assert "base" in out


def test_cmd_score_fail_below_returns_3_when_triggered():
    reg = _FakeRegistry([_FakeChain("empty")])
    args = _make_args(chains=["empty"], fail_below=99)
    result = cmd_score(args, reg)
    assert result == 3


def test_cmd_score_fail_below_returns_0_when_not_triggered():
    reg = _make_registry()
    args = _make_args(chains=["base"], fail_below=0)
    assert cmd_score(args, reg) == 0


def test_build_score_parser_registers_subcommand():
    main = argparse.ArgumentParser()
    sub = main.add_subparsers()
    build_score_parser(sub)
    parsed = main.parse_args(["score", "mychain", "--format", "json"])
    assert parsed.chains == ["mychain"]
    assert parsed.format == "json"
