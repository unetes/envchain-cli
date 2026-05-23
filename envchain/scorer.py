"""Chain health scorer — produces a numeric quality score for a chain."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envchain.linter import lint_chain, LintReport
from envchain.chain import Chain


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of a chain's health score."""
    chain_name: str
    base_score: int = 100
    deductions: List[tuple] = field(default_factory=list)  # (reason, points)
    bonuses: List[tuple] = field(default_factory=list)    # (reason, points)

    @property
    def final_score(self) -> int:
        total = self.base_score
        total -= sum(pts for _, pts in self.deductions)
        total += sum(pts for _, pts in self.bonuses)
        return max(0, min(100, total))

    @property
    def grade(self) -> str:
        s = self.final_score
        if s >= 90:
            return "A"
        if s >= 75:
            return "B"
        if s >= 60:
            return "C"
        if s >= 40:
            return "D"
        return "F"

    def summary(self) -> str:
        lines = [f"Chain '{self.chain_name}': {self.final_score}/100 ({self.grade})"]
        for reason, pts in self.deductions:
            lines.append(f"  -{pts:>3}  {reason}")
        for reason, pts in self.bonuses:
            lines.append(f"  +{pts:>3}  {reason}")
        return "\n".join(lines)


def score_chain(chain: Chain, registry=None) -> ScoreBreakdown:
    """Compute a health score for *chain*."""
    bd = ScoreBreakdown(chain_name=chain.name)

    report: LintReport = lint_chain(chain, registry=registry)

    error_count = len(report.errors())
    warning_count = len(report.warnings())

    if error_count:
        bd.deductions.append((f"{error_count} lint error(s)", min(50, error_count * 15)))
    if warning_count:
        bd.deductions.append((f"{warning_count} lint warning(s)", min(20, warning_count * 5)))

    vars_ = chain.vars
    if not vars_:
        bd.deductions.append(("chain has no variables", 20))
    elif len(vars_) >= 5:
        bd.bonuses.append(("good variable coverage (>=5 keys)", 5))

    if chain.parent:
        bd.bonuses.append(("inherits from parent chain", 3))

    return bd
