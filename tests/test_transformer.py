"""Tests for envchain.transformer."""

import pytest

from envchain.transformer import (
    TransformError,
    apply_pipeline,
    apply_transform,
    available_transforms,
    transform_vars,
)


def test_available_transforms_is_sorted():
    names = available_transforms()
    assert names == sorted(names)


def test_available_transforms_includes_upper():
    assert "upper" in available_transforms()


def test_apply_transform_upper():
    assert apply_transform("hello", "upper") == "HELLO"


def test_apply_transform_lower():
    assert apply_transform("WORLD", "lower") == "world"


def test_apply_transform_strip():
    assert apply_transform("  hi  ", "strip") == "hi"


def test_apply_transform_reverse():
    assert apply_transform("abc", "reverse") == "cba"


def test_apply_transform_base64_roundtrip():
    encoded = apply_transform("secret", "base64encode")
    assert apply_transform(encoded, "base64decode") == "secret"


def test_apply_transform_urlencode():
    result = apply_transform("hello world", "urlencode")
    assert result == "hello%20world"


def test_apply_transform_urldecode():
    assert apply_transform("hello%20world", "urldecode") == "hello world"


def test_apply_transform_trim_quotes():
    assert apply_transform('"value"', "trim_quotes") == "value"


def test_apply_transform_unknown_raises():
    with pytest.raises(TransformError, match="Unknown transform"):
        apply_transform("x", "nonexistent")


def test_apply_pipeline_empty_returns_unchanged():
    assert apply_pipeline("Hello", []) == "Hello"


def test_apply_pipeline_multiple_steps():
    result = apply_pipeline("  Hello World  ", ["strip", "upper"])
    assert result == "HELLO WORLD"


def test_apply_pipeline_stops_on_bad_transform():
    with pytest.raises(TransformError):
        apply_pipeline("x", ["upper", "bad_transform"])


def test_transform_vars_all_keys():
    vars_ = {"A": "hello", "B": "world"}
    result = transform_vars(vars_, ["upper"])
    assert result == {"A": "HELLO", "B": "WORLD"}


def test_transform_vars_selected_keys_only():
    vars_ = {"A": "hello", "B": "world"}
    result = transform_vars(vars_, ["upper"], keys=["A"])
    assert result["A"] == "HELLO"
    assert result["B"] == "world"


def test_transform_vars_returns_new_dict():
    vars_ = {"A": "hello"}
    result = transform_vars(vars_, ["upper"])
    assert result is not vars_


def test_transform_vars_empty_pipeline_unchanged():
    vars_ = {"A": "hello"}
    assert transform_vars(vars_, []) == vars_
