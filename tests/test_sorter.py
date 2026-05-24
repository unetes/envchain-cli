"""Tests for envchain.sorter."""

import pytest

from envchain.sorter import (
    AVAILABLE_STRATEGIES,
    SortError,
    sort_chain_vars,
    sort_vars,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name: str, vars_: dict):
        self.name = name
        self.vars = vars_


class _FakeRegistry:
    def __init__(self, chains: dict):
        self._chains = chains

    def get(self, name: str):
        return self._chains.get(name)


def _registry(*chains: _FakeChain) -> _FakeRegistry:
    return _FakeRegistry({c.name: c for c in chains})


# ---------------------------------------------------------------------------
# sort_vars
# ---------------------------------------------------------------------------

def test_sort_vars_alpha_ascending():
    result = sort_vars({"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}, "alpha")
    assert list(result.keys()) == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_vars_alpha_descending():
    result = sort_vars({"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}, "alpha_desc")
    assert list(result.keys()) == ["ZEBRA", "MANGO", "APPLE"]


def test_sort_vars_length_ascending():
    result = sort_vars({"AB": "1", "ABCDE": "2", "ABC": "3"}, "length")
    assert list(result.keys()) == ["AB", "ABC", "ABCDE"]


def test_sort_vars_length_descending():
    result = sort_vars({"AB": "1", "ABCDE": "2", "ABC": "3"}, "length_desc")
    assert list(result.keys()) == ["ABCDE", "ABC", "AB"]


def test_sort_vars_preserves_values():
    original = {"Z": "zval", "A": "aval"}
    result = sort_vars(original, "alpha")
    assert result["Z"] == "zval"
    assert result["A"] == "aval"


def test_sort_vars_empty_dict_returns_empty():
    assert sort_vars({}, "alpha") == {}


def test_sort_vars_unknown_strategy_raises():
    with pytest.raises(SortError, match="Unknown sort strategy"):
        sort_vars({"A": "1"}, "random")  # type: ignore[arg-type]


def test_sort_vars_does_not_mutate_original():
    original = {"Z": "1", "A": "2"}
    sort_vars(original, "alpha")
    assert list(original.keys()) == ["Z", "A"]


def test_sort_vars_case_insensitive_alpha():
    result = sort_vars({"b_KEY": "1", "A_KEY": "2", "c_KEY": "3"}, "alpha")
    assert list(result.keys()) == ["A_KEY", "b_KEY", "c_KEY"]


# ---------------------------------------------------------------------------
# AVAILABLE_STRATEGIES
# ---------------------------------------------------------------------------

def test_available_strategies_is_sorted():
    assert AVAILABLE_STRATEGIES == sorted(AVAILABLE_STRATEGIES)


def test_available_strategies_includes_alpha():
    assert "alpha" in AVAILABLE_STRATEGIES


# ---------------------------------------------------------------------------
# sort_chain_vars
# ---------------------------------------------------------------------------

def test_sort_chain_vars_returns_sorted_own_vars():
    chain = _FakeChain("dev", {"Z": "1", "A": "2", "M": "3"})
    reg = _registry(chain)
    result = sort_chain_vars("dev", reg, "alpha")
    assert list(result.keys()) == ["A", "M", "Z"]


def test_sort_chain_vars_raises_when_chain_missing():
    reg = _registry()
    with pytest.raises(SortError, match="not found"):
        sort_chain_vars("ghost", reg)


def test_sort_chain_vars_default_strategy_is_alpha():
    chain = _FakeChain("prod", {"Z": "1", "A": "2"})
    reg = _registry(chain)
    result = sort_chain_vars("prod", reg)
    assert list(result.keys()) == ["A", "Z"]
