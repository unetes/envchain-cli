"""Tests for envchain.importer."""

import json
from pathlib import Path

import pytest

from envchain.importer import load_vars, parse_dotenv_string


# ---------------------------------------------------------------------------
# parse_dotenv_string
# ---------------------------------------------------------------------------

def test_parse_simple_key_value():
    result = parse_dotenv_string("FOO=bar")
    assert result == {"FOO": "bar"}


def test_parse_strips_double_quotes():
    result = parse_dotenv_string('KEY="hello world"')
    assert result["KEY"] == "hello world"


def test_parse_strips_single_quotes():
    result = parse_dotenv_string("KEY='hello world'")
    assert result["KEY"] == "hello world"


def test_parse_ignores_comments():
    text = "# this is a comment\nFOO=bar"
    result = parse_dotenv_string(text)
    assert "#" not in "".join(result.keys())
    assert result["FOO"] == "bar"


def test_parse_ignores_blank_lines():
    result = parse_dotenv_string("\n\nFOO=1\n\nBAR=2\n")
    assert result == {"FOO": "1", "BAR": "2"}


def test_parse_raises_on_malformed_line():
    with pytest.raises(ValueError, match="Malformed"):
        parse_dotenv_string("THIS IS NOT VALID")


# ---------------------------------------------------------------------------
# load_vars — dotenv file
# ---------------------------------------------------------------------------

def test_load_dotenv_file(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text('APP=prod\nDEBUG="false"\n')
    result = load_vars(f, fmt="dotenv")
    assert result == {"APP": "prod", "DEBUG": "false"}


def test_load_json_file(tmp_path: Path):
    f = tmp_path / "vars.json"
    f.write_text(json.dumps({"HOST": "localhost", "PORT": "5432"}))
    result = load_vars(f, fmt="json")
    assert result == {"HOST": "localhost", "PORT": "5432"}


def test_load_auto_detects_json_by_extension(tmp_path: Path):
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"X": "1"}))
    result = load_vars(f)  # fmt="auto"
    assert result == {"X": "1"}


def test_load_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_vars("/nonexistent/.env")


def test_load_raises_on_invalid_json(tmp_path: Path):
    f = tmp_path / "bad.json"
    f.write_text("not json at all")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_vars(f, fmt="json")
