"""CLI commands for managing envchain notification hooks (list, test)."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from envchain.notifier import NotifierIndex, NotifyEvent


def cmd_notify_list(args: Any, index: NotifierIndex) -> int:
    """List all registered notification hooks."""
    names = index.hook_names()
    if not names:
        print("No notification hooks registered.")
        return 0
    for name in names:
        print(name)
    return 0


def cmd_notify_test(args: Any, index: NotifierIndex) -> int:
    """Dispatch a synthetic test event through all registered hooks."""
    event = NotifyEvent(
        event_type="test",
        chain=getattr(args, "chain", "__test__"),
        key=getattr(args, "key", None),
        meta={"source": "cli_notify_test"},
    )
    print(f"Dispatching test event: {event}")
    failed = index.dispatch(event)
    if failed:
        print(
            f"WARNING: {len(failed)} hook(s) raised an exception: {', '.join(failed)}",
            file=sys.stderr,
        )
        return 1
    hook_count = len(index.hook_names())
    print(f"OK — {hook_count} hook(s) notified successfully.")
    return 0


def build_notify_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_notify = sub.add_parser("notify", help="Manage notification hooks.")
    notify_sub = p_notify.add_subparsers(dest="notify_cmd", required=True)

    # list
    notify_sub.add_parser("list", help="List registered hooks.")

    # test
    p_test = notify_sub.add_parser("test", help="Fire a test event.")
    p_test.add_argument("--chain", default="__test__", help="Chain name for test event.")
    p_test.add_argument("--key", default=None, help="Optional key name for test event.")


def run_notify_cmd(args: Any, index: NotifierIndex) -> int:
    """Dispatch to the appropriate notify sub-command."""
    dispatch = {
        "list": cmd_notify_list,
        "test": cmd_notify_test,
    }
    handler = dispatch.get(args.notify_cmd)
    if handler is None:
        print(f"Unknown notify command: {args.notify_cmd}", file=sys.stderr)
        return 2
    return handler(args, index)
