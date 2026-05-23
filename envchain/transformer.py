"""Value transformation pipeline for environment variable chains."""

from __future__ import annotations

from typing import Callable, Dict, List


class TransformError(Exception):
    """Raised when a transformation fails."""


_BUILTIN: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "reverse": lambda v: v[::-1],
    "base64encode": lambda v: __import__("base64").b64encode(v.encode()).decode(),
    "base64decode": lambda v: __import__("base64").b64decode(v.encode()).decode(),
    "urlencode": lambda v: __import__("urllib.parse", fromlist=["quote"]).quote(v, safe=""),
    "urldecode": lambda v: __import__("urllib.parse", fromlist=["unquote"]).unquote(v),
    "trim_quotes": lambda v: v.strip("'\")"),
}


def available_transforms() -> List[str]:
    """Return sorted list of built-in transform names."""
    return sorted(_BUILTIN.keys())


def apply_transform(value: str, name: str) -> str:
    """Apply a single named transform to *value*.

    Raises TransformError if the transform name is unknown.
    """
    if name not in _BUILTIN:
        raise TransformError(
            f"Unknown transform {name!r}. Available: {available_transforms()}"
        )
    try:
        return _BUILTIN[name](value)
    except Exception as exc:  # noqa: BLE001
        raise TransformError(f"Transform {name!r} failed: {exc}") from exc


def apply_pipeline(value: str, pipeline: List[str]) -> str:
    """Apply a sequence of transforms in order, returning the final value."""
    result = value
    for name in pipeline:
        result = apply_transform(result, name)
    return result


def transform_vars(
    vars_: Dict[str, str],
    pipeline: List[str],
    keys: List[str] | None = None,
) -> Dict[str, str]:
    """Return a new dict with the pipeline applied to selected (or all) keys.

    If *keys* is None every key is transformed.
    """
    target_keys = set(keys) if keys is not None else set(vars_)
    return {
        k: apply_pipeline(v, pipeline) if k in target_keys else v
        for k, v in vars_.items()
    }
