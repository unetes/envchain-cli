"""CLI commands for viewing the audit log."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Optional

from envchain.auditor import load_log, filter_log, AuditEntry

DEFAULT_LOG = Path(".envchain") / "audit.jsonl"


def _format_entry(entry: AuditEntry) -> str:
    """Format a single audit entry for display."""
    old = entry.old_value if entry.old_value is not None else "-"
    new = entry.new_value if entry.new_value is not None else "-"
    note = f"  # {entry.note}" if entry.note else ""
    return f"{entry}  {old} -> {new}{note}"


def cmd_audit_log(args: argparse.Namespace, log_path: Path = DEFAULT_LOG) -> int:
    """Print filtered audit log entries to stdout."""
    entries = load_log(log_path)

    since: Optional[float] = None
    if hasattr(args, "since") and args.since:
        try:
            since = time.time() - float(args.since) * 3600
        except ValueError:
            print(f"Error: --since must be a number of hours, got {args.since!r}")
            return 2

    chain = getattr(args, "chain", None) or None
    action = getattr(args, "action", None) or None

    filtered = filter_log(entries, chain=chain, action=action, since=since)

    if not filtered:
        print("No audit entries found.")
        return 0

    for entry in filtered:
        print(_format_entry(entry))

    return 0


def cmd_audit_clear(args: argparse.Namespace, log_path: Path = DEFAULT_LOG) -> int:
    """Clear the audit log file."""
    if not log_path.exists():
        print("Audit log is already empty.")
        return 0
    confirm = getattr(args, "yes", False)
    if not confirm:
        answer = input("Clear the entire audit log? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1
    log_path.write_text("", encoding="utf-8")
    print("Audit log cleared.")
    return 0


def build_audit_parser(subparsers: argparse._SubParsersAction) -> None:
    p_log = subparsers.add_parser("audit-log", help="Show audit log")
    p_log.add_argument("--chain", default="", help="Filter by chain name")
    p_log.add_argument("--action", default="", help="Filter by action (set, delete, rename, ...)")
    p_log.add_argument("--since", default="", help="Show entries from last N hours")
    p_log.set_defaults(func=cmd_audit_log)

    p_clear = subparsers.add_parser("audit-clear", help="Clear the audit log")
    p_clear.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    p_clear.set_defaults(func=cmd_audit_clear)
