"""Tests for envchain.scorer."""
from __future__ import annotations

import pytest

from envchain.scorer import ScoreBreakdown, score_chain


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name, vars_=None, parent=None):
        self.name = name
        self.vars = vars_ or {}
        self.parent = parent


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)

    def all_names(self):
        return list(self._chains)


# ---------------------------------------------------------------------------
# ScoreBreakdown unit tests
# ---------------------------------------------------------------------------

def test_breakdown_base_score_is_100():
    bd = ScoreBreakdown(chain_name="test")
    assert bd.final_score == 100


def test_breakdown_deduction_reduces_score():
    bd = ScoreBreakdown(chain_name="test", deductions=[("bad thing", 20)])
    assert bd.final_score == 80


def test_breakdown_bonus_increases_score():
    bd = ScoreBreakdown(chain_name="test", bonuses=[("good thing", 5)])
    assert bd.final_score == 105  # capped at 100
    assert bd.final_score == 100  # max is 100


def test_breakdown_score_clamped_at_zero():
    bd = ScoreBreakdown(chain_name="test", deductions=[("huge penalty", 200)])
    assert bd.final_score == 0


def test_breakdown_grade_a():
    bd = ScoreBreakdown(chain_name="test")
    assert bd.grade == "A"


def test_breakdown_grade_f():
    bd = ScoreBreakdown(chain_name="test", deductions=[("huge", 200)])
    assert bd.grade == "F"


def test_breakdown_summary_contains_chain_name():
    bd = ScoreBreakdown(chain_name="mychain")
    assert "mychain" in bd.summary()


def test_breakdown_summary_contains_deduction_reason():
    bd = ScoreBreakdown(chain_name="x", deductions=[("missing values", 10)])
    assert "missing values" in bd.summary()


# ---------------------------------------------------------------------------
# score_chain integration tests
# ---------------------------------------------------------------------------

def test_score_chain_empty_vars_deducts_points():
    chain = _FakeChain("empty")
    bd = score_chain(chain)
    reasons = [r for r, _ in bd.deductions]
    assert any("no variables" in r for r in reasons)


def test_score_chain_with_vars_no_empty_deduction():
    chain = _FakeChain("full", vars_={f"K{i}": str(i) for i in range(6)})
    bd = score_chain(chain)
    reasons = [r for r, _ in bd.deductions]
    assert not any("no variables" in r for r in reasons)


def test_score_chain_good_coverage_bonus():
    chain = _FakeChain("full", vars_={f"KEY_{i}": str(i) for i in range(5)})
    bd = score_chain(chain)
    bonus_reasons = [r for r, _ in bd.bonuses]
    assert any("coverage" in r for r in bonus_reasons)


def test_score_chain_with_parent_gives_bonus():
    parent = _FakeChain("base", vars_={"A": "1"})
    child = _FakeChain("child", vars_={"B": "2"}, parent="base")
    reg = _FakeRegistry([parent, child])
    bd = score_chain(child, registry=reg)
    bonus_reasons = [r for r, _ in bd.bonuses]
    assert any("parent" in r for r in bonus_reasons)


def test_score_chain_returns_score_breakdown():
    chain = _FakeChain("x", vars_={"KEY": "val"})
    result = score_chain(chain)
    assert isinstance(result, ScoreBreakdown)
    assert result.chain_name == "x"
