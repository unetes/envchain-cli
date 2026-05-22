"""Validation utilities for environment variable chains."""

import re
from typing import Optional

KEY_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
CHAIN_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_\-\.]*$')


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_key(key: str) -> None:
    """Validate an environment variable key.

    Args:
        key: The variable name to validate.

    Raises:
        ValidationError: If the key is not a valid identifier.
    """
    if not key:
        raise ValidationError("Variable key must not be empty.")
    if not KEY_PATTERN.match(key):
        raise ValidationError(
            f"Invalid variable key '{key}': must start with a letter or "
            f"underscore and contain only letters, digits, or underscores."
        )


def validate_chain_name(name: str) -> None:
    """Validate a chain name.

    Args:
        name: The chain name to validate.

    Raises:
        ValidationError: If the name contains invalid characters.
    """
    if not name:
        raise ValidationError("Chain name must not be empty.")
    if not CHAIN_NAME_PATTERN.match(name):
        raise ValidationError(
            f"Invalid chain name '{name}': must start with a letter or digit "
            f"and contain only letters, digits, underscores, hyphens, or dots."
        )


def validate_vars(vars_dict: dict) -> None:
    """Validate a dictionary of environment variables.

    Args:
        vars_dict: Mapping of variable names to values.

    Raises:
        ValidationError: If any key is invalid.
    """
    for key, value in vars_dict.items():
        validate_key(key)
        if not isinstance(value, str):
            raise ValidationError(
                f"Value for '{key}' must be a string, got {type(value).__name__}."
            )


def validate_no_circular(name: str, parent: Optional[str], existing_chains: dict) -> None:
    """Check that adding a parent to a chain would not create a cycle.

    Args:
        name: The chain being updated.
        parent: The proposed parent chain name.
        existing_chains: Mapping of chain name -> Chain object with .parent attribute.

    Raises:
        ValidationError: If a circular dependency would be introduced.
    """
    visited = set()
    current = parent
    while current is not None:
        if current == name:
            raise ValidationError(
                f"Circular inheritance detected: '{name}' cannot inherit from '{parent}'."
            )
        if current in visited:
            break
        visited.add(current)
        chain = existing_chains.get(current)
        current = chain.parent if chain else None
