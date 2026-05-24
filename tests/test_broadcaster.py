"""Tests for envchain.broadcaster."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from envchain.broadcaster import (
    BroadcastError,
    BroadcastResult,
    broadcast,
    broadcast_to_command,
    broadcast_to_env,
    broadcast_to_file,
)

SAMPLE_VARS = {"FOO": "bar", "BAZ": "qux"}


# ---------------------------------------------------------------------------
# BroadcastResult
# ---------------------------------------------------------------------------

def test_result_str_ok():
    r = BroadcastResult(target="env", success=True, message="2 var(s) exported")
    assert "ok" in str(r)
    assert "env" in str(r)


def test_result_str_fail():
    r = BroadcastResult(target="/tmp/x", success=False, message="permission denied")
    assert "fail" in str(r)


# ---------------------------------------------------------------------------
# broadcast_to_env
# ---------------------------------------------------------------------------

def test_broadcast_to_env_sets_os_environ():
    broadcast_to_env({"_TEST_BCAST_KEY": "hello"})
    assert os.environ.get("_TEST_BCAST_KEY") == "hello"
    del os.environ["_TEST_BCAST_KEY"]


def test_broadcast_to_env_returns_success_result():
    result = broadcast_to_env(SAMPLE_VARS)
    assert result.success is True
    assert result.target == "env"


# ---------------------------------------------------------------------------
# broadcast_to_file
# ---------------------------------------------------------------------------

def test_broadcast_to_file_creates_file(tmp_path):
    dest = tmp_path / "out.env"
    result = broadcast_to_file(SAMPLE_VARS, str(dest))
    assert result.success is True
    assert dest.exists()


def test_broadcast_to_file_contains_key_value(tmp_path):
    dest = tmp_path / "out.env"
    broadcast_to_file({"MY_VAR": "my_val"}, str(dest))
    content = dest.read_text()
    assert "MY_VAR=my_val" in content


def test_broadcast_to_file_sorted_keys(tmp_path):
    dest = tmp_path / "out.env"
    broadcast_to_file({"Z_KEY": "1", "A_KEY": "2"}, str(dest))
    lines = dest.read_text().splitlines()
    assert lines[0].startswith("A_KEY")
    assert lines[1].startswith("Z_KEY")


def test_broadcast_to_file_bad_path_returns_failure():
    result = broadcast_to_file(SAMPLE_VARS, "/no/such/dir/out.env")
    assert result.success is False
    assert result.message != ""


# ---------------------------------------------------------------------------
# broadcast_to_command
# ---------------------------------------------------------------------------

def test_broadcast_to_command_passes_vars_to_process():
    result = broadcast_to_command(
        {"_BCAST_TEST": "passed"},
        [sys.executable, "-c", "import os, sys; sys.exit(0 if os.environ.get('_BCAST_TEST')=='passed' else 1)"],
    )
    assert result.success is True


def test_broadcast_to_command_nonzero_exit_is_failure():
    result = broadcast_to_command({}, [sys.executable, "-c", "raise SystemExit(2)"])
    assert result.success is False


def test_broadcast_to_command_empty_command_raises():
    with pytest.raises(BroadcastError):
        broadcast_to_command({}, [])


def test_broadcast_to_command_missing_binary_returns_failure():
    result = broadcast_to_command({}, ["/no/such/binary"])
    assert result.success is False


# ---------------------------------------------------------------------------
# broadcast (dispatcher)
# ---------------------------------------------------------------------------

def test_broadcast_env_target(tmp_path):
    results = broadcast({"_BCAST_DISP": "1"}, targets=[":env:"])
    assert len(results) == 1
    assert results[0].success is True
    os.environ.pop("_BCAST_DISP", None)


def test_broadcast_file_target(tmp_path):
    dest = str(tmp_path / "dispatch.env")
    results = broadcast(SAMPLE_VARS, targets=[dest])
    assert results[0].success is True


def test_broadcast_no_targets_returns_empty_list():
    results = broadcast(SAMPLE_VARS)
    assert results == []


def test_broadcast_command_target():
    results = broadcast({}, command=[sys.executable, "-c", "pass"])
    assert len(results) == 1
    assert results[0].success is True
