"""Integration-style roundtrip tests for CSV export/import."""
from __future__ import annotations

import pytest

from envchain.exporter_csv import export_csv, export_multi_csv, parse_csv


SAMPLE_VARS = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "SECRET_KEY": "s3cr3t!",
    "DEBUG": "true",
    "PORT": "8080",
}


def test_single_chain_roundtrip():
    csv_text = export_csv("dev", SAMPLE_VARS)
    parsed = parse_csv(csv_text)
    assert parsed["dev"] == SAMPLE_VARS


def test_multi_chain_roundtrip():
    chains = {
        "dev": {"FOO": "bar", "BAZ": "1"},
        "staging": {"FOO": "baz", "EXTRA": "yes"},
        "prod": {"FOO": "prod_val"},
    }
    csv_text = export_multi_csv(chains)
    parsed = parse_csv(csv_text)
    assert parsed == chains


def test_values_with_commas_roundtrip():
    vars_ = {"CSV_FIELD": "one,two,three"}
    csv_text = export_csv("dev", vars_)
    parsed = parse_csv(csv_text)
    assert parsed["dev"]["CSV_FIELD"] == "one,two,three"


def test_values_with_newlines_roundtrip():
    vars_ = {"MULTILINE": "line1\nline2"}
    csv_text = export_csv("dev", vars_)
    parsed = parse_csv(csv_text)
    assert parsed["dev"]["MULTILINE"] == "line1\nline2"


def test_values_with_quotes_roundtrip():
    vars_ = {"QUOTED": 'say "hello"'}
    csv_text = export_csv("dev", vars_)
    parsed = parse_csv(csv_text)
    assert parsed["dev"]["QUOTED"] == 'say "hello"'


def test_empty_vars_roundtrip():
    csv_text = export_csv("dev", {})
    parsed = parse_csv(csv_text)
    assert parsed == {}


def test_custom_delimiter_roundtrip():
    vars_ = {"KEY": "value"}
    csv_text = export_csv("dev", vars_, delimiter=";")
    parsed = parse_csv(csv_text, delimiter=";")
    assert parsed["dev"] == vars_


def test_no_header_roundtrip():
    vars_ = {"A": "1"}
    csv_text = export_csv("dev", vars_, include_header=False)
    # Without header the first row IS data; parse_csv will treat it as data
    # because it won't match the literal header pattern.
    parsed = parse_csv(csv_text)
    assert parsed["dev"] == vars_


def test_special_characters_in_chain_name_roundtrip():
    """Chain names containing spaces or hyphens should survive a roundtrip."""
    vars_ = {"KEY": "value"}
    for chain_name in ("my-chain", "my chain", "chain_1"):
        csv_text = export_csv(chain_name, vars_)
        parsed = parse_csv(csv_text)
        assert chain_name in parsed, f"Chain '{chain_name}' missing from parsed output"
        assert parsed[chain_name] == vars_
