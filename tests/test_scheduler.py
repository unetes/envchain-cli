"""Tests for envchain.scheduler."""

import time
import pytest
from envchain.scheduler import ScheduleEntry, ScheduleIndex, ScheduleError


@pytest.fixture
def idx():
    return ScheduleIndex()


@pytest.fixture
def entry():
    return ScheduleEntry(
        chain_name="prod",
        output_path="/tmp/prod.env",
        format="dotenv",
        interval_seconds=60,
    )


def test_entry_is_due_when_never_run(entry):
    assert entry.is_due(time.time()) is True


def test_entry_not_due_when_recently_run(entry):
    entry.last_run = time.time()
    assert entry.is_due(time.time()) is False


def test_entry_due_after_interval_passes(entry):
    entry.last_run = time.time() - 120
    entry.interval_seconds = 60
    assert entry.is_due(time.time()) is True


def test_entry_not_due_when_disabled(entry):
    entry.enabled = False
    assert entry.is_due(time.time()) is False


def test_entry_roundtrip(entry):
    restored = ScheduleEntry.from_dict(entry.to_dict())
    assert restored.chain_name == entry.chain_name
    assert restored.output_path == entry.output_path
    assert restored.format == entry.format
    assert restored.interval_seconds == entry.interval_seconds
    assert restored.enabled == entry.enabled


def test_add_entry_to_index(idx, entry):
    idx.add(entry)
    assert len(idx.list_all()) == 1


def test_add_multiple_entries(idx):
    idx.add(ScheduleEntry("a", "/tmp/a.env"))
    idx.add(ScheduleEntry("b", "/tmp/b.env"))
    assert len(idx.list_all()) == 2


def test_remove_entry(idx, entry):
    idx.add(entry)
    idx.remove(entry.chain_name, entry.output_path)
    assert len(idx.list_all()) == 0


def test_remove_nonexistent_raises(idx):
    with pytest.raises(ScheduleError):
        idx.remove("ghost", "/tmp/ghost.env")


def test_due_entries_returns_only_due(idx):
    now = time.time()
    e1 = ScheduleEntry("a", "/tmp/a.env", interval_seconds=10, last_run=now - 20)
    e2 = ScheduleEntry("b", "/tmp/b.env", interval_seconds=3600, last_run=now)
    idx.add(e1)
    idx.add(e2)
    due = idx.due_entries(now)
    assert len(due) == 1
    assert due[0].chain_name == "a"


def test_index_roundtrip(idx, entry):
    idx.add(entry)
    restored = ScheduleIndex.from_dict(idx.to_dict())
    entries = restored.list_all()
    assert len(entries) == 1
    assert entries[0].chain_name == entry.chain_name


def test_list_all_sorted_by_chain_name(idx):
    idx.add(ScheduleEntry("z", "/tmp/z.env"))
    idx.add(ScheduleEntry("a", "/tmp/a.env"))
    names = [e.chain_name for e in idx.list_all()]
    assert names == ["a", "z"]
