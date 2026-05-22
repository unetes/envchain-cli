"""Tests for envchain.cli_compare."""

import argparse
import json
import pytest
from envchain.chain import Chain
from envchain.registry import ChainRegistry
from envchain.cli_compare import cmd_compare, build_compare_parser


def _make_args(**kwargs):
    defaults = {"left": "a", "right": "b", "no_resolve": False, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_registry(*chains):
    reg = ChainRegistry()
    for c in chains:
        reg.add(c)
    return reg


def test_cmd_compare_returns_0_when_identical(capsys):
    a = Chain(name="a", vars={"X": "1"})
    b = Chain(name="b", vars={"X": "1"})
    reg = _make_registry(a, b)
    rc = cmd_compare(_make_args(left="a", right="b"), reg)
    assert rc == 0


def test_cmd_compare_returns_1_when_different(capsys):
    a = Chain(name="a", vars={"X": "1"})
    b = Chain(name="b", vars={"X": "2"})
    reg = _make_registry(a, b)
    rc = cmd_compare(_make_args(left="a", right="b"), reg)
    assert rc == 1


def test_cmd_compare_text_output_contains_chain_names(capsys):
    a = Chain(name="alpha", vars={"K": "v"})
    b = Chain(name="beta", vars={"K": "v"})
    reg = _make_registry(a, b)
    cmd_compare(_make_args(left="alpha", right="beta"), reg)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_cmd_compare_text_output_contains_summary(capsys):
    a = Chain(name="a", vars={"X": "1"})
    b = Chain(name="b", vars={"X": "2"})
    reg = _make_registry(a, b)
    cmd_compare(_make_args(left="a", right="b"), reg)
    out = capsys.readouterr().out
    assert "Summary" in out


def test_cmd_compare_json_format_is_valid_json(capsys):
    a = Chain(name="a", vars={"X": "1"})
    b = Chain(name="b", vars={"X": "2"})
    reg = _make_registry(a, b)
    cmd_compare(_make_args(left="a", right="b", format="json"), reg)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["left_chain"] == "a"
    assert data["right_chain"] == "b"
    assert "rows" in data
    assert "summary" in data


def test_cmd_compare_json_has_differences_flag(capsys):
    a = Chain(name="a", vars={"X": "1"})
    b = Chain(name="b", vars={"X": "99"})
    reg = _make_registry(a, b)
    cmd_compare(_make_args(left="a", right="b", format="json"), reg)
    data = json.loads(capsys.readouterr().out)
    assert data["has_differences"] is True


def test_cmd_compare_missing_chain_returns_1(capsys):
    a = Chain(name="a", vars={})
    reg = _make_registry(a)
    rc = cmd_compare(_make_args(left="a", right="ghost"), reg)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Error" in out


def test_build_compare_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_compare_parser(sub)
    args = parser.parse_args(["compare", "chainA", "chainB"])
    assert args.left == "chainA"
    assert args.right == "chainB"
    assert args.no_resolve is False
    assert args.format == "text"
