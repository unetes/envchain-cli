"""Tests for envchain.differ module."""

import pytest
from envchain.differ import diff_vars, format_diff, ChainDiff, DiffEntry


OLD = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
NEW = {"HOST": "prod.db", "PORT": "5432", "TIMEOUT": "30"}


def test_diff_detects_added_keys():
    result = diff_vars("mychain", OLD, NEW)
    keys = [e.key for e in result.added]
    assert "TIMEOUT" in keys


def test_diff_detects_removed_keys():
    result = diff_vars("mychain", OLD, NEW)
    keys = [e.key for e in result.removed]
    assert "DEBUG" in keys


def test_diff_detects_modified_keys():
    result = diff_vars("mychain", OLD, NEW)
    keys = [e.key for e in result.modified]
    assert "HOST" in keys


def test_diff_unchanged_key_not_in_changes_by_default():
    result = diff_vars("mychain", OLD, NEW)
    all_changed_keys = (
        [e.key for e in result.added]
        + [e.key for e in result.removed]
        + [e.key for e in result.modified]
    )
    assert "PORT" not in all_changed_keys
    assert result.unchanged == []


def test_diff_include_unchanged():
    result = diff_vars("mychain", OLD, NEW, include_unchanged=True)
    keys = [e.key for e in result.unchanged]
    assert "PORT" in keys


def test_diff_modified_entry_has_old_and_new_values():
    result = diff_vars("mychain", OLD, NEW)
    host_entry = next(e for e in result.modified if e.key == "HOST")
    assert host_entry.old_value == "localhost"
    assert host_entry.new_value == "prod.db"


def test_diff_added_entry_has_no_old_value():
    result = diff_vars("mychain", OLD, NEW)
    timeout_entry = next(e for e in result.added if e.key == "TIMEOUT")
    assert timeout_entry.old_value is None
    assert timeout_entry.new_value == "30"


def test_diff_removed_entry_has_no_new_value():
    result = diff_vars("mychain", OLD, NEW)
    debug_entry = next(e for e in result.removed if e.key == "DEBUG")
    assert debug_entry.old_value == "true"
    assert debug_entry.new_value is None


def test_has_changes_true_when_differences_exist():
    result = diff_vars("mychain", OLD, NEW)
    assert result.has_changes is True


def test_has_changes_false_when_identical():
    result = diff_vars("mychain", OLD, OLD)
    assert result.has_changes is False


def test_summary_no_changes():
    result = diff_vars("mychain", OLD, OLD)
    assert result.summary == "no changes"


def test_summary_with_changes():
    result = diff_vars("mychain", OLD, NEW)
    assert "+" in result.summary or "-" in result.summary or "~" in result.summary


def test_format_diff_contains_chain_name():
    result = diff_vars("mychain", OLD, NEW)
    output = format_diff(result)
    assert "mychain" in output


def test_format_diff_shows_plus_for_added():
    result = diff_vars("mychain", {}, {"FOO": "bar"})
    output = format_diff(result)
    assert "+ FOO" in output


def test_format_diff_shows_minus_for_removed():
    result = diff_vars("mychain", {"FOO": "bar"}, {})
    output = format_diff(result)
    assert "- FOO" in output


def test_format_diff_hides_values_when_disabled():
    result = diff_vars("mychain", OLD, NEW)
    output = format_diff(result, show_values=False)
    assert "localhost" not in output
    assert "prod.db" not in output
