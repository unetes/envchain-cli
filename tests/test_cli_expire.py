"""Tests for envchain.cli_expire."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from envchain.cli_expire import (
    cmd_expire_set,
    cmd_expire_remove,
    cmd_expire_list,
    cmd_expire_check,
)
from envchain.expirer import ExpiryIndex, set_expiry

PAST_ISO = "2000-01-01T00:00:00"
FUTURE_ISO = "2999-01-01T00:00:00"


def _make_args(tmp_path, **kwargs):
    ns = SimpleNamespace(index_path=tmp_path / "expiry.json", **kwargs)
    return ns


def test_set_returns_0_on_success(tmp_path):
    args = _make_args(tmp_path, chain="prod", key="API_KEY", expires_at=FUTURE_ISO, note="")
    assert cmd_expire_set(args) == 0


def test_set_persists_entry(tmp_path):
    args = _make_args(tmp_path, chain="prod", key="API_KEY", expires_at=FUTURE_ISO, note="test")
    cmd_expire_set(args)
    data = json.loads((tmp_path / "expiry.json").read_text())
    assert len(data["entries"]) == 1
    assert data["entries"][0]["key"] == "API_KEY"


def test_set_invalid_date_returns_1(tmp_path):
    args = _make_args(tmp_path, chain="prod", key="K", expires_at="not-a-date", note="")
    assert cmd_expire_set(args) == 1


def test_remove_returns_0_on_success(tmp_path):
    args_set = _make_args(tmp_path, chain="prod", key="SECRET", expires_at=FUTURE_ISO, note="")
    cmd_expire_set(args_set)
    args_rm = _make_args(tmp_path, chain="prod", key="SECRET")
    assert cmd_expire_remove(args_rm) == 0


def test_remove_returns_1_when_missing(tmp_path):
    args = _make_args(tmp_path, chain="prod", key="GHOST")
    assert cmd_expire_remove(args) == 1


def test_list_prints_entries(tmp_path, capsys):
    args_set = _make_args(tmp_path, chain="dev", key="DB_PASS", expires_at=FUTURE_ISO, note="rotate")
    cmd_expire_set(args_set)
    args_list = _make_args(tmp_path)
    cmd_expire_list(args_list)
    out = capsys.readouterr().out
    assert "DB_PASS" in out
    assert "rotate" in out


def test_list_empty_index(tmp_path, capsys):
    args = _make_args(tmp_path)
    cmd_expire_list(args)
    out = capsys.readouterr().out
    assert "No expiry" in out


def test_check_returns_0_when_all_valid(tmp_path):
    args_set = _make_args(tmp_path, chain="prod", key="K", expires_at=FUTURE_ISO, note="")
    cmd_expire_set(args_set)
    args_check = _make_args(tmp_path, warn_within=60)
    assert cmd_expire_check(args_check) == 0


def test_check_returns_1_when_expired(tmp_path, capsys):
    args_set = _make_args(tmp_path, chain="prod", key="OLD", expires_at=PAST_ISO, note="")
    cmd_expire_set(args_set)
    args_check = _make_args(tmp_path, warn_within=60)
    result = cmd_expire_check(args_check)
    assert result == 1
    out = capsys.readouterr().out
    assert "expired" in out.lower()


def test_check_reports_soon_expiring(tmp_path, capsys):
    soon_iso = (datetime.now(timezone.utc) + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%S")
    args_set = _make_args(tmp_path, chain="prod", key="SOON", expires_at=soon_iso, note="")
    cmd_expire_set(args_set)
    args_check = _make_args(tmp_path, warn_within=3600)
    result = cmd_expire_check(args_check)
    assert result == 1
    out = capsys.readouterr().out
    assert "SOON" in out
