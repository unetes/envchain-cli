"""Tests for envchain.redactor."""

import pytest

from envchain.redactor import (
    DEFAULT_MASK,
    RedactError,
    is_sensitive_key,
    redact_value,
    redact_vars,
    strip_sensitive,
)


# ---------------------------------------------------------------------------
# is_sensitive_key
# ---------------------------------------------------------------------------

def test_password_key_is_sensitive():
    assert is_sensitive_key("PASSWORD") is True


def test_token_key_is_sensitive():
    assert is_sensitive_key("GITHUB_TOKEN") is True


def test_api_key_is_sensitive():
    assert is_sensitive_key("API_KEY") is True


def test_plain_key_is_not_sensitive():
    assert is_sensitive_key("DATABASE_HOST") is False


def test_extra_pattern_matches():
    assert is_sensitive_key("MY_CREDENTIAL", extra_patterns=[r"credential"]) is True


def test_extra_pattern_does_not_match_unrelated():
    assert is_sensitive_key("DATABASE_HOST", extra_patterns=[r"credential"]) is False


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------

def test_redact_value_returns_default_mask():
    assert redact_value("super-secret") == DEFAULT_MASK


def test_redact_value_custom_mask():
    assert redact_value("super-secret", mask="[HIDDEN]") == "[HIDDEN]"


def test_redact_value_empty_mask_raises():
    with pytest.raises(RedactError):
        redact_value("value", mask="")


# ---------------------------------------------------------------------------
# redact_vars
# ---------------------------------------------------------------------------

def test_redact_vars_masks_sensitive_keys_auto():
    result = redact_vars({"API_KEY": "abc123", "HOST": "localhost"})
    assert result["API_KEY"] == DEFAULT_MASK
    assert result["HOST"] == "localhost"


def test_redact_vars_explicit_keys_always_masked():
    result = redact_vars({"HOST": "localhost"}, keys=["HOST"], auto_detect=False)
    assert result["HOST"] == DEFAULT_MASK


def test_redact_vars_auto_detect_false_skips_heuristic():
    result = redact_vars({"API_KEY": "abc"}, auto_detect=False)
    assert result["API_KEY"] == "abc"


def test_redact_vars_custom_mask():
    result = redact_vars({"SECRET": "x"}, mask="REDACTED")
    assert result["SECRET"] == "REDACTED"


def test_redact_vars_returns_copy_not_mutate():
    original = {"PASSWORD": "pw", "HOST": "h"}
    redact_vars(original)
    assert original["PASSWORD"] == "pw"


# ---------------------------------------------------------------------------
# strip_sensitive
# ---------------------------------------------------------------------------

def test_strip_sensitive_removes_sensitive_keys():
    result = strip_sensitive({"TOKEN": "t", "PORT": "8080"})
    assert "TOKEN" not in result
    assert "PORT" in result


def test_strip_sensitive_explicit_keys_removed():
    result = strip_sensitive({"HOST": "h"}, keys=["HOST"], auto_detect=False)
    assert "HOST" not in result


def test_strip_sensitive_empty_input_returns_empty():
    assert strip_sensitive({}) == {}


def test_strip_sensitive_no_sensitive_keys_returns_all():
    data = {"HOST": "localhost", "PORT": "5432"}
    assert strip_sensitive(data) == data
