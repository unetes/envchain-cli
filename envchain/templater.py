"""Template rendering for environment variable values with chain variable substitution."""

import re
from typing import Dict, Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)")


def render_value(template: str, context: Dict[str, str], strict: bool = True) -> str:
    """Render a single template string using the provided context.

    Supports ${VAR_NAME} and $VAR_NAME syntax.

    Args:
        template: The template string to render.
        context: Dictionary of variable names to values.
        strict: If True, raise TemplateError for missing variables.

    Returns:
        The rendered string.

    Raises:
        TemplateError: If a referenced variable is missing and strict=True.
    """
    def replacer(match: re.Match) -> str:
        key = match.group(1) or match.group(2)
        if key in context:
            return context[key]
        if strict:
            raise TemplateError(f"Undefined variable '{key}' in template: {template!r}")
        return match.group(0)

    return _VAR_PATTERN.sub(replacer, template)


def render_vars(
    vars_: Dict[str, str],
    context: Optional[Dict[str, str]] = None,
    strict: bool = True,
) -> Dict[str, str]:
    """Render all values in a vars dict, using the vars themselves plus optional extra context.

    Args:
        vars_: The variables whose values may contain templates.
        context: Additional context variables (e.g. resolved parent chain vars).
        strict: Propagated to render_value.

    Returns:
        A new dict with all values rendered.
    """
    merged_context: Dict[str, str] = {}
    if context:
        merged_context.update(context)
    merged_context.update(vars_)

    return {key: render_value(value, merged_context, strict=strict) for key, value in vars_.items()}


def extract_variable_refs(template: str) -> list[str]:
    """Return a list of variable names referenced in the template string.

    Args:
        template: The template string to inspect.

    Returns:
        A list of unique variable names in the order they first appear.
    """
    seen: set[str] = set()
    refs: list[str] = []
    for match in _VAR_PATTERN.finditer(template):
        key = match.group(1) or match.group(2)
        if key not in seen:
            seen.add(key)
            refs.append(key)
    return refs


def has_template_syntax(value: str) -> bool:
    """Return True if the value contains template variable references."""
    return bool(_VAR_PATTERN.search(value))
