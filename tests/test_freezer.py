"""Tests for envchain.freezer."""

import json
import pytest
from pathlib import Path

from envchain.freezer import (
    FreezeError,
    FreezeIndex,
    freeze,
    unfreeze,
    is_frozen,
    frozen_chains,
    freeze_reason,
    save_freeze_index,
    load_freeze_index,
)


@pytest.fixture
def idx() -> FreezeIndex:
    return FreezeIndex()


def test_freeze_marks_chain(idx):
    freeze(idx, "prod")
    assert is_frozen(idx, "prod")


def test_freeze_stores_reason(idx):
    freeze(idx, "prod", reason="release lock")
    assert freeze_reason(idx, "prod") == "release lock"


def test_freeze_default_reason_is_empty(idx):
    freeze(idx, "prod")
    assert freeze_reason(idx, "prod") == ""


def test_freeze_raises_when_already_frozen(idx):
    freeze(idx, "prod")
    with pytest.raises(FreezeError, match="already frozen"):
        freeze(idx, "prod")


def test_unfreeze_removes_chain(idx):
    freeze(idx, "prod")
    unfreeze(idx, "prod")
    assert not is_frozen(idx, "prod")


def test_unfreeze_raises_when_not_frozen(idx):
    with pytest.raises(FreezeError, match="not frozen"):
        unfreeze(idx, "prod")


def test_is_frozen_returns_false_for_unknown(idx):
    assert not is_frozen(idx, "staging")


def test_frozen_chains_returns_sorted(idx):
    freeze(idx, "z-chain")
    freeze(idx, "a-chain")
    assert frozen_chains(idx) == ["a-chain", "z-chain"]


def test_frozen_chains_empty_when_none(idx):
    assert frozen_chains(idx) == []


def test_roundtrip_to_dict_from_dict(idx):
    freeze(idx, "prod", reason="locked")
    freeze(idx, "staging")
    restored = FreezeIndex.from_dict(idx.to_dict())
    assert is_frozen(restored, "prod")
    assert freeze_reason(restored, "prod") == "locked"
    assert is_frozen(restored, "staging")


def test_save_and_load_freeze_index(tmp_path, idx):
    freeze(idx, "prod", reason="deploy")
    p = tmp_path / "freeze.json"
    save_freeze_index(idx, p)
    loaded = load_freeze_index(p)
    assert is_frozen(loaded, "prod")
    assert freeze_reason(loaded, "prod") == "deploy"


def test_load_freeze_index_missing_file_returns_empty(tmp_path):
    p = tmp_path / "nonexistent.json"
    loaded = load_freeze_index(p)
    assert frozen_chains(loaded) == []
