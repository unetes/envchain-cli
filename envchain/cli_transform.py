"""CLI commands for the value-transformation pipeline."""

from __future__ import annotations

import argparse
import json
from typing import List

from envchain.transformer import (
    TransformError,
    apply_pipeline,
    available_transforms,
    transform_vars,
)


def cmd_transform_value(args: argparse.Namespace) -> int:
    """Apply a pipeline of transforms to a single value and print the result."""
    pipeline: List[str] = args.transforms
    try:
        result = apply_pipeline(args.value, pipeline)
    except TransformError as exc:
        print(f"error: {exc}")
        return 1
    print(result)
    return 0


def cmd_transform_chain(args: argparse.Namespace, registry) -> int:
    """Apply transforms to all (or selected) keys of a chain."""
    chain = registry.get(args.chain)
    if chain is None:
        print(f"error: chain {args.chain!r} not found")
        return 1

    vars_ = dict(chain.vars)
    keys = args.keys if args.keys else None
    pipeline: List[str] = args.transforms

    try:
        transformed = transform_vars(vars_, pipeline, keys=keys)
    except TransformError as exc:
        print(f"error: {exc}")
        return 1

    if args.format == "json":
        print(json.dumps(transformed, indent=2))
    else:
        for k, v in sorted(transformed.items()):
            print(f"{k}={v}")
    return 0


def cmd_transform_list(_args: argparse.Namespace) -> int:
    """List all available built-in transforms."""
    for name in available_transforms():
        print(name)
    return 0


def build_transform_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("transform", help="Apply value transforms")
    sp = p.add_subparsers(dest="transform_cmd")

    # transform value
    pv = sp.add_parser("value", help="Transform a single value")
    pv.add_argument("value", help="The value to transform")
    pv.add_argument("transforms", nargs="+", help="Transform names in order")

    # transform chain
    pc = sp.add_parser("chain", help="Transform vars in a chain")
    pc.add_argument("chain", help="Chain name")
    pc.add_argument("transforms", nargs="+", help="Transform names in order")
    pc.add_argument("--keys", nargs="+", default=[], help="Limit to specific keys")
    pc.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )

    # transform list
    sp.add_parser("list", help="List available transforms")
