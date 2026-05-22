"""Tests for envchain.merger module."""

import pytest

from envchain.merger import MergeConflictError, merge_vars, merge_chains


# ---------------------------------------------------------------------------
# merge_vars tests
# ---------------------------------------------------------------------------

def test_merge_vars_last_wins_default():
    result = merge_vars([{"A": "1"}, {"A": "2"}])
    assert result["A"] == "2"


def test_merge_vars_first_wins():
    result = merge_vars([{"A": "1"}, {"A": "2"}], strategy="first_wins")
    assert result["A"] == "1"


def test_merge_vars_raise_on_conflict():
    with pytest.raises(MergeConflictError) as exc_info:
        merge_vars([{"A": "1"}, {"A": "2"}], strategy="raise_on_conflict")
    assert exc_info.value.key == "A"


def test_merge_vars_no_conflict_combines_all_keys():
    result = merge_vars([{"A": "1"}, {"B": "2"}, {"C": "3"}])
    assert result == {"A": "1", "B": "2", "C": "3"}


def test_merge_vars_empty_sources():
    assert merge_vars([]) == {}


def test_merge_vars_single_source():
    result = merge_vars([{"X": "hello"}])
    assert result == {"X": "hello"}


def test_merge_vars_labels_length_mismatch_raises():
    with pytest.raises(ValueError):
        merge_vars([{"A": "1"}], labels=["src1", "src2"])


def test_merge_conflict_error_contains_sources():
    labels = ["base", "override"]
    with pytest.raises(MergeConflictError) as exc_info:
        merge_vars([{"KEY": "v1"}, {"KEY": "v2"}], labels=labels, strategy="raise_on_conflict")
    assert "base" in exc_info.value.sources
    assert "override" in exc_info.value.sources


def test_merge_vars_last_wins_with_three_sources():
    result = merge_vars([{"A": "1"}, {"A": "2"}, {"A": "3"}], strategy="last_wins")
    assert result["A"] == "3"


def test_merge_vars_first_wins_with_three_sources():
    result = merge_vars([{"A": "1"}, {"A": "2"}, {"A": "3"}], strategy="first_wins")
    assert result["A"] == "1"


# ---------------------------------------------------------------------------
# merge_chains tests
# ---------------------------------------------------------------------------

def _make_registry():
    from envchain.registry import ChainRegistry
    reg = ChainRegistry()
    reg.add("base", vars={"HOST": "localhost", "PORT": "5432"})
    reg.add("prod", vars={"HOST": "prod.example.com", "DEBUG": "false"})
    reg.add("dev", vars={"DEBUG": "true", "PORT": "5433"})
    return reg


def test_merge_chains_last_wins():
    reg = _make_registry()
    result = merge_chains(reg, ["base", "prod"])
    assert result["HOST"] == "prod.example.com"
    assert result["PORT"] == "5432"
    assert result["DEBUG"] == "false"


def test_merge_chains_first_wins():
    reg = _make_registry()
    result = merge_chains(reg, ["base", "prod"], strategy="first_wins")
    assert result["HOST"] == "localhost"


def test_merge_chains_raise_on_conflict():
    reg = _make_registry()
    with pytest.raises(MergeConflictError):
        merge_chains(reg, ["base", "prod"], strategy="raise_on_conflict")


def test_merge_chains_no_overlap():
    reg = _make_registry()
    result = merge_chains(reg, ["base", "dev"])
    # PORT conflicts -> last_wins gives dev's value
    assert result["PORT"] == "5433"
    assert result["HOST"] == "localhost"
    assert result["DEBUG"] == "true"
