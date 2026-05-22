"""Tests for envchain.cli_copy."""

import argparse
import json

import pytest

from envchain.cli_copy import cmd_copy_chain
from envchain.registry import ChainRegistry


def _make_args(**kwargs):
    defaults = {
        "src": "base",
        "dst": "base_copy",
        "include": None,
        "exclude": None,
        "no_parent": False,
        "overwrite": False,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_registry():
    reg = ChainRegistry()
    reg.add("base", vars={"HOST": "localhost", "PORT": "5432"})
    reg.add("child", vars={"DEBUG": "true"}, parent="base")
    return reg


def test_cmd_copy_returns_0_on_success():
    reg = _make_registry()
    assert cmd_copy_chain(_make_args(), reg) == 0


def test_cmd_copy_creates_chain_in_registry():
    reg = _make_registry()
    cmd_copy_chain(_make_args(), reg)
    assert reg.get("base_copy") is not None


def test_cmd_copy_text_output(capsys):
    reg = _make_registry()
    cmd_copy_chain(_make_args(), reg)
    out = capsys.readouterr().out
    assert "base" in out
    assert "base_copy" in out


def test_cmd_copy_json_output(capsys):
    reg = _make_registry()
    cmd_copy_chain(_make_args(format="json"), reg)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "vars" in data


def test_cmd_copy_returns_1_on_missing_src(capsys):
    reg = _make_registry()
    rc = cmd_copy_chain(_make_args(src="ghost"), reg)
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_cmd_copy_returns_1_on_existing_dst_no_overwrite(capsys):
    reg = _make_registry()
    rc = cmd_copy_chain(_make_args(dst="child"), reg)
    assert rc == 1


def test_cmd_copy_overwrite_flag_succeeds():
    reg = _make_registry()
    rc = cmd_copy_chain(_make_args(dst="child", overwrite=True), reg)
    assert rc == 0


def test_cmd_copy_no_parent_flag():
    reg = _make_registry()
    cmd_copy_chain(_make_args(src="child", dst="child_copy", no_parent=True), reg)
    assert reg.get("child_copy").get("parent") is None


def test_cmd_copy_include_keys():
    reg = _make_registry()
    cmd_copy_chain(_make_args(include=["HOST"]), reg)
    assert list(reg.get("base_copy")["vars"].keys()) == ["HOST"]


def test_cmd_copy_exclude_keys():
    reg = _make_registry()
    cmd_copy_chain(_make_args(exclude=["PORT"]), reg)
    assert "PORT" not in reg.get("base_copy")["vars"]
