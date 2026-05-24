"""CLI commands for sorting chain variable keys."""

from __future__ import annotations

import argparse
import json
from typing import Optional

from envchain.sorter import AVAILABLE_STRATEGIES, SortError, sort_chain_vars


def _format_text(chain_name: str, sorted_vars: dict) -> str:
    lines = [f"# {chain_name}"]
    for key, value in sorted_vars.items():
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def _format_json(chain_name: str, sorted_vars: dict) -> str:
    return json.dumps({"chain": chain_name, "vars": sorted_vars}, indent=2)


def cmd_sort(
    args: argparse.Namespace,
    registry,
    out=None,
    err=None,
) -> int:
    """Sort and display a chain's variables.

    Returns 0 on success, 1 on error.
    """
    import sys

    out = out or sys.stdout
    err = err or sys.stderr

    try:
        sorted_vars = sort_chain_vars(args.chain, registry, args.strategy)
    except SortError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if getattr(args, "format", "text") == "json":
        out.write(_format_json(args.chain, sorted_vars) + "\n")
    else:
        out.write(_format_text(args.chain, sorted_vars) + "\n")

    return 0


def build_sort_parser(subparsers) -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "sort",
        help="Display a chain's variables sorted by a chosen strategy.",
    )
    parser.add_argument("chain", help="Name of the chain to sort.")
    parser.add_argument(
        "--strategy",
        choices=AVAILABLE_STRATEGIES,
        default="alpha",
        help="Sort strategy (default: alpha).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.set_defaults(func=cmd_sort)
    return parser
