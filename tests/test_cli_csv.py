"""Tests for envchain.cli_csv."""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path

import pytest

from envchain.cli_csv import cmd_csv_export, cmd_csv_import


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name: str, vars: dict):
        self.name = name
        self.vars = dict(vars)


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)

    def all_names(self):
        return list(self._chains)


def _make_args(**kwargs):
    ns = argparse.Namespace(
        chains=[],
        output=None,
        file=None,
        chain=None,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _make_registry():
    return _FakeRegistry([
        _FakeChain("dev", {"FOO": "bar", "BAZ": "qux"}),
        _FakeChain("prod", {"FOO": "baz"}),
    ])


# ---------------------------------------------------------------------------
# cmd_csv_export
# ---------------------------------------------------------------------------

def test_export_returns_0_on_success():
    reg = _make_registry()
    out = io.StringIO()
    rc = cmd_csv_export(_make_args(chains=["dev"]), reg, out=out)
    assert rc == 0


def test_export_output_contains_header():
    reg = _make_registry()
    out = io.StringIO()
    cmd_csv_export(_make_args(chains=["dev"]), reg, out=out)
    assert "chain,key,value" in out.getvalue()


def test_export_output_contains_vars():
    reg = _make_registry()
    out = io.StringIO()
    cmd_csv_export(_make_args(chains=["dev"]), reg, out=out)
    assert "FOO" in out.getvalue()
    assert "bar" in out.getvalue()


def test_export_unknown_chain_returns_1():
    reg = _make_registry()
    err = io.StringIO()
    rc = cmd_csv_export(_make_args(chains=["ghost"]), reg, err=err)
    assert rc == 1
    assert "ghost" in err.getvalue()


def test_export_to_file(tmp_path):
    reg = _make_registry()
    dest = str(tmp_path / "out.csv")
    out = io.StringIO()
    rc = cmd_csv_export(_make_args(chains=["dev"], output=dest), reg, out=out)
    assert rc == 0
    assert Path(dest).exists()
    assert "FOO" in Path(dest).read_text()


def test_export_all_chains_when_no_names_given():
    reg = _make_registry()
    out = io.StringIO()
    cmd_csv_export(_make_args(chains=[]), reg, out=out)
    text = out.getvalue()
    assert "dev" in text
    assert "prod" in text


# ---------------------------------------------------------------------------
# cmd_csv_import
# ---------------------------------------------------------------------------

def test_import_returns_0_on_success(tmp_path):
    csv_file = tmp_path / "vars.csv"
    csv_file.write_text("chain,key,value\ndev,NEW_KEY,hello\n")
    reg = _make_registry()
    out = io.StringIO()
    rc = cmd_csv_import(_make_args(file=str(csv_file)), reg, out=out)
    assert rc == 0


def test_import_updates_chain_vars(tmp_path):
    csv_file = tmp_path / "vars.csv"
    csv_file.write_text("chain,key,value\ndev,NEW_KEY,hello\n")
    reg = _make_registry()
    cmd_csv_import(_make_args(file=str(csv_file)), reg)
    assert reg.get("dev").vars["NEW_KEY"] == "hello"


def test_import_missing_file_returns_1():
    reg = _make_registry()
    err = io.StringIO()
    rc = cmd_csv_import(_make_args(file="/no/such/file.csv"), reg, err=err)
    assert rc == 1
    assert "Cannot read" in err.getvalue()


def test_import_bad_csv_returns_1(tmp_path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("chain,key\ndev,A\n")  # only 2 columns
    reg = _make_registry()
    err = io.StringIO()
    rc = cmd_csv_import(_make_args(file=str(csv_file)), reg, err=err)
    assert rc == 1
    assert "CSV error" in err.getvalue()


def test_import_unknown_chain_skips_with_warning(tmp_path):
    csv_file = tmp_path / "vars.csv"
    csv_file.write_text("chain,key,value\nghost,K,v\n")
    reg = _make_registry()
    err = io.StringIO()
    rc = cmd_csv_import(_make_args(file=str(csv_file)), reg, err=err)
    assert rc == 0  # skips, does not hard-fail
    assert "ghost" in err.getvalue()
