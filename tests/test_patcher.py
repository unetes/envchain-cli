"""Tests for envchain.patcher."""

from __future__ import annotations

import pytest

from envchain.patcher import PatchError, PatchReport, patch_vars


class _FakeChain:
    def __init__(self, name: str, vars_: dict):
        self.name = name
        self.vars = dict(vars_)


# ---------------------------------------------------------------------------
# PatchReport tests
# ---------------------------------------------------------------------------

def test_patch_report_total_changes_sums_all():
    r = PatchReport("dev", added=["A"], updated=["B", "C"], deleted=["D"])
    assert r.total_changes == 4


def test_patch_report_summary_no_changes():
    r = PatchReport("dev", added=[], updated=[], deleted=[])
    assert "no changes" in r.summary()


def test_patch_report_summary_contains_chain_name():
    r = PatchReport("staging", added=["X"], updated=[], deleted=[])
    assert "staging" in r.summary()


def test_patch_report_summary_shows_added():
    r = PatchReport("dev", added=["A", "B"], updated=[], deleted=[])
    assert "+2 added" in r.summary()


def test_patch_report_summary_shows_updated():
    r = PatchReport("dev", added=[], updated=["A"], deleted=[])
    assert "~1 updated" in r.summary()


def test_patch_report_summary_shows_deleted():
    r = PatchReport("dev", added=[], updated=[], deleted=["A"])
    assert "-1 deleted" in r.summary()


def test_patch_report_lists_are_sorted():
    r = PatchReport("dev", added=["Z", "A"], updated=[], deleted=[])
    assert r.added == ["A", "Z"]


# ---------------------------------------------------------------------------
# patch_vars – add / update
# ---------------------------------------------------------------------------

def test_patch_adds_new_key():
    chain = _FakeChain("dev", {"FOO": "bar"})
    report = patch_vars(chain, updates={"NEW": "val"})
    assert chain.vars["NEW"] == "val"
    assert "NEW" in report.added


def test_patch_updates_existing_key():
    chain = _FakeChain("dev", {"FOO": "old"})
    report = patch_vars(chain, updates={"FOO": "new"})
    assert chain.vars["FOO"] == "new"
    assert "FOO" in report.updated


def test_patch_same_value_not_counted_as_update():
    chain = _FakeChain("dev", {"FOO": "same"})
    report = patch_vars(chain, updates={"FOO": "same"})
    assert "FOO" not in report.updated
    assert report.total_changes == 0


def test_patch_preserves_untouched_keys():
    chain = _FakeChain("dev", {"FOO": "a", "BAR": "b"})
    patch_vars(chain, updates={"FOO": "z"})
    assert chain.vars["BAR"] == "b"


def test_patch_allow_new_false_raises_on_unknown_key():
    chain = _FakeChain("dev", {"FOO": "a"})
    with pytest.raises(PatchError, match="allow_new"):
        patch_vars(chain, updates={"UNKNOWN": "x"}, allow_new=False)


# ---------------------------------------------------------------------------
# patch_vars – deletions
# ---------------------------------------------------------------------------

def test_patch_deletes_existing_key():
    chain = _FakeChain("dev", {"FOO": "a", "BAR": "b"})
    report = patch_vars(chain, deletions=["FOO"])
    assert "FOO" not in chain.vars
    assert "FOO" in report.deleted


def test_patch_delete_missing_key_raises():
    chain = _FakeChain("dev", {"FOO": "a"})
    with pytest.raises(PatchError, match="not found"):
        patch_vars(chain, deletions=["MISSING"])


def test_patch_combined_add_update_delete():
    chain = _FakeChain("dev", {"OLD": "x", "KEEP": "y"})
    report = patch_vars(
        chain,
        updates={"NEW": "n", "KEEP": "z"},
        deletions=["OLD"],
    )
    assert "OLD" not in chain.vars
    assert chain.vars["NEW"] == "n"
    assert chain.vars["KEEP"] == "z"
    assert report.total_changes == 3
