"""Tests for envchain.auditor."""

import time
from pathlib import Path

import pytest

from envchain.auditor import AuditEntry, record, load_log, filter_log


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------

def test_audit_entry_str_contains_action():
    e = AuditEntry(action="set", chain="prod", key="DB_URL", old_value=None, new_value="x")
    assert "set" in str(e)


def test_audit_entry_str_contains_chain():
    e = AuditEntry(action="delete", chain="staging", key="TOKEN", old_value="abc", new_value=None)
    assert "staging" in str(e)


def test_audit_entry_str_contains_key():
    e = AuditEntry(action="set", chain="dev", key="MY_KEY", old_value=None, new_value="v")
    assert "MY_KEY" in str(e)


def test_audit_entry_str_no_key():
    e = AuditEntry(action="copy", chain="dev", key=None, old_value=None, new_value=None)
    s = str(e)
    assert "[" not in s


def test_audit_entry_roundtrip():
    e = AuditEntry(action="merge", chain="base", key="X", old_value="1", new_value="2", note="test")
    restored = AuditEntry.from_dict(e.to_dict())
    assert restored.action == e.action
    assert restored.chain == e.chain
    assert restored.note == e.note


# ---------------------------------------------------------------------------
# record / load_log
# ---------------------------------------------------------------------------

def test_record_creates_file(tmp_path):
    log = tmp_path / "audit.jsonl"
    e = AuditEntry(action="set", chain="dev", key="K", old_value=None, new_value="v")
    record(log, e)
    assert log.exists()


def test_load_log_returns_entries(tmp_path):
    log = tmp_path / "audit.jsonl"
    e1 = AuditEntry(action="set", chain="dev", key="A", old_value=None, new_value="1")
    e2 = AuditEntry(action="delete", chain="prod", key="B", old_value="2", new_value=None)
    record(log, e1)
    record(log, e2)
    entries = load_log(log)
    assert len(entries) == 2
    assert entries[0].action == "set"
    assert entries[1].action == "delete"


def test_load_log_missing_file_returns_empty(tmp_path):
    log = tmp_path / "nonexistent.jsonl"
    assert load_log(log) == []


def test_record_appends_multiple(tmp_path):
    log = tmp_path / "audit.jsonl"
    for i in range(5):
        record(log, AuditEntry(action="set", chain="c", key=f"K{i}", old_value=None, new_value=str(i)))
    assert len(load_log(log)) == 5


# ---------------------------------------------------------------------------
# filter_log
# ---------------------------------------------------------------------------

def _sample_entries():
    now = time.time()
    return [
        AuditEntry(action="set", chain="dev", key="A", old_value=None, new_value="1", timestamp=now - 100),
        AuditEntry(action="delete", chain="prod", key="B", old_value="2", new_value=None, timestamp=now - 50),
        AuditEntry(action="set", chain="dev", key="C", old_value=None, new_value="3", timestamp=now - 10),
    ]


def test_filter_by_chain():
    entries = filter_log(_sample_entries(), chain="dev")
    assert all(e.chain == "dev" for e in entries)
    assert len(entries) == 2


def test_filter_by_action():
    entries = filter_log(_sample_entries(), action="delete")
    assert len(entries) == 1
    assert entries[0].key == "B"


def test_filter_by_since():
    now = time.time()
    entries = filter_log(_sample_entries(), since=now - 60)
    assert len(entries) == 2


def test_filter_combined():
    entries = filter_log(_sample_entries(), chain="dev", action="set")
    assert len(entries) == 2
