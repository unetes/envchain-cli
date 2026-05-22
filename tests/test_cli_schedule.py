"""Tests for envchain.cli_schedule."""

import argparse
import json
import pytest
from pathlib import Path
from envchain.cli_schedule import cmd_schedule_add, cmd_schedule_remove, cmd_schedule_list
from envchain.scheduler import ScheduleIndex


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"chain": "prod", "output": "/tmp/prod.env", "format": "dotenv", "interval": 60}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def idx_path(tmp_path):
    return str(tmp_path / "schedules.json")


def test_add_returns_0_on_success(idx_path):
    args = _make_args()
    assert cmd_schedule_add(args, idx_path) == 0


def test_add_persists_entry(idx_path):
    args = _make_args(chain="staging", output="/tmp/staging.env")
    cmd_schedule_add(args, idx_path)
    idx = ScheduleIndex.from_dict(json.loads(Path(idx_path).read_text()))
    entries = idx.list_all()
    assert any(e.chain_name == "staging" for e in entries)


def test_add_multiple_entries_accumulate(idx_path):
    cmd_schedule_add(_make_args(chain="a", output="/tmp/a.env"), idx_path)
    cmd_schedule_add(_make_args(chain="b", output="/tmp/b.env"), idx_path)
    idx = ScheduleIndex.from_dict(json.loads(Path(idx_path).read_text()))
    assert len(idx.list_all()) == 2


def test_remove_returns_0_on_success(idx_path):
    args = _make_args()
    cmd_schedule_add(args, idx_path)
    assert cmd_schedule_remove(args, idx_path) == 0


def test_remove_deletes_entry(idx_path):
    args = _make_args()
    cmd_schedule_add(args, idx_path)
    cmd_schedule_remove(args, idx_path)
    idx = ScheduleIndex.from_dict(json.loads(Path(idx_path).read_text()))
    assert len(idx.list_all()) == 0


def test_remove_nonexistent_returns_1(idx_path):
    args = _make_args(chain="ghost", output="/tmp/ghost.env")
    assert cmd_schedule_remove(args, idx_path) == 1


def test_list_returns_0_when_empty(idx_path, capsys):
    args = argparse.Namespace()
    assert cmd_schedule_list(args, idx_path) == 0
    out = capsys.readouterr().out
    assert "No schedules" in out


def test_list_shows_chain_name(idx_path, capsys):
    cmd_schedule_add(_make_args(chain="prod"), idx_path)
    cmd_schedule_list(argparse.Namespace(), idx_path)
    out = capsys.readouterr().out
    assert "prod" in out


def test_list_shows_format(idx_path, capsys):
    cmd_schedule_add(_make_args(format="json"), idx_path)
    cmd_schedule_list(argparse.Namespace(), idx_path)
    out = capsys.readouterr().out
    assert "json" in out
