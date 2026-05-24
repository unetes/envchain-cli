"""Broadcast resolved chain variables to one or more output targets."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class BroadcastError(Exception):
    """Raised when a broadcast operation fails."""


@dataclass
class BroadcastResult:
    target: str
    success: bool
    message: str = ""

    def __str__(self) -> str:
        status = "ok" if self.success else "fail"
        return f"[{status}] {self.target}: {self.message}"


def broadcast_to_env(vars: Dict[str, str]) -> BroadcastResult:
    """Write vars into the current process environment."""
    for key, value in vars.items():
        os.environ[key] = value
    return BroadcastResult(target="env", success=True, message=f"{len(vars)} var(s) exported")


def broadcast_to_file(vars: Dict[str, str], path: str) -> BroadcastResult:
    """Write vars as KEY=VALUE lines to a file."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            for key, value in sorted(vars.items()):
                fh.write(f"{key}={value}\n")
        return BroadcastResult(target=path, success=True, message=f"{len(vars)} var(s) written")
    except OSError as exc:
        return BroadcastResult(target=path, success=False, message=str(exc))


def broadcast_to_command(vars: Dict[str, str], command: List[str]) -> BroadcastResult:
    """Run *command* with vars injected into its environment."""
    if not command:
        raise BroadcastError("command must not be empty")
    env = {**os.environ, **vars}
    try:
        result = subprocess.run(command, env=env, check=False)
        return BroadcastResult(
            target=" ".join(command),
            success=result.returncode == 0,
            message=f"exit code {result.returncode}",
        )
    except FileNotFoundError as exc:
        return BroadcastResult(target=" ".join(command), success=False, message=str(exc))


def broadcast(
    vars: Dict[str, str],
    *,
    targets: Optional[List[str]] = None,
    command: Optional[List[str]] = None,
) -> List[BroadcastResult]:
    """Dispatch vars to all requested targets and return results."""
    results: List[BroadcastResult] = []
    for target in targets or []:
        if target == ":env:":
            results.append(broadcast_to_env(vars))
        else:
            results.append(broadcast_to_file(vars, target))
    if command:
        results.append(broadcast_to_command(vars, command))
    return results
