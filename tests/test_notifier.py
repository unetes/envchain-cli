"""Tests for envchain.notifier."""

import pytest

from envchain.notifier import NotifierError, NotifierIndex, NotifyEvent


# ---------------------------------------------------------------------------
# NotifyEvent
# ---------------------------------------------------------------------------

def test_event_str_contains_event_type():
    ev = NotifyEvent(event_type="key_set", chain="dev")
    assert "key_set" in str(ev)


def test_event_str_contains_chain():
    ev = NotifyEvent(event_type="chain_created", chain="staging")
    assert "staging" in str(ev)


def test_event_str_contains_key_when_present():
    ev = NotifyEvent(event_type="key_set", chain="dev", key="API_KEY")
    assert "API_KEY" in str(ev)


def test_event_str_omits_key_when_absent():
    ev = NotifyEvent(event_type="chain_created", chain="dev")
    assert "key=" not in str(ev)


def test_event_to_dict_has_required_keys():
    ev = NotifyEvent(event_type="key_set", chain="dev", key="X")
    d = ev.to_dict()
    assert set(d) >= {"event_type", "chain", "key", "meta"}


# ---------------------------------------------------------------------------
# NotifierIndex — register / unregister
# ---------------------------------------------------------------------------

def test_register_adds_hook():
    idx = NotifierIndex()
    idx.register("slack", lambda e: None)
    assert "slack" in idx.hook_names()


def test_register_empty_name_raises():
    idx = NotifierIndex()
    with pytest.raises(NotifierError):
        idx.register("", lambda e: None)


def test_unregister_removes_hook():
    idx = NotifierIndex()
    idx.register("slack", lambda e: None)
    idx.unregister("slack")
    assert "slack" not in idx.hook_names()


def test_unregister_unknown_raises():
    idx = NotifierIndex()
    with pytest.raises(NotifierError):
        idx.unregister("ghost")


def test_hook_names_sorted():
    idx = NotifierIndex()
    idx.register("z_hook", lambda e: None)
    idx.register("a_hook", lambda e: None)
    assert idx.hook_names() == ["a_hook", "z_hook"]


# ---------------------------------------------------------------------------
# NotifierIndex — dispatch
# ---------------------------------------------------------------------------

def test_dispatch_calls_hook():
    received = []
    idx = NotifierIndex()
    idx.register("capture", lambda e: received.append(e))
    ev = NotifyEvent(event_type="key_set", chain="dev", key="TOKEN")
    idx.dispatch(ev)
    assert len(received) == 1
    assert received[0] is ev


def test_dispatch_calls_multiple_hooks():
    counts = {"a": 0, "b": 0}
    idx = NotifierIndex()
    idx.register("a", lambda e: counts.__setitem__("a", counts["a"] + 1))
    idx.register("b", lambda e: counts.__setitem__("b", counts["b"] + 1))
    idx.dispatch(NotifyEvent(event_type="chain_created", chain="prod"))
    assert counts["a"] == 1
    assert counts["b"] == 1


def test_dispatch_returns_failed_hook_names():
    def bad_hook(e):
        raise RuntimeError("boom")

    idx = NotifierIndex()
    idx.register("bad", bad_hook)
    failed = idx.dispatch(NotifyEvent(event_type="key_set", chain="dev"))
    assert "bad" in failed


def test_dispatch_continues_after_hook_failure():
    received = []
    idx = NotifierIndex()
    idx.register("a_bad", lambda e: (_ for _ in ()).throw(RuntimeError()))
    idx.register("b_good", lambda e: received.append(True))
    idx.dispatch(NotifyEvent(event_type="key_set", chain="dev"))
    assert received == [True]


def test_dispatch_no_hooks_returns_empty_list():
    idx = NotifierIndex()
    result = idx.dispatch(NotifyEvent(event_type="chain_deleted", chain="old"))
    assert result == []
