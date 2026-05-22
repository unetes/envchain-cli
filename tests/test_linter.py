"""Tests for envchain.linter module."""

import pytest
from envchain.linter import lint_chain, lint_registry, LintIssue, LintReport
from envchain.registry import ChainRegistry
from envchain.chain import Chain


def _make_registry(chains: dict) -> ChainRegistry:
    reg = ChainRegistry()
    for name, data in chains.items():
        reg.add(Chain(name=name, parent=data.get("parent"), vars=data.get("vars", {})))
    return reg


def test_lint_report_has_errors_false_when_empty():
    report = LintReport()
    assert not report.has_errors()


def test_lint_report_has_errors_true():
    report = LintReport(issues=[
        LintIssue(chain="x", key=None, level="error", code="E001", message="oops")
    ])
    assert report.has_errors()


def test_lint_report_errors_filters_correctly():
    report = LintReport(issues=[
        LintIssue(chain="x", key=None, level="error", code="E001", message="e"),
        LintIssue(chain="x", key=None, level="warning", code="W001", message="w"),
    ])
    assert len(report.errors()) == 1
    assert len(report.warnings()) == 1


def test_lint_issue_str_with_key():
    issue = LintIssue(chain="prod", key="DB_URL", level="warning", code="W002", message="empty")
    assert "prod:DB_URL" in str(issue)
    assert "W002" in str(issue)


def test_lint_issue_str_without_key():
    issue = LintIssue(chain="prod", key=None, level="error", code="E001", message="missing")
    assert "prod" in str(issue)
    assert "prod:" not in str(issue)


def test_lint_nonexistent_chain_returns_error():
    reg = _make_registry({})
    report = lint_chain("ghost", reg)
    assert report.has_errors()
    assert any(i.code == "E001" for i in report.issues)


def test_lint_empty_chain_returns_warning():
    reg = _make_registry({"base": {"vars": {}}})
    report = lint_chain("base", reg)
    assert report.has_warnings()
    assert any(i.code == "W001" for i in report.issues)


def test_lint_empty_value_returns_warning():
    reg = _make_registry({"base": {"vars": {"API_KEY": ""}}})
    report = lint_chain("base", reg)
    assert any(i.code == "W002" for i in report.issues)


def test_lint_lowercase_key_returns_info():
    reg = _make_registry({"base": {"vars": {"api_key": "secret"}}})
    report = lint_chain("base", reg)
    assert any(i.code == "I001" for i in report.issues)


def test_lint_uppercase_key_no_info():
    reg = _make_registry({"base": {"vars": {"API_KEY": "secret"}}})
    report = lint_chain("base", reg)
    assert not any(i.code == "I001" for i in report.issues)


def test_lint_long_value_returns_warning():
    reg = _make_registry({"base": {"vars": {"BIG": "x" * 1025}}})
    report = lint_chain("base", reg)
    assert any(i.code == "W003" for i in report.issues)


def test_lint_registry_returns_all_chains():
    reg = _make_registry({
        "base": {"vars": {"A": "1"}},
        "prod": {"vars": {"B": "2"}},
    })
    results = lint_registry(reg)
    assert "base" in results
    assert "prod" in results


def test_lint_registry_empty_registry():
    reg = _make_registry({})
    results = lint_registry(reg)
    assert results == {}
