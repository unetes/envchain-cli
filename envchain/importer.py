"""Import environment variables into a chain from common file formats."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Union

_DOTENV_LINE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)\s*$"
)


def load_vars(source: Union[str, Path], fmt: str = "auto") -> Dict[str, str]:
    """Read variables from *source* and return them as a plain dict.

    Args:
        source: Path to the file to read.
        fmt:    ``auto``, ``dotenv``, or ``json``.

    Returns:
        Dictionary mapping variable names to string values.

    Raises:
        ValueError: If the format cannot be detected or the file is malformed.
    """
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    detected = fmt
    if detected == "auto":
        detected = _detect_format(path)

    text = path.read_text(encoding="utf-8")

    if detected == "json":
        return _parse_json(text)
    return _parse_dotenv(text)


def parse_dotenv_string(text: str) -> Dict[str, str]:
    """Parse a dotenv-formatted string without touching the filesystem."""
    return _parse_dotenv(text)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_format(path: Path) -> str:
    if path.suffix == ".json":
        return "json"
    return "dotenv"


def _parse_json(text: str) -> Dict[str, str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return {str(k): str(v) for k, v in data.items()}


def _parse_dotenv(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _DOTENV_LINE.match(line)
        if not m:
            raise ValueError(f"Malformed dotenv line {lineno}: {raw!r}")
        key = m.group("key")
        value = m.group("value")
        # Strip optional surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result
