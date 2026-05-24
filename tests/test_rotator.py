"""Tests for envchain.rotator."""
import pytest
from envchain.rotator import (
    RotateError,
    RotateReport,
    rotate_keys,
    _default_generator,
)


class _FakeChain:
    def __init__(self, name: str, vars_: dict):
        self.name = name
        self.vars = dict(vars_)


class _FakeRegistry:
    def __init__(self, chains: dict):
        self._chains = chains

    def get(self, name: str):
        return self._chains.get(name)


def _make_registry():
    return _FakeRegistry({
        "prod": _FakeChain("prod", {"DB_PASS": "old_pass", "API_KEY": "old_key"}),
        "dev": _FakeChain("dev", {"SECRET": "dev_secret"}),
    })


def test_rotate_returns_report():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS"])
    assert isinstance(report, RotateReport)


def test_rotate_total_rotated_count():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS", "API_KEY"])
    assert report.total_rotated == 2


def test_rotate_updates_chain_vars():
    reg = _make_registry()
    rotate_keys(reg, "prod", ["DB_PASS"])
    assert reg.get("prod").vars["DB_PASS"] != "old_pass"


def test_rotate_entry_records_old_value():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS"])
    assert report.entries[0].old_value == "old_pass"


def test_rotate_entry_records_new_value():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS"])
    assert report.entries[0].new_value != "old_pass"


def test_rotate_dry_run_does_not_modify_chain():
    reg = _make_registry()
    rotate_keys(reg, "prod", ["DB_PASS"], dry_run=True)
    assert reg.get("prod").vars["DB_PASS"] == "old_pass"


def test_rotate_dry_run_still_returns_entries():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS"], dry_run=True)
    assert report.total_rotated == 1


def test_rotate_raises_when_chain_missing():
    reg = _make_registry()
    with pytest.raises(RotateError, match="not found"):
        rotate_keys(reg, "missing", ["DB_PASS"])


def test_rotate_raises_when_key_missing():
    reg = _make_registry()
    with pytest.raises(RotateError, match="'NO_SUCH_KEY'"):
        rotate_keys(reg, "prod", ["NO_SUCH_KEY"])


def test_rotate_custom_generator_is_used():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS"], generator=lambda: "FIXED")
    assert report.entries[0].new_value == "FIXED"
    assert reg.get("prod").vars["DB_PASS"] == "FIXED"


def test_rotate_entry_to_dict_has_required_keys():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS"])
    d = report.entries[0].to_dict()
    assert set(d.keys()) == {"chain", "key", "old_value", "new_value"}


def test_rotate_summary_lists_all_keys():
    reg = _make_registry()
    report = rotate_keys(reg, "prod", ["DB_PASS", "API_KEY"])
    summary = report.summary()
    assert "DB_PASS" in summary
    assert "API_KEY" in summary


def test_rotate_summary_empty_report():
    report = RotateReport()
    assert report.summary() == "No keys rotated."


def test_default_generator_returns_string_of_correct_length():
    val = _default_generator(16)
    assert len(val) == 16


def test_default_generator_unique_each_call():
    assert _default_generator() != _default_generator()
