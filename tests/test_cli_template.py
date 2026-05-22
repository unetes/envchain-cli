"""Tests for envchain.cli_template module."""

import argparse
import io

import pytest

from envchain.chain import Chain
from envchain.cli_template import cmd_template_check, cmd_template_render
from envchain.registry import ChainRegistry


def _make_registry(*chains: Chain) -> ChainRegistry:
    reg = ChainRegistry()
    for chain in chains:
        reg.add(chain)
    return reg


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"chain": "dev", "lenient": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# cmd_template_render
# ---------------------------------------------------------------------------

def test_render_returns_0_on_success():
    chain = Chain(name="dev", vars={"HOST": "localhost", "URL": "${HOST}:8080"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_template_render(_make_args(chain="dev"), reg, out, err)
    assert rc == 0


def test_render_output_contains_rendered_value():
    chain = Chain(name="dev", vars={"HOST": "localhost", "URL": "${HOST}:8080"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    cmd_template_render(_make_args(chain="dev"), reg, out, err)
    assert "URL=localhost:8080" in out.getvalue()


def test_render_marks_template_keys():
    chain = Chain(name="dev", vars={"HOST": "localhost", "URL": "${HOST}:8080"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    cmd_template_render(_make_args(chain="dev"), reg, out, err)
    assert "[t]" in out.getvalue()


def test_render_returns_1_for_missing_chain():
    reg = _make_registry()
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_template_render(_make_args(chain="ghost"), reg, out, err)
    assert rc == 1
    assert "not found" in err.getvalue()


def test_render_returns_1_on_unresolved_strict():
    chain = Chain(name="dev", vars={"URL": "${UNDEFINED_VAR}"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_template_render(_make_args(chain="dev", lenient=False), reg, out, err)
    assert rc == 1


def test_render_lenient_returns_0_on_unresolved():
    chain = Chain(name="dev", vars={"URL": "${UNDEFINED_VAR}"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_template_render(_make_args(chain="dev", lenient=True), reg, out, err)
    assert rc == 0


# ---------------------------------------------------------------------------
# cmd_template_check
# ---------------------------------------------------------------------------

def test_check_returns_0_when_templates_found():
    chain = Chain(name="dev", vars={"URL": "${HOST}:8080"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_template_check(_make_args(chain="dev"), reg, out, err)
    assert rc == 0


def test_check_returns_1_when_no_templates():
    chain = Chain(name="dev", vars={"HOST": "localhost"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_template_check(_make_args(chain="dev"), reg, out, err)
    assert rc == 1


def test_check_returns_2_for_missing_chain():
    reg = _make_registry()
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_template_check(_make_args(chain="ghost"), reg, out, err)
    assert rc == 2


def test_check_lists_template_keys_in_output():
    chain = Chain(name="dev", vars={"URL": "${HOST}:8080", "PLAIN": "value"})
    reg = _make_registry(chain)
    out, err = io.StringIO(), io.StringIO()
    cmd_template_check(_make_args(chain="dev"), reg, out, err)
    assert "URL" in out.getvalue()
    assert "PLAIN" not in out.getvalue()
