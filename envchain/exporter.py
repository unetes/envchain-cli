"""Export resolved environment variable chains to various formats."""

from __future__ import annotations

import json
import shlex
from typing import Dict, Literal

ExportFormat = Literal["env", "json", "shell", "dotenv"]


def export_vars(
    variables: Dict[str, str],
    fmt: ExportFormat = "env",
    *,
    chain_name: str = "",
) -> str:
    """Serialize resolved variables into the requested format.

    Args:
        variables: Mapping of variable names to their resolved values.
        fmt:       One of ``env``, ``json``, ``shell``, ``dotenv``.
        chain_name: Optional chain name used as a comment header.

    Returns:
        A string representation ready to be written to a file or stdout.
    """
    if fmt == "json":
        return _to_json(variables)
    if fmt == "shell":
        return _to_shell(variables, chain_name=chain_name)
    if fmt == "dotenv":
        return _to_dotenv(variables, chain_name=chain_name)
    # default: "env" — same as dotenv but no header
    return _to_dotenv(variables)


def _to_json(variables: Dict[str, str]) -> str:
    return json.dumps(variables, indent=2)


def _to_shell(variables: Dict[str, str], *, chain_name: str = "") -> str:
    lines = []
    if chain_name:
        lines.append(f"# envchain: {chain_name}")
    for key, value in sorted(variables.items()):
        quoted = shlex.quote(value)
        lines.append(f"export {key}={quoted}")
    return "\n".join(lines)


def _to_dotenv(variables: Dict[str, str], *, chain_name: str = "") -> str:
    lines = []
    if chain_name:
        lines.append(f"# envchain: {chain_name}")
    for key, value in sorted(variables.items()):
        # Escape double-quotes inside the value
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines)
