"""Tests for envchain.templater module."""

import pytest

from envchain.templater import (
    TemplateError,
    has_template_syntax,
    render_value,
    render_vars,
)


# ---------------------------------------------------------------------------
# render_value
# ---------------------------------------------------------------------------

def test_render_value_curly_brace_syntax():
    result = render_value("Hello, ${NAME}!", {"NAME": "world"})
    assert result == "Hello, world!"


def test_render_value_dollar_syntax():
    result = render_value("Hello, $NAME!", {"NAME": "world"})
    assert result == "Hello, world!"


def test_render_value_multiple_vars():
    result = render_value("${HOST}:${PORT}", {"HOST": "localhost", "PORT": "5432"})
    assert result == "localhost:5432"


def test_render_value_no_template_returns_unchanged():
    result = render_value("plain value", {})
    assert result == "plain value"


def test_render_value_strict_raises_on_missing():
    with pytest.raises(TemplateError, match="Undefined variable 'MISSING'"):
        render_value("${MISSING}", {}, strict=True)


def test_render_value_non_strict_keeps_original_on_missing():
    result = render_value("${MISSING}", {}, strict=False)
    assert result == "${MISSING}"


def test_render_value_partial_substitution_non_strict():
    result = render_value("${FOUND}-${MISSING}", {"FOUND": "ok"}, strict=False)
    assert result == "ok-${MISSING}"


# ---------------------------------------------------------------------------
# render_vars
# ---------------------------------------------------------------------------

def test_render_vars_self_referencing_context():
    vars_ = {"BASE": "/app", "DATA": "${BASE}/data"}
    result = render_vars(vars_)
    assert result["DATA"] == "/app/data"


def test_render_vars_uses_extra_context():
    vars_ = {"URL": "${SCHEME}://${HOST}"}
    context = {"SCHEME": "https", "HOST": "example.com"}
    result = render_vars(vars_, context=context)
    assert result["URL"] == "https://example.com"


def test_render_vars_own_vars_override_context():
    vars_ = {"KEY": "own", "OUT": "${KEY}"}
    context = {"KEY": "from_context"}
    result = render_vars(vars_, context=context)
    assert result["OUT"] == "own"


def test_render_vars_empty_returns_empty():
    assert render_vars({}) == {}


def test_render_vars_strict_raises_on_missing():
    with pytest.raises(TemplateError):
        render_vars({"A": "${UNDEFINED}"}, strict=True)


# ---------------------------------------------------------------------------
# has_template_syntax
# ---------------------------------------------------------------------------

def test_has_template_syntax_curly():
    assert has_template_syntax("${FOO}") is True


def test_has_template_syntax_dollar():
    assert has_template_syntax("$FOO") is True


def test_has_template_syntax_plain_false():
    assert has_template_syntax("just a plain value") is False


def test_has_template_syntax_empty_false():
    assert has_template_syntax("") is False
