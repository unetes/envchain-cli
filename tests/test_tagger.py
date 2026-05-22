"""Tests for envchain.tagger."""

import pytest
from envchain.tagger import TagIndex, TagError


@pytest.fixture()
def idx():
    return TagIndex()


def test_add_tag_associates_chain(idx):
    idx.add_tag("dev", "backend")
    assert "dev" in idx.chains_for("backend")


def test_tags_for_chain_returns_sorted(idx):
    idx.add_tag("dev", "zebra")
    idx.add_tag("dev", "alpha")
    assert idx.tags_for("dev") == ["alpha", "zebra"]


def test_chains_for_tag_returns_sorted(idx):
    idx.add_tag("dev", "backend")
    idx.add_tag("staging", "backend")
    result = idx.chains_for("backend")
    assert result == ["dev", "staging"]


def test_remove_tag_disassociates_chain(idx):
    idx.add_tag("dev", "backend")
    idx.remove_tag("dev", "backend")
    assert "dev" not in idx.chains_for("backend")


def test_remove_tag_cleans_empty_entry(idx):
    idx.add_tag("dev", "backend")
    idx.remove_tag("dev", "backend")
    assert "backend" not in idx.all_tags()


def test_remove_tag_silently_ignores_missing(idx):
    idx.remove_tag("dev", "nonexistent")  # should not raise


def test_empty_tag_raises(idx):
    with pytest.raises(TagError):
        idx.add_tag("dev", "")


def test_whitespace_only_tag_raises(idx):
    with pytest.raises(TagError):
        idx.add_tag("dev", "   ")


def test_tag_normalised_to_lowercase(idx):
    idx.add_tag("dev", "Backend")
    assert "backend" in idx.all_tags()


def test_all_tags_returns_sorted(idx):
    idx.add_tag("dev", "zebra")
    idx.add_tag("dev", "alpha")
    assert idx.all_tags() == ["alpha", "zebra"]


def test_remove_chain_clears_all_tags(idx):
    idx.add_tag("dev", "backend")
    idx.add_tag("dev", "service")
    idx.remove_chain("dev")
    assert idx.tags_for("dev") == []
    assert "backend" not in idx.all_tags()


def test_filter_chains_intersection(idx):
    idx.add_tag("dev", "backend")
    idx.add_tag("dev", "python")
    idx.add_tag("staging", "backend")
    result = idx.filter_chains(["backend", "python"])
    assert result == ["dev"]


def test_filter_chains_empty_tags_returns_empty(idx):
    idx.add_tag("dev", "backend")
    assert idx.filter_chains([]) == []


def test_filter_chains_no_match_returns_empty(idx):
    idx.add_tag("dev", "backend")
    assert idx.filter_chains(["backend", "nonexistent"]) == []
