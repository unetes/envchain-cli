"""CLI commands for broadcasting chain variables to external targets."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envchain.broadcaster import BroadcastError, broadcast


def cmd_broadcast(
    args: argparse.Namespace,
    registry,  # ChainRegistry
) -> int:
    """Resolve a chain and broadcast its vars to the requested targets."""
    chain = registry.get(args.chain)
    if chain is None:
        print(f"error: chain '{args.chain}' not found", file=sys.stderr)
        return 1

    from envchain.chain import resolve  # local import to avoid circular deps

    vars = resolve(chain, registry)

    targets: List[str] = list(args.target or [])
    command: Optional[List[str]] = list(args.cmd) if args.cmd else None

    if not targets and not command:
        print("error: specify at least one --target or --cmd", file=sys.stderr)
        return 1

    try:
        results = broadcast(vars, targets=targets, command=command)
    except BroadcastError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    all_ok = True
    for result in results:
        print(result)
        if not result.success:
            all_ok = False

    return 0 if all_ok else 1


def build_broadcast_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "broadcast",
        help="Resolve a chain and send its variables to one or more targets",
    )
    p.add_argument("chain", help="Name of the chain to resolve")
    p.add_argument(
        "--target",
        metavar="TARGET",
        action="append",
        help="Output target: ':env:' for current process, or a file path (repeatable)",
    )
    p.add_argument(
        "--cmd",
        nargs=argparse.REMAINDER,
        help="Command to run with variables injected (must be last argument)",
    )
    p.set_defaults(func=cmd_broadcast)
    return p
