"""CLI commands for rendering chain variable templates."""

import argparse
import sys
from typing import List, Optional

from envchain.chain import resolve
from envchain.registry import ChainRegistry
from envchain.templater import TemplateError, has_template_syntax, render_vars


def cmd_template_render(
    args: argparse.Namespace,
    registry: ChainRegistry,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Render template variables for a chain and print the result.

    Returns 0 on success, 1 on error.
    """
    chain = registry.get(args.chain)
    if chain is None:
        err.write(f"error: chain '{args.chain}' not found\n")
        return 1

    resolved = resolve(chain, registry)
    try:
        rendered = render_vars(resolved, strict=not args.lenient)
    except TemplateError as exc:
        err.write(f"error: {exc}\n")
        return 1

    for key, value in sorted(rendered.items()):
        marker = " [t]" if has_template_syntax(chain.vars.get(key, "")) else ""
        out.write(f"{key}={value}{marker}\n")
    return 0


def cmd_template_check(
    args: argparse.Namespace,
    registry: ChainRegistry,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Check whether a chain has any template variables and list them.

    Returns 0 if templates found, 1 if none, 2 on error.
    """
    chain = registry.get(args.chain)
    if chain is None:
        err.write(f"error: chain '{args.chain}' not found\n")
        return 2

    template_keys = [k for k, v in chain.vars.items() if has_template_syntax(v)]
    if not template_keys:
        out.write(f"No template variables found in chain '{args.chain}'.\n")
        return 1

    out.write(f"Template variables in '{args.chain}':\n")
    for key in sorted(template_keys):
        out.write(f"  {key} = {chain.vars[key]}\n")
    return 0


def build_template_parser(subparsers) -> None:
    """Register template sub-commands onto the provided subparsers action."""
    p_render = subparsers.add_parser("render", help="Render template vars for a chain")
    p_render.add_argument("chain", help="Chain name")
    p_render.add_argument(
        "--lenient", action="store_true", help="Leave unresolved vars as-is"
    )
    p_render.set_defaults(func=cmd_template_render)

    p_check = subparsers.add_parser("check", help="List template vars in a chain")
    p_check.add_argument("chain", help="Chain name")
    p_check.set_defaults(func=cmd_template_check)
