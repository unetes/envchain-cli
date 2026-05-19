"""Tests for envchain.snapshot."""

import json
import time
from pathlib import Path

import pytest

from envchain.snapshot import (
    SNAPSHOT_VERSION,
    create_snapshot,
    diff_snapshots,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


SAMPLE_VARS = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"}


# ---------------------------------------------------------------------------
# create_snapshot
# ---------------------------------------------------------------------------

def test_create_snapshot_has_required_keys():
    snap = create_snapshot("prod", SAMPLE_VARS)
    assert snap["version"] == SNAPSHOT_VERSION
    assert snap["chain"] == "prod"
    assert snap["variables"] == SAMPLE_VARS
    assert isinstance(snap["timestamp"], int)


def test_create_snapshot_label_defaults_to_empty_string():
    snap = create_snapshot("dev", {})
    assert snap["label"] == ""


def test_create_snapshot_custom_label():
    snap = create_snapshot("staging", {}, label="before-deploy")
    assert snap["label"] == "before-deploy"


def test_create_snapshot_timestamp_is_recent():
    before = int(time.time())
    snap = create_snapshot("x", {})
    after = int(time.time())
    assert before <= snap["timestamp"] <= after


# ---------------------------------------------------------------------------
# save_snapshot / load_snapshot
# ---------------------------------------------------------------------------

def test_save_snapshot_creates_file(tmp_path):
    snap = create_snapshot("prod", SAMPLE_VARS)
    dest = save_snapshot(snap, tmp_path)
    assert dest.exists()
    assert dest.suffix == ".json"


def test_save_snapshot_filename_contains_chain_and_timestamp(tmp_path):
    snap = create_snapshot("prod", SAMPLE_VARS)
    dest = save_snapshot(snap, tmp_path)
    assert dest.name.startswith("prod_")


def test_load_snapshot_roundtrip(tmp_path):
    snap = create_snapshot("prod", SAMPLE_VARS)
    dest = save_snapshot(snap, tmp_path)
    loaded = load_snapshot(dest)
    assert loaded == snap


def test_load_snapshot_raises_on_wrong_version(tmp_path):
    bad = {"version": 99, "chain": "x", "variables": {}}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported snapshot version"):
        load_snapshot(p)


# ---------------------------------------------------------------------------
# list_snapshots
# ---------------------------------------------------------------------------

def test_list_snapshots_empty_when_directory_missing(tmp_path):
    assert list_snapshots(tmp_path / "nonexistent") == []


def test_list_snapshots_returns_all(tmp_path):
    for chain in ("prod", "dev", "prod"):
        save_snapshot(create_snapshot(chain, {}), tmp_path)
    assert len(list_snapshots(tmp_path)) == 3


def test_list_snapshots_filtered_by_chain(tmp_path):
    save_snapshot(create_snapshot("prod", {}), tmp_path)
    save_snapshot(create_snapshot("dev", {}), tmp_path)
    results = list_snapshots(tmp_path, chain_name="prod")
    assert all(p.name.startswith("prod_") for p in results)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_no_changes():
    s = create_snapshot("prod", SAMPLE_VARS)
    assert diff_snapshots(s, s) == {}


def test_diff_detects_changed_value():
    old = create_snapshot("prod", {"KEY": "old"})
    new = create_snapshot("prod", {"KEY": "new"})
    diff = diff_snapshots(old, new)
    assert diff == {"KEY": {"old": "old", "new": "new"}}


def test_diff_detects_added_key():
    old = create_snapshot("prod", {})
    new = create_snapshot("prod", {"NEW_KEY": "val"})
    diff = diff_snapshots(old, new)
    assert diff == {"NEW_KEY": {"old": None, "new": "val"}}


def test_diff_detects_removed_key():
    old = create_snapshot("prod", {"GONE": "bye"})
    new = create_snapshot("prod", {})
    diff = diff_snapshots(old, new)
    assert diff == {"GONE": {"old": "bye", "new": None}}
