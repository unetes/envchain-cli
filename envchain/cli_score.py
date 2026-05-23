"""CLI commands for the chain health scorer."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envchain.scorer import score_chain, ScoreBreakdown


def _format_text(breakdowns: List[ScoreBreakdown]) -> str:
    return "\n\n".join(bd.summary() for bd in breakdowns)


def _format_json(breakdowns: List[ScoreBreakdown]) -> str:
    rows = []
    for bd in breakdowns:
        rows.append({
            "chain": bd.chain_name,
            "score": bd.final_score,
            "grade": bd.grade,
            "deductions": [{"reason": r, "points": p} for r, p in bd.deductions],
            "bonuses": [{"reason": r, "points": p} for r, p in bd.bonuses],
        })
    return json.dumps(rows, indent=2)


def cmd_score(args: argparse.Namespace, registry) -> int:
    """Score one or more chains and print the results."""
    names: List[str] = args.chains if args.chains else registry.all_names()

    if not names:
        print("No chains found.", file=sys.stderr)
        return 1

    breakdowns = []
    for name in names:
        chain = registry.get(name)
        if chain is None:
            print(f"Chain '{name}' not found.", file=sys.stderr)
            return 2
        breakdowns.append(score_chain(chain, registry=registry))

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(_format_json(breakdowns))
    else:
        print(_format_text(breakdowns))

    if args.fail_below is not None:
        if any(bd.final_score < args.fail_below for bd in breakdowns):
            return 3

    return 0


def build_score_parser(subparsers) -> None:
    p: argparse.ArgumentParser = subparsers.add_parser(
        "score",
        help="Show health score for one or more chains.",
    )
    p.add_argument("chains", nargs="*", metavar="CHAIN",
                   help="Chain names to score (default: all).")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument(
        "--fail-below", dest="fail_below", type=int, default=None, metavar="N",
        help="Exit with code 3 if any chain scores below N.",
    )
    p.set_defaults(func=cmd_score)
