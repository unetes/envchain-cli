"""Lint environment variable chains for common issues and best practices."""

from dataclasses import dataclass, field
from typing import List, Optional
from envchain.registry import ChainRegistry


@dataclass
class LintIssue:
    chain: str
    key: Optional[str]
    level: str  # 'error' | 'warning' | 'info'
    code: str
    message: str

    def __str__(self) -> str:
        loc = f"{self.chain}:{self.key}" if self.key else self.chain
        return f"[{self.level.upper()}] {loc} ({self.code}): {self.message}"


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.level == "warning" for i in self.issues)

    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.level == "warning"]


def lint_chain(chain_name: str, registry: ChainRegistry) -> LintReport:
    """Lint a single chain and return a LintReport."""
    report = LintReport()
    chain = registry.get(chain_name)
    if chain is None:
        report.issues.append(LintIssue(
            chain=chain_name, key=None, level="error",
            code="E001", message=f"Chain '{chain_name}' does not exist."
        ))
        return report

    vars_ = chain.vars

    if not vars_:
        report.issues.append(LintIssue(
            chain=chain_name, key=None, level="warning",
            code="W001", message="Chain has no variables defined."
        ))

    for key, value in vars_.items():
        if value == "":
            report.issues.append(LintIssue(
                chain=chain_name, key=key, level="warning",
                code="W002", message=f"Variable '{key}' has an empty value."
            ))
        if key != key.upper():
            report.issues.append(LintIssue(
                chain=chain_name, key=key, level="info",
                code="I001", message=f"Variable '{key}' is not uppercase (convention)."
            ))
        if len(value) > 1024:
            report.issues.append(LintIssue(
                chain=chain_name, key=key, level="warning",
                code="W003", message=f"Variable '{key}' value exceeds 1024 characters."
            ))

    return report


def lint_registry(registry: ChainRegistry) -> dict:
    """Lint all chains in the registry. Returns dict of chain_name -> LintReport."""
    results = {}
    for name in registry.list():
        results[name] = lint_chain(name, registry)
    return results
