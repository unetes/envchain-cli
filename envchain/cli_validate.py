"""CLI commands for validating chains and variable sets."""

import json
import sys
from typing import Optional

from envchain.validator import (
    validate_chain_name,
    validate_vars,
    validate_no_circular,
    ValidationError,
)


def cmd_validate_chain(name: str, parent: Optional[str], registry) -> int:
    """Validate a chain name and its proposed parent.

    Args:
        name: Chain name to validate.
        parent: Optional parent chain name.
        registry: ChainRegistry instance used for circular-dependency check.

    Returns:
        Exit code (0 = success, 1 = failure).
    """
    try:
        validate_chain_name(name)
        if parent is not None:
            validate_chain_name(parent)
            existing = {n: registry.get(n) for n in registry.list()}
            validate_no_circular(name, parent, existing)
        print(f"Chain '{name}' is valid.")
        return 0
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1


def cmd_validate_vars(source: str, fmt: str = "dotenv") -> int:
    """Validate a set of environment variables from a string or file path.

    Args:
        source: Raw content string or path to a file containing variables.
        fmt: Format hint — 'json' or 'dotenv'.

    Returns:
        Exit code (0 = success, 1 = failure).
    """
    try:
        # Try treating source as a file path first
        try:
            with open(source, "r", encoding="utf-8") as fh:
                content = fh.read()
        except (OSError, FileNotFoundError):
            content = source

        if fmt == "json":
            try:
                vars_dict = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Invalid JSON: {exc}") from exc
            if not isinstance(vars_dict, dict):
                raise ValidationError("JSON content must be an object/dict.")
        else:
            from envchain.importer import parse_dotenv_string
            vars_dict = parse_dotenv_string(content)

        validate_vars(vars_dict)
        print(f"All {len(vars_dict)} variable(s) are valid.")
        return 0
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1
