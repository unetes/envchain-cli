"""CSV export/import support for envchain chains."""
from __future__ import annotations

import csv
import io
from typing import Dict, List, Optional


class CsvError(Exception):
    """Raised when CSV parsing or export fails."""


def export_csv(
    chain_name: str,
    variables: Dict[str, str],
    *,
    include_header: bool = True,
    delimiter: str = ",",
) -> str:
    """Serialise *variables* to a CSV string.

    Each row contains ``chain``, ``key``, ``value`` columns.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
    if include_header:
        writer.writerow(["chain", "key", "value"])
    for key, value in sorted(variables.items()):
        writer.writerow([chain_name, key, value])
    return buf.getvalue()


def parse_csv(
    text: str,
    *,
    delimiter: str = ",",
    expected_chain: Optional[str] = None,
) -> Dict[str, Dict[str, str]]:
    """Parse a CSV string produced by :func:`export_csv`.

    Returns a mapping of ``{chain_name: {key: value}}``.
    Raises :class:`CsvError` on malformed rows.
    """
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    result: Dict[str, Dict[str, str]] = {}
    header_skipped = False

    for lineno, row in enumerate(reader, start=1):
        if not row or all(cell.strip() == "" for cell in row):
            continue
        if not header_skipped and row == ["chain", "key", "value"]:
            header_skipped = True
            continue
        if len(row) != 3:
            raise CsvError(
                f"Line {lineno}: expected 3 columns, got {len(row)}"
            )
        chain, key, value = row
        if expected_chain and chain != expected_chain:
            raise CsvError(
                f"Line {lineno}: chain '{chain}' does not match expected '{expected_chain}'"
            )
        result.setdefault(chain, {})[key] = value

    return result


def export_multi_csv(
    chains: Dict[str, Dict[str, str]],
    *,
    delimiter: str = ",",
) -> str:
    """Export multiple chains into a single CSV document."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["chain", "key", "value"])
    for chain_name in sorted(chains):
        for key in sorted(chains[chain_name]):
            writer.writerow([chain_name, key, chains[chain_name][key]])
    return buf.getvalue()
