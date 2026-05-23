"""CLI commands for linting environment variable chains."""

import argparse
from envchain.linter import lint_chain, lint_registry
from envchain.registry import ChainRegistry


def cmd_lint(args: argparse.Namespace, registry: ChainRegistry) -> int:
    """
    Lint one or all chains. Returns exit code:
      0 = no issues (or only info)
      1 = warnings found
      2 = errors found
      3 = bad arguments
    """
    if not hasattr(args, "chain_name") or args.chain_name is None:
        results = lint_registry(registry)
        if not results:
            print("No chains found in registry.")
            return 0
    else:
        if args.chain_name not in registry:
            print(f"Error: chain '{args.chain_name}' not found in registry.")
            return 3
        report = lint_chain(args.chain_name, registry)
        results = {args.chain_name: report}

    total_issues = 0
    has_errors = False
    has_warnings = False

    for chain_name, report in results.items():
        for issue in report.issues:
            if args.errors_only and not issue.is_error():
                continue
            print(str(issue))
            total_issues += 1
        if report.has_errors():
            has_errors = True
        if report.has_warnings():
            has_warnings = True

    if total_issues == 0:
        chains = ", ".join(results.keys())
        print(f"OK: no issues found in chain(s): {chains}")

    if has_errors:
        return 2
    if has_warnings and not args.errors_only:
        return 1
    return 0


def build_lint_parser(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "lint",
        help="Lint chain(s) for common issues and best practices."
    )
    parser.add_argument(
        "chain_name",
        nargs="?",
        default=None,
        help="Name of the chain to lint. If omitted, all chains are linted."
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        default=False,
        help="Only report errors, suppress warnings and info."
    )
    parser.set_defaults(func=cmd_lint)
    return parser
