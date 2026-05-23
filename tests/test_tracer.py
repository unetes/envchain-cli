"""Tests for envchain.tracer."""

import pytest

from envchain.tracer import TraceError, TraceResult, TraceStep, trace_key


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class _FakeChain:
    def __init__(self, name, vars_, parent=None):
        self.name = name
        self.vars = vars_
        self.parent = parent


class _FakeRegistry:
    def __init__(self, chains):
        self._chains = {c.name: c for c in chains}

    def get(self, name):
        return self._chains.get(name)


def _make_registry():
    root = _FakeChain("base", {"HOST": "localhost", "PORT": "5432"})
    child = _FakeChain("dev", {"PORT": "5433"}, parent="base")
    grandchild = _FakeChain("dev-local", {}, parent="dev")
    return _FakeRegistry([root, child, grandchild])


# Patch _ancestors so it works with our fake registry
import envchain.chain as _chain_mod


def _fake_ancestors(registry, name):
    visited, order = set(), []
    current = registry.get(name)
    while current and current.parent:
        parent_name = current.parent
        if parent_name in visited:
            break
        visited.add(parent_name)
        order.append(parent_name)
        current = registry.get(parent_name)
    return order


@pytest.fixture(autouse=True)
def patch_ancestors(monkeypatch):
    monkeypatch.setattr(_chain_mod, "_ancestors", _fake_ancestors)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_trace_returns_trace_result():
    reg = _make_registry()
    result = trace_key(reg, "dev", "PORT")
    assert isinstance(result, TraceResult)


def test_trace_found_in_own_chain():
    reg = _make_registry()
    result = trace_key(reg, "dev", "PORT")
    assert result.found is True
    assert result.final_value == "5433"
    assert result.steps[0].chain_name == "dev"
    assert result.steps[0].resolved is True


def test_trace_found_in_parent():
    reg = _make_registry()
    result = trace_key(reg, "dev", "HOST")
    assert result.found is True
    assert result.final_value == "localhost"
    # First step (dev) should be unresolved, second (base) resolved
    assert result.steps[0].resolved is False
    assert result.steps[1].resolved is True
    assert result.steps[1].chain_name == "base"


def test_trace_found_in_grandparent():
    reg = _make_registry()
    result = trace_key(reg, "dev-local", "HOST")
    assert result.found is True
    assert result.final_value == "localhost"
    chain_names = [s.chain_name for s in result.steps]
    assert "dev-local" in chain_names
    assert "base" in chain_names


def test_trace_key_not_found():
    reg = _make_registry()
    result = trace_key(reg, "dev", "MISSING_KEY")
    assert result.found is False
    assert result.final_value is None


def test_trace_raises_on_unknown_chain():
    reg = _make_registry()
    with pytest.raises(TraceError):
        trace_key(reg, "nonexistent", "HOST")


def test_trace_step_str_resolved():
    step = TraceStep(chain_name="base", key="HOST", value="localhost", resolved=True)
    assert "resolved here" in str(step)
    assert "localhost" in str(step)


def test_trace_step_str_unresolved():
    step = TraceStep(chain_name="dev", key="HOST", value=None, resolved=False)
    assert "not set" in str(step)


def test_trace_result_summary_contains_key():
    reg = _make_registry()
    result = trace_key(reg, "dev", "PORT")
    summary = result.summary()
    assert "PORT" in summary


def test_trace_step_to_dict():
    step = TraceStep(chain_name="base", key="HOST", value="localhost", resolved=True)
    d = step.to_dict()
    assert d["chain"] == "base"
    assert d["key"] == "HOST"
    assert d["value"] == "localhost"
    assert d["resolved"] is True
