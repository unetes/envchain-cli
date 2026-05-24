"""Tests for envchain.locker."""
import json
from pathlib import Path

import pytest

from envchain.locker import (
    LockError,
    LockIndex,
    is_locked,
    list_locks,
    load_lock_index,
    lock_chain,
    lock_reason,
    save_lock_index,
    unlock_chain,
)


@pytest.fixture()
def idx() -> LockIndex:
    return LockIndex()


def test_lock_chain_marks_as_locked(idx):
    lock_chain(idx, "prod")
    assert is_locked(idx, "prod")


def test_lock_chain_stores_reason(idx):
    lock_chain(idx, "prod", reason="release freeze")
    assert lock_reason(idx, "prod") == "release freeze"


def test_lock_chain_default_reason_is_empty(idx):
    lock_chain(idx, "staging")
    assert lock_reason(idx, "staging") == ""


def test_lock_chain_raises_when_already_locked(idx):
    lock_chain(idx, "prod")
    with pytest.raises(LockError, match="already locked"):
        lock_chain(idx, "prod")


def test_unlock_chain_removes_lock(idx):
    lock_chain(idx, "prod")
    unlock_chain(idx, "prod")
    assert not is_locked(idx, "prod")


def test_unlock_chain_raises_when_not_locked(idx):
    with pytest.raises(LockError, match="not locked"):
        unlock_chain(idx, "prod")


def test_is_locked_returns_false_for_unknown(idx):
    assert not is_locked(idx, "unknown")


def test_list_locks_returns_sorted(idx):
    lock_chain(idx, "z-chain")
    lock_chain(idx, "a-chain")
    assert list_locks(idx) == ["a-chain", "z-chain"]


def test_list_locks_empty(idx):
    assert list_locks(idx) == []


def test_roundtrip_via_dict(idx):
    lock_chain(idx, "prod", reason="freeze")
    lock_chain(idx, "dev")
    restored = LockIndex.from_dict(idx.to_dict())
    assert is_locked(restored, "prod")
    assert lock_reason(restored, "prod") == "freeze"
    assert is_locked(restored, "dev")


def test_save_and_load(tmp_path, idx):
    lock_chain(idx, "prod", reason="deploy")
    p = tmp_path / "locks.json"
    save_lock_index(idx, p)
    loaded = load_lock_index(p)
    assert is_locked(loaded, "prod")
    assert lock_reason(loaded, "prod") == "deploy"


def test_load_missing_file_returns_empty(tmp_path):
    p = tmp_path / "nonexistent.json"
    idx = load_lock_index(p)
    assert list_locks(idx) == []


def test_save_creates_valid_json(tmp_path, idx):
    lock_chain(idx, "prod")
    p = tmp_path / "locks.json"
    save_lock_index(idx, p)
    data = json.loads(p.read_text())
    assert "locks" in data
    assert "prod" in data["locks"]
