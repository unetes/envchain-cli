"""Key rotation: generate new values for specified keys across chains."""
from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class RotateError(Exception):
    """Raised when key rotation fails."""


_DEFAULT_ALPHABET = string.ascii_letters + string.digits
_DEFAULT_LENGTH = 32


def _default_generator(length: int = _DEFAULT_LENGTH) -> str:
    """Generate a cryptographically secure random string."""
    return "".join(secrets.choice(_DEFAULT_ALPHABET) for _ in range(length))


@dataclass
class RotateEntry:
    chain_name: str
    key: str
    old_value: str
    new_value: str

    def to_dict(self) -> dict:
        return {
            "chain": self.chain_name,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class RotateReport:
    entries: List[RotateEntry] = field(default_factory=list)

    @property
    def total_rotated(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        if not self.entries:
            return "No keys rotated."
        lines = [f"Rotated {self.total_rotated} key(s):"]
        for e in self.entries:
            lines.append(f"  {e.chain_name}.{e.key}")
        return "\n".join(lines)


def rotate_keys(
    registry,
    chain_name: str,
    keys: List[str],
    generator: Optional[Callable[[], str]] = None,
    dry_run: bool = False,
) -> RotateReport:
    """Rotate the given keys in *chain_name*, replacing values with generated ones."""
    chain = registry.get(chain_name)
    if chain is None:
        raise RotateError(f"Chain '{chain_name}' not found.")

    gen = generator or _default_generator
    report = RotateReport()

    for key in keys:
        if key not in chain.vars:
            raise RotateError(f"Key '{key}' not found in chain '{chain_name}'.")
        old_val = chain.vars[key]
        new_val = gen()
        entry = RotateEntry(
            chain_name=chain_name,
            key=key,
            old_value=old_val,
            new_value=new_val,
        )
        report.entries.append(entry)
        if not dry_run:
            chain.vars[key] = new_val

    return report
