"""Diff utilities for comparing environment variable chains."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'modified', 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None


@dataclass
class ChainDiff:
    chain_name: str
    added: List[DiffEntry] = field(default_factory=list)
    removed: List[DiffEntry] = field(default_factory=list)
    modified: List[DiffEntry] = field(default_factory=list)
    unchanged: List[DiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    @property
    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.modified:
            parts.append(f"~{len(self.modified)} modified")
        if not parts:
            return "no changes"
        return ", ".join(parts)


def diff_vars(
    chain_name: str,
    old_vars: Dict[str, str],
    new_vars: Dict[str, str],
    include_unchanged: bool = False,
) -> ChainDiff:
    """Compute a diff between two sets of environment variables."""
    result = ChainDiff(chain_name=chain_name)
    all_keys = set(old_vars) | set(new_vars)

    for key in sorted(all_keys):
        in_old = key in old_vars
        in_new = key in new_vars

        if in_old and in_new:
            if old_vars[key] != new_vars[key]:
                result.modified.append(
                    DiffEntry(key=key, status="modified",
                              old_value=old_vars[key], new_value=new_vars[key])
                )
            elif include_unchanged:
                result.unchanged.append(
                    DiffEntry(key=key, status="unchanged",
                              old_value=old_vars[key], new_value=new_vars[key])
                )
        elif in_new:
            result.added.append(
                DiffEntry(key=key, status="added", new_value=new_vars[key])
            )
        else:
            result.removed.append(
                DiffEntry(key=key, status="removed", old_value=old_vars[key])
            )

    return result


def format_diff(diff: ChainDiff, show_values: bool = True) -> str:
    """Format a ChainDiff as a human-readable string."""
    lines = [f"Chain: {diff.chain_name} — {diff.summary}"]
    for entry in diff.added:
        val = f" = {entry.new_value}" if show_values else ""
        lines.append(f"  + {entry.key}{val}")
    for entry in diff.removed:
        val = f" = {entry.old_value}" if show_values else ""
        lines.append(f"  - {entry.key}{val}")
    for entry in diff.modified:
        if show_values:
            lines.append(f"  ~ {entry.key}: {entry.old_value!r} -> {entry.new_value!r}")
        else:
            lines.append(f"  ~ {entry.key}")
    return "\n".join(lines)
