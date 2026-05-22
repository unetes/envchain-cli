"""CLI command for comparing two chains side-by-side."""

import argparse
import json
from typing import Any
from envchain.comparator import compare_chains, CompareResult
from envchain.registry import ChainRegistry


def _format_text(result: CompareResult) -> str:
    lines = [f"Comparing '{result.left_chain}' vs '{result.right_chain}'\n"]
    col_w = max((len(r.key) for r in result.rows), default=10)
    header = f"{'KEY':<{col_w}}  {'LEFT':<20}  {'RIGHT':<20}  STATUS"
    lines.append(header)
    lines.append("-" * len(header))
    for row in result.rows:
        left = row.left_value if row.left_value is not None else "(missing)"
        right = row.right_value if row.right_value is not None else "(missing)"
        lines.append(f"{row.key:<{col_w}}  {left:<20}  {right:<20}  {row.status}")
    summary = result.summary()
    lines.append("")
    lines.append(
        f"Summary: {summary['same']} same, {summary['different']} different, "
        f"{summary['left_only']} left-only, {summary['right_only']} right-only"
    )
    return "\n".join(lines)


def _format_json(result: CompareResult) -> str:
    data: Any = {
        "left_chain": result.left_chain,
        "right_chain": result.right_chain,
        "has_differences": result.has_differences,
        "summary": result.summary(),
        "rows": [
            {
                "key": r.key,
                "left_value": r.left_value,
                "right_value": r.right_value,
                "status": r.status,
            }
            for r in result.rows
        ],
    }
    return json.dumps(data, indent=2)


def cmd_compare(args: argparse.Namespace, registry: ChainRegistry) -> int:
    try:
        result = compare_chains(
            registry,
            args.left,
            args.right,
            resolved=not args.no_resolve,
        )
    except KeyError as exc:
        print(f"Error: chain not found — {exc}")
        return 1

    if getattr(args, "format", "text") == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 1 if result.has_differences else 0


def build_compare_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("compare", help="Compare two chains side-by-side")
    p.add_argument("left", help="Name of the left chain")
    p.add_argument("right", help="Name of the right chain")
    p.add_argument(
        "--no-resolve",
        action="store_true",
        help="Compare only own vars, skip parent inheritance",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p
