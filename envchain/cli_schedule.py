"""CLI commands for managing export schedules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from envchain.scheduler import ScheduleEntry, ScheduleIndex, ScheduleError


def _load_index(path: str) -> ScheduleIndex:
    p = Path(path)
    if not p.exists():
        return ScheduleIndex()
    return ScheduleIndex.from_dict(json.loads(p.read_text()))


def _save_index(idx: ScheduleIndex, path: str) -> None:
    Path(path).write_text(json.dumps(idx.to_dict(), indent=2))


def cmd_schedule_add(args: argparse.Namespace, index_path: str = "schedules.json") -> int:
    idx = _load_index(index_path)
    entry = ScheduleEntry(
        chain_name=args.chain,
        output_path=args.output,
        format=getattr(args, "format", "dotenv"),
        interval_seconds=getattr(args, "interval", 3600),
    )
    idx.add(entry)
    _save_index(idx, index_path)
    print(f"Scheduled '{args.chain}' -> '{args.output}' every {entry.interval_seconds}s")
    return 0


def cmd_schedule_remove(args: argparse.Namespace, index_path: str = "schedules.json") -> int:
    idx = _load_index(index_path)
    try:
        idx.remove(args.chain, args.output)
    except ScheduleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    _save_index(idx, index_path)
    print(f"Removed schedule for '{args.chain}' -> '{args.output}'")
    return 0


def cmd_schedule_list(args: argparse.Namespace, index_path: str = "schedules.json") -> int:
    idx = _load_index(index_path)
    entries = idx.list_all()
    if not entries:
        print("No schedules defined.")
        return 0
    for e in entries:
        status = "enabled" if e.enabled else "disabled"
        print(f"  {e.chain_name:20s}  {e.output_path:30s}  [{e.format}]  every {e.interval_seconds}s  ({status})")
    return 0


def build_schedule_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("schedule", help="Manage auto-export schedules")
    sp = p.add_subparsers(dest="schedule_cmd")

    add_p = sp.add_parser("add", help="Add a new schedule")
    add_p.add_argument("chain", help="Chain name")
    add_p.add_argument("output", help="Output file path")
    add_p.add_argument("--format", default="dotenv", choices=["dotenv", "shell", "json"])
    add_p.add_argument("--interval", type=int, default=3600, help="Interval in seconds")
    add_p.set_defaults(func=cmd_schedule_add)

    rm_p = sp.add_parser("remove", help="Remove a schedule")
    rm_p.add_argument("chain")
    rm_p.add_argument("output")
    rm_p.set_defaults(func=cmd_schedule_remove)

    ls_p = sp.add_parser("list", help="List all schedules")
    ls_p.set_defaults(func=cmd_schedule_list)
