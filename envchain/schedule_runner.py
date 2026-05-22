"""Runner that executes due schedule entries by exporting chain vars."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envchain.scheduler import ScheduleEntry, ScheduleIndex
from envchain.registry import ChainRegistry
from envchain.chain import resolve
from envchain.exporter import export_vars


@dataclass
class RunResult:
    entry: ScheduleEntry
    success: bool
    error: str = ""


def run_due(
    idx: ScheduleIndex,
    registry: ChainRegistry,
    now: float | None = None,
) -> List[RunResult]:
    """Execute all due schedule entries and return results."""
    now = now if now is not None else time.time()
    results: List[RunResult] = []

    for entry in idx.due_entries(now):
        try:
            chain = registry.get(entry.chain_name)
            resolved = resolve(chain, registry)
            content = export_vars(resolved, fmt=entry.format, chain_name=entry.chain_name)
            Path(entry.output_path).write_text(content)
            entry.last_run = now
            results.append(RunResult(entry=entry, success=True))
        except Exception as exc:  # noqa: BLE001
            results.append(RunResult(entry=entry, success=False, error=str(exc)))

    return results


def summarise_run(results: List[RunResult]) -> str:
    """Return a human-readable summary of a run."""
    if not results:
        return "No entries were due."
    lines = []
    for r in results:
        if r.success:
            lines.append(f"  [OK]  {r.entry.chain_name} -> {r.entry.output_path}")
        else:
            lines.append(f"  [ERR] {r.entry.chain_name} -> {r.entry.output_path}: {r.error}")
    ok = sum(1 for r in results if r.success)
    lines.append(f"\n{ok}/{len(results)} succeeded.")
    return "\n".join(lines)
