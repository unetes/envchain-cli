"""Tests for envchain.exporter_csv."""
from __future__ import annotations

import pytest

from envchain.exporter_csv import (
    CsvError,
    export_csv,
    export_multi_csv,
    parse_csv,
)


# ---------------------------------------------------------------------------
# export_csv
# ---------------------------------------------------------------------------

def test_export_csv_contains_header():
    out = export_csv("dev", {"FOO": "bar"})
    assert out.startswith("chain,key,value")


def test_export_csv_no_header():
    out = export_csv("dev", {"FOO": "bar"}, include_header=False)
    assert "chain" not in out.split("\n")[0]


def test_export_csv_row_contains_chain_name():
    out = export_csv("staging", {"X": "1"})
    assert "staging" in out


def test_export_csv_row_contains_key_and_value():
    out = export_csv("dev", {"DB_URL": "postgres://localhost"})
    assert "DB_URL" in out
    assert "postgres://localhost" in out


def test_export_csv_rows_are_sorted_by_key():
    out = export_csv("dev", {"Z_KEY": "z", "A_KEY": "a"})
    lines = [l for l in out.strip().splitlines() if l and not l.startswith("chain")]
    keys = [l.split(",")[1] for l in lines]
    assert keys == sorted(keys)


def test_export_csv_custom_delimiter():
    out = export_csv("dev", {"K": "v"}, delimiter=";")
    assert ";" in out
    assert "," not in out


# ---------------------------------------------------------------------------
# parse_csv
# ---------------------------------------------------------------------------

def test_parse_csv_returns_chain_dict():
    text = "chain,key,value\ndev,FOO,bar\n"
    result = parse_csv(text)
    assert result == {"dev": {"FOO": "bar"}}


def test_parse_csv_multiple_rows_same_chain():
    text = "chain,key,value\ndev,A,1\ndev,B,2\n"
    result = parse_csv(text)
    assert result["dev"] == {"A": "1", "B": "2"}


def test_parse_csv_multiple_chains():
    text = "chain,key,value\ndev,A,1\nprod,B,2\n"
    result = parse_csv(text)
    assert "dev" in result
    assert "prod" in result


def test_parse_csv_expected_chain_mismatch_raises():
    text = "chain,key,value\nprod,A,1\n"
    with pytest.raises(CsvError, match="expected"):
        parse_csv(text, expected_chain="dev")


def test_parse_csv_bad_column_count_raises():
    text = "chain,key\ndev,A\n"
    with pytest.raises(CsvError, match="3 columns"):
        parse_csv(text)


def test_parse_csv_skips_blank_lines():
    text = "chain,key,value\n\ndev,FOO,bar\n\n"
    result = parse_csv(text)
    assert result == {"dev": {"FOO": "bar"}}


# ---------------------------------------------------------------------------
# export_multi_csv
# ---------------------------------------------------------------------------

def test_export_multi_csv_includes_all_chains():
    chains = {"dev": {"A": "1"}, "prod": {"B": "2"}}
    out = export_multi_csv(chains)
    assert "dev" in out
    assert "prod" in out


def test_export_multi_csv_roundtrip():
    chains = {"dev": {"FOO": "bar", "BAZ": "qux"}, "prod": {"FOO": "baz"}}
    out = export_multi_csv(chains)
    parsed = parse_csv(out)
    assert parsed == chains
