"""Redactor: mask or strip sensitive variable values in output."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

DEFAULT_MASK = "***"
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)", re.I),
]


class RedactError(Exception):
    """Raised when redaction configuration is invalid."""


def is_sensitive_key(key: str, extra_patterns: Optional[Iterable[str]] = None) -> bool:
    """Return True if *key* looks like it holds a sensitive value."""
    patterns = list(_SENSITIVE_PATTERNS)
    for pat in extra_patterns or []:
        patterns.append(re.compile(pat, re.I))
    return any(p.search(key) for p in patterns)


def redact_value(value: str, mask: str = DEFAULT_MASK) -> str:
    """Return *mask* unconditionally — used when caller decides to redact."""
    if not mask:
        raise RedactError("mask must be a non-empty string")
    return mask


def redact_vars(
    vars_: Dict[str, str],
    *,
    keys: Optional[Iterable[str]] = None,
    auto_detect: bool = True,
    extra_patterns: Optional[Iterable[str]] = None,
    mask: str = DEFAULT_MASK,
) -> Dict[str, str]:
    """Return a copy of *vars_* with sensitive values replaced by *mask*.

    If *keys* is provided those keys are always redacted.
    If *auto_detect* is True, keys matching built-in (and *extra_patterns*)
    sensitivity heuristics are also redacted.
    """
    explicit = set(keys or [])
    result: Dict[str, str] = {}
    for k, v in vars_.items():
        should_redact = k in explicit or (
            auto_detect and is_sensitive_key(k, extra_patterns)
        )
        result[k] = redact_value(v, mask) if should_redact else v
    return result


def strip_sensitive(
    vars_: Dict[str, str],
    *,
    keys: Optional[Iterable[str]] = None,
    auto_detect: bool = True,
    extra_patterns: Optional[Iterable[str]] = None,
) -> Dict[str, str]:
    """Return a copy of *vars_* with sensitive keys removed entirely."""
    explicit = set(keys or [])
    return {
        k: v
        for k, v in vars_.items()
        if k not in explicit
        and not (auto_detect and is_sensitive_key(k, extra_patterns))
    }
