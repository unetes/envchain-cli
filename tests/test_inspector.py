"""Tests for envchain.inspector."""
import pytest
from envchain.inspector import inspect_chain, InspectReport, KeyInfo


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


# ---------- helpers ----------

def _make_registry():
    root = _FakeChain("root", {"A": "1", "B": "2"})
    child = _FakeChain("child", {"B": "override", "C": "3"}, parent="root")
    grandchild = _FakeChain("grandchild", {"D": "4"}, parent="child")
    return _FakeRegistry([root, child, grandchild])


# ---------- tests ----------

def test_inspect_returns_report_type():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    assert isinstance(report, InspectReport)


def test_inspect_unknown_chain_raises():
    reg = _make_registry()
    with pytest.raises(ValueError, match="not found"):
        inspect_chain("ghost", reg)


def test_inspect_chain_name_matches():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    assert report.chain_name == "child"


def test_inspect_parent_is_set():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    assert report.parent == "root"


def test_inspect_root_has_no_parent():
    reg = _make_registry()
    report = inspect_chain("root", reg)
    assert report.parent is None


def test_inspect_ancestry_excludes_self():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    assert "child" not in report.ancestry


def test_inspect_ancestry_includes_parent():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    assert "root" in report.ancestry


def test_inspect_all_keys_present():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    key_names = {k.key for k in report.keys}
    assert key_names == {"A", "B", "C"}


def test_inspect_own_keys_correct():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    own = {k.key for k in report.own_keys}
    # B is overridden by child, C is new in child
    assert "C" in own
    assert "B" in own


def test_inspect_inherited_key_source():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    inherited = {k.key: k for k in report.inherited_keys}
    assert "A" in inherited
    assert inherited["A"].source_chain == "root"


def test_inspect_to_dict_has_required_keys():
    reg = _make_registry()
    report = inspect_chain("child", reg)
    d = report.to_dict()
    assert "chain_name" in d
    assert "parent" in d
    assert "ancestry" in d
    assert "keys" in d


def test_key_info_to_dict_structure():
    ki = KeyInfo(key="FOO", value="bar", source_chain="mychain", overridden=False)
    d = ki.to_dict()
    assert d["key"] == "FOO"
    assert d["value"] == "bar"
    assert d["source_chain"] == "mychain"
    assert d["overridden"] is False


def test_inspect_grandchild_inherits_all():
    reg = _make_registry()
    report = inspect_chain("grandchild", reg)
    key_names = {k.key for k in report.keys}
    assert {"A", "B", "C", "D"}.issubset(key_names)
