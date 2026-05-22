"""Tests for envchain.comparator."""

import pytest
from envchain.chain import Chain
from envchain.registry import ChainRegistry
from envchain.comparator import compare_chains, CompareRow, CompareResult


def _make_registry(*chains):
    reg = ChainRegistry()
    for c in chains:
        reg.add(c)
    return reg


def test_compare_same_chains_no_differences():
    c = Chain(name="a", vars={"X": "1", "Y": "2"})
    reg = _make_registry(c)
    result = compare_chains(reg, "a", "a")
    assert not result.has_differences


def test_compare_detects_different_value():
    a = Chain(name="a", vars={"X": "1"})
    b = Chain(name="b", vars={"X": "2"})
    reg = _make_registry(a, b)
    result = compare_chains(reg, "a", "b")
    assert result.has_differences
    row = result.rows[0]
    assert row.status == "different"
    assert row.left_value == "1"
    assert row.right_value == "2"


def test_compare_detects_left_only_key():
    a = Chain(name="a", vars={"X": "1", "Y": "2"})
    b = Chain(name="b", vars={"X": "1"})
    reg = _make_registry(a, b)
    result = compare_chains(reg, "a", "b")
    row = next(r for r in result.rows if r.key == "Y")
    assert row.status == "left_only"
    assert row.right_value is None


def test_compare_detects_right_only_key():
    a = Chain(name="a", vars={"X": "1"})
    b = Chain(name="b", vars={"X": "1", "Z": "3"})
    reg = _make_registry(a, b)
    result = compare_chains(reg, "a", "b")
    row = next(r for r in result.rows if r.key == "Z")
    assert row.status == "right_only"
    assert row.left_value is None


def test_compare_keys_are_sorted():
    a = Chain(name="a", vars={"Z": "1", "A": "2", "M": "3"})
    b = Chain(name="b", vars={"Z": "1", "A": "2", "M": "3"})
    reg = _make_registry(a, b)
    result = compare_chains(reg, "a", "b")
    keys = [r.key for r in result.rows]
    assert keys == sorted(keys)


def test_compare_resolved_inherits_parent_vars():
    parent = Chain(name="base", vars={"SHARED": "base_val"})
    child = Chain(name="child", parent="base", vars={"OWN": "child_val"})
    other = Chain(name="other", vars={"SHARED": "base_val", "OWN": "child_val"})
    reg = _make_registry(parent, child, other)
    result = compare_chains(reg, "child", "other", resolved=True)
    assert not result.has_differences


def test_compare_unresolved_ignores_parent_vars():
    parent = Chain(name="base", vars={"SHARED": "base_val"})
    child = Chain(name="child", parent="base", vars={"OWN": "child_val"})
    other = Chain(name="other", vars={"SHARED": "base_val", "OWN": "child_val"})
    reg = _make_registry(parent, child, other)
    result = compare_chains(reg, "child", "other", resolved=False)
    assert result.has_differences


def test_compare_summary_counts():
    a = Chain(name="a", vars={"X": "1", "Y": "2", "Z": "3"})
    b = Chain(name="b", vars={"X": "1", "Y": "99", "W": "4"})
    reg = _make_registry(a, b)
    result = compare_chains(reg, "a", "b")
    summary = result.summary()
    assert summary["same"] == 1       # X
    assert summary["different"] == 1  # Y
    assert summary["left_only"] == 1  # Z
    assert summary["right_only"] == 1 # W


def test_compare_result_stores_chain_names():
    a = Chain(name="alpha", vars={})
    b = Chain(name="beta", vars={})
    reg = _make_registry(a, b)
    result = compare_chains(reg, "alpha", "beta")
    assert result.left_chain == "alpha"
    assert result.right_chain == "beta"
