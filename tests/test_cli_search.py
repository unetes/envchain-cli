"""Tests for envchain.cli_search module."""

import argparse
import pytest
from envchain.registry import ChainRegistry
from envchain.cli_search import cmd_search, build_search_parser


def _make_args(**kwargs):
    defaults = {
        "query": "DB",
        "chain": None,
        "search_values": False,
        "case_sensitive": False,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_registry():
    reg = ChainRegistry()
    reg.add("base", vars={"DB_HOST": "localhost", "DB_PORT": "5432"})
    reg.add("prod", parent="base", vars={"SECRET": "s3cr3t"})
    return reg


def test_cmd_search_returns_0_when_found(capsys):
    reg = _make_registry()
    code = cmd_search(_make_args(query="DB"), reg)
    assert code == 0


def test_cmd_search_returns_1_when_not_found(capsys):
    reg = _make_registry()
    code = cmd_search(_make_args(query="NONEXISTENT_XYZ"), reg)
    assert code == 1


def test_cmd_search_returns_2_on_empty_query(capsys):
    reg = _make_registry()
    code = cmd_search(_make_args(query=""), reg)
    assert code == 2


def test_cmd_search_text_output_contains_key(capsys):
    reg = _make_registry()
    cmd_search(_make_args(query="DB_HOST"), reg)
    out = capsys.readouterr().out
    assert "DB_HOST" in out


def test_cmd_search_text_output_contains_chain_name(capsys):
    reg = _make_registry()
    cmd_search(_make_args(query="DB_HOST"), reg)
    out = capsys.readouterr().out
    assert "base" in out


def test_cmd_search_json_format_is_valid_json(capsys):
    import json
    reg = _make_registry()
    cmd_search(_make_args(query="DB", format="json"), reg)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert all("chain" in item and "key" in item for item in data)


def test_cmd_search_chain_filter_applied(capsys):
    reg = _make_registry()
    cmd_search(_make_args(query="DB", chain="base"), reg)
    out = capsys.readouterr().out
    assert "base" in out
    assert "prod" not in out


def test_cmd_search_values_flag(capsys):
    reg = _make_registry()
    code = cmd_search(_make_args(query="localhost", search_values=True), reg)
    assert code == 0
    out = capsys.readouterr().out
    assert "[value]" in out


def test_build_search_parser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    build_search_parser(subs)
    args = parser.parse_args(["search", "MY_KEY"])
    assert args.query == "MY_KEY"
    assert args.search_values is False
    assert args.case_sensitive is False
    assert args.format == "text"
