"""Tests for envchain.searcher module."""

import pytest
from envchain.registry import ChainRegistry
from envchain.searcher import search_keys, SearchResult, SearchSummary


def _make_registry():
    reg = ChainRegistry()
    reg.add("base", vars={"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "dev"})
    reg.add("prod", parent="base", vars={"DB_HOST": "prod.db", "SECRET_KEY": "abc123"})
    reg.add("staging", parent="base", vars={"APP_ENV": "staging", "FEATURE_FLAG": "on"})
    return reg


def test_search_returns_summary_object():
    reg = _make_registry()
    result = search_keys(reg, "DB")
    assert isinstance(result, SearchSummary)


def test_search_finds_matching_keys():
    reg = _make_registry()
    result = search_keys(reg, "DB")
    keys = [r.key for r in result.results]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys


def test_search_total_count():
    reg = _make_registry()
    result = search_keys(reg, "DB")
    assert result.total == 3  # DB_HOST in base, DB_PORT in base, DB_HOST in prod


def test_search_chains_matched():
    reg = _make_registry()
    result = search_keys(reg, "DB")
    assert "base" in result.chains_matched
    assert "prod" in result.chains_matched


def test_search_no_results_returns_empty_summary():
    reg = _make_registry()
    result = search_keys(reg, "NONEXISTENT_KEY_XYZ")
    assert result.total == 0
    assert result.results == []


def test_search_case_insensitive_by_default():
    reg = _make_registry()
    result = search_keys(reg, "db_host")
    keys = [r.key for r in result.results]
    assert "DB_HOST" in keys


def test_search_case_sensitive_no_match():
    reg = _make_registry()
    result = search_keys(reg, "db_host", case_sensitive=True)
    assert result.total == 0


def test_search_case_sensitive_match():
    reg = _make_registry()
    result = search_keys(reg, "DB_HOST", case_sensitive=True)
    assert result.total == 2


def test_search_values_finds_value_match():
    reg = _make_registry()
    result = search_keys(reg, "localhost", search_values=True)
    assert result.total >= 1
    assert any(r.key == "DB_HOST" and r.matched_value for r in result.results)


def test_search_values_false_skips_value_match():
    reg = _make_registry()
    result = search_keys(reg, "localhost", search_values=False)
    assert result.total == 0


def test_search_chain_filter_limits_scope():
    reg = _make_registry()
    result = search_keys(reg, "DB", chain_filter="base")
    assert all(r.chain_name == "base" for r in result.results)


def test_search_chain_filter_nonexistent_returns_empty():
    reg = _make_registry()
    result = search_keys(reg, "DB", chain_filter="ghost")
    assert result.total == 0


def test_search_result_fields():
    reg = _make_registry()
    result = search_keys(reg, "APP_ENV", chain_filter="base")
    assert result.total == 1
    r = result.results[0]
    assert isinstance(r, SearchResult)
    assert r.chain_name == "base"
    assert r.key == "APP_ENV"
    assert r.value == "dev"
