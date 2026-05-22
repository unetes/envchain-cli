"""Tests for envchain.renamer."""

import pytest

from envchain.renamer import RenameError, rename_key, rename_key_in_chains


# ---------------------------------------------------------------------------
# rename_key
# ---------------------------------------------------------------------------

def test_rename_key_basic():
    result = rename_key({"FOO": "bar", "BAZ": "qux"}, "FOO", "NEW_FOO")
    assert "NEW_FOO" in result
    assert result["NEW_FOO"] == "bar"
    assert "FOO" not in result


def test_rename_key_preserves_other_keys():
    result = rename_key({"A": "1", "B": "2"}, "A", "C")
    assert result["B"] == "2"
    assert len(result) == 2


def test_rename_key_raises_when_old_key_missing():
    with pytest.raises(RenameError, match="not found"):
        rename_key({"FOO": "bar"}, "MISSING", "NEW")


def test_rename_key_raises_when_new_key_exists_no_overwrite():
    with pytest.raises(RenameError, match="already exists"):
        rename_key({"FOO": "bar", "NEW": "existing"}, "FOO", "NEW")


def test_rename_key_overwrite_replaces_existing():
    result = rename_key({"FOO": "bar", "NEW": "existing"}, "FOO", "NEW", overwrite=True)
    assert result["NEW"] == "bar"
    assert "FOO" not in result
    assert len(result) == 1


def test_rename_key_raises_on_empty_old_key():
    with pytest.raises(RenameError, match="old_key"):
        rename_key({"FOO": "bar"}, "", "NEW")


def test_rename_key_raises_on_empty_new_key():
    with pytest.raises(RenameError, match="new_key"):
        rename_key({"FOO": "bar"}, "FOO", "")


# ---------------------------------------------------------------------------
# rename_key_in_chains
# ---------------------------------------------------------------------------

def _sample_chains():
    return {
        "base": {"DB_HOST": "localhost", "PORT": "5432"},
        "staging": {"DB_HOST": "staging.db", "DEBUG": "true"},
        "prod": {"PORT": "5432"},
    }


def test_rename_in_chains_applies_to_all_by_default():
    result = rename_key_in_chains(_sample_chains(), "DB_HOST", "DATABASE_HOST")
    assert "DATABASE_HOST" in result["base"]
    assert "DATABASE_HOST" in result["staging"]
    # prod doesn't have DB_HOST; skip_missing=True by default
    assert "DB_HOST" not in result["prod"]


def test_rename_in_chains_subset_only():
    result = rename_key_in_chains(
        _sample_chains(), "DB_HOST", "DATABASE_HOST", chain_names=["base"]
    )
    assert "DATABASE_HOST" in result["base"]
    # staging should be untouched
    assert "DB_HOST" in result["staging"]


def test_rename_in_chains_skip_missing_false_raises():
    with pytest.raises(RenameError):
        rename_key_in_chains(
            _sample_chains(), "DB_HOST", "DATABASE_HOST", skip_missing=False
        )


def test_rename_in_chains_returns_new_dicts():
    chains = _sample_chains()
    result = rename_key_in_chains(chains, "PORT", "DB_PORT")
    # Original must be unmodified
    assert "PORT" in chains["base"]
    assert "DB_PORT" in result["base"]


def test_rename_in_chains_empty_chains():
    result = rename_key_in_chains({}, "FOO", "BAR")
    assert result == {}
