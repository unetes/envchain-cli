"""Tests for envchain.expirer."""
from datetime import datetime, timezone, timedelta
import pytest

from envchain.expirer import (
    ExpiryEntry,
    ExpiryIndex,
    ExpireError,
    set_expiry,
    remove_expiry,
    expired_entries,
    expiring_soon,
)

PAST = datetime(2000, 1, 1, tzinfo=timezone.utc)
FUTURE = datetime(2999, 1, 1, tzinfo=timezone.utc)
NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _idx(*entries):
    return ExpiryIndex(entries=list(entries))


def test_entry_is_expired_past():
    e = ExpiryEntry(chain="c", key="K", expires_at=PAST)
    assert e.is_expired(NOW) is True


def test_entry_is_not_expired_future():
    e = ExpiryEntry(chain="c", key="K", expires_at=FUTURE)
    assert e.is_expired(NOW) is False


def test_entry_roundtrip():
    e = ExpiryEntry(chain="prod", key="TOKEN", expires_at=NOW, note="rotate soon")
    assert ExpiryEntry.from_dict(e.to_dict()) == e


def test_set_expiry_adds_entry():
    idx = ExpiryIndex()
    set_expiry(idx, "prod", "API_KEY", FUTURE)
    assert len(idx.entries) == 1
    assert idx.entries[0].key == "API_KEY"


def test_set_expiry_replaces_existing():
    idx = ExpiryIndex()
    set_expiry(idx, "prod", "API_KEY", PAST)
    set_expiry(idx, "prod", "API_KEY", FUTURE, note="updated")
    assert len(idx.entries) == 1
    assert idx.entries[0].expires_at == FUTURE
    assert idx.entries[0].note == "updated"


def test_remove_expiry_removes_entry():
    idx = ExpiryIndex()
    set_expiry(idx, "prod", "SECRET", FUTURE)
    remove_expiry(idx, "prod", "SECRET")
    assert len(idx.entries) == 0


def test_remove_expiry_raises_when_missing():
    idx = ExpiryIndex()
    with pytest.raises(ExpireError, match="No expiry"):
        remove_expiry(idx, "prod", "MISSING")


def test_expired_entries_returns_past_only():
    idx = _idx(
        ExpiryEntry("c", "OLD", PAST),
        ExpiryEntry("c", "NEW", FUTURE),
    )
    result = expired_entries(idx, NOW)
    assert len(result) == 1
    assert result[0].key == "OLD"


def test_expired_entries_empty_when_none_expired():
    idx = _idx(ExpiryEntry("c", "K", FUTURE))
    assert expired_entries(idx, NOW) == []


def test_expiring_soon_within_window():
    soon = NOW + timedelta(seconds=300)
    idx = _idx(
        ExpiryEntry("c", "SOON", soon),
        ExpiryEntry("c", "LATER", FUTURE),
    )
    result = expiring_soon(idx, within_seconds=600, now=NOW)
    assert len(result) == 1
    assert result[0].key == "SOON"


def test_expiring_soon_excludes_already_expired():
    idx = _idx(ExpiryEntry("c", "OLD", PAST))
    result = expiring_soon(idx, within_seconds=9999999, now=NOW)
    assert result == []


def test_index_roundtrip():
    idx = ExpiryIndex()
    set_expiry(idx, "dev", "DB_PASS", FUTURE, note="quarterly")
    restored = ExpiryIndex.from_dict(idx.to_dict())
    assert len(restored.entries) == 1
    assert restored.entries[0].chain == "dev"
    assert restored.entries[0].note == "quarterly"
