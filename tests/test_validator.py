"""Tests for envchain.validator module."""

import pytest
from envchain.validator import (
    validate_key,
    validate_chain_name,
    validate_vars,
    validate_no_circular,
    ValidationError,
)


# --- validate_key ---

def test_valid_key_simple():
    validate_key("MY_VAR")  # should not raise


def test_valid_key_starts_with_underscore():
    validate_key("_PRIVATE")  # should not raise


def test_invalid_key_starts_with_digit():
    with pytest.raises(ValidationError, match="Invalid variable key"):
        validate_key("1BAD")


def test_invalid_key_empty():
    with pytest.raises(ValidationError, match="must not be empty"):
        validate_key("")


def test_invalid_key_contains_dash():
    with pytest.raises(ValidationError, match="Invalid variable key"):
        validate_key("MY-VAR")


# --- validate_chain_name ---

def test_valid_chain_name():
    validate_chain_name("prod.api-v2")  # should not raise


def test_invalid_chain_name_empty():
    with pytest.raises(ValidationError, match="must not be empty"):
        validate_chain_name("")


def test_invalid_chain_name_starts_with_dash():
    with pytest.raises(ValidationError, match="Invalid chain name"):
        validate_chain_name("-bad")


# --- validate_vars ---

def test_validate_vars_valid():
    validate_vars({"HOST": "localhost", "PORT": "8080"})  # should not raise


def test_validate_vars_invalid_key():
    with pytest.raises(ValidationError, match="Invalid variable key"):
        validate_vars({"BAD-KEY": "value"})


def test_validate_vars_non_string_value():
    with pytest.raises(ValidationError, match="must be a string"):
        validate_vars({"PORT": 8080})


# --- validate_no_circular ---

class _FakeChain:
    def __init__(self, parent):
        self.parent = parent


def test_no_circular_simple():
    chains = {"base": _FakeChain(None)}
    validate_no_circular("child", "base", chains)  # should not raise


def test_no_circular_direct_self_reference():
    chains = {}
    with pytest.raises(ValidationError, match="Circular inheritance"):
        validate_no_circular("a", "a", chains)


def test_no_circular_indirect_cycle():
    # a -> b -> c -> a would be circular when trying to set a's parent to c
    chains = {
        "b": _FakeChain("a"),
        "c": _FakeChain("b"),
    }
    with pytest.raises(ValidationError, match="Circular inheritance"):
        validate_no_circular("a", "c", chains)


def test_no_circular_valid_chain():
    chains = {
        "base": _FakeChain(None),
        "mid": _FakeChain("base"),
    }
    validate_no_circular("top", "mid", chains)  # should not raise
