"""Tests for envchain.exporter."""

import json

import pytest

from envchain.exporter import export_vars


SAMPLE = {"APP_ENV": "production", "DB_HOST": "localhost", "SECRET": 'p@ss"word'}


def test_json_format_is_valid_json():
    output = export_vars(SAMPLE, "json")
    parsed = json.loads(output)
    assert parsed == SAMPLE


def test_shell_format_contains_export():
    output = export_vars(SAMPLE, "shell")
    assert "export APP_ENV=production" in output
    assert "export DB_HOST=localhost" in output


def test_shell_format_quotes_special_chars():
    output = export_vars({"KEY": "hello world"}, "shell")
    assert "export KEY='hello world'" in output


def test_shell_format_includes_chain_name_comment():
    output = export_vars(SAMPLE, "shell", chain_name="mychain")
    assert output.startswith("# envchain: mychain")


def test_dotenv_format_wraps_values_in_quotes():
    output = export_vars({"FOO": "bar"}, "dotenv")
    assert 'FOO="bar"' in output


def test_dotenv_format_escapes_double_quotes():
    output = export_vars({"SECRET": 'p@ss"word'}, "dotenv")
    assert 'SECRET="p@ss\\"word"' in output


def test_dotenv_includes_chain_name_comment():
    output = export_vars({"X": "1"}, "dotenv", chain_name="base")
    assert "# envchain: base" in output


def test_env_format_is_dotenv_without_header():
    output = export_vars({"A": "1"}, "env")
    assert not output.startswith("#")
    assert 'A="1"' in output


def test_keys_are_sorted():
    data = {"ZZZ": "last", "AAA": "first", "MMM": "mid"}
    output = export_vars(data, "dotenv")
    keys = [line.split("=")[0] for line in output.splitlines() if "=" in line]
    assert keys == sorted(keys)
