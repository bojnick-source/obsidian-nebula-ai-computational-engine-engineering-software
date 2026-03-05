"""Tests for EventConsumer and ForgeEvent schema."""

from __future__ import annotations

from datetime import datetime

import pytest

from forge_output.event_schema import EventType, ForgeEvent


def _make_event(**kwargs) -> dict:
    base = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "run_id": "run-0000-0001",
        "trace_id": "00000000-0000-4000-8000-000000000001",
        "event_type": "run_start",
    }
    base.update(kwargs)
    return base


def test_parse_run_start():
    event = ForgeEvent.from_dict(_make_event(event_type="run_start"))
    assert event.event_type == EventType.RUN_START


def test_parse_phase_start():
    event = ForgeEvent.from_dict(_make_event(event_type="phase_start", phase="specialist"))
    assert event.phase == "specialist"


def test_parse_token():
    event = ForgeEvent.from_dict(
        _make_event(event_type="token", agent="me_specialist", meta={"token": "hello"})
    )
    assert event.meta["token"] == "hello"


def test_meta_json_alias():
    """Wire format may send meta_json instead of meta."""
    raw = _make_event(event_type="progress", meta_json={"some": "data"})
    del raw["meta_json"]  # ensure only meta_json key present
    raw["meta_json"] = {"some": "data"}
    event = ForgeEvent.from_dict(raw)
    assert event.meta["some"] == "data"


def test_progress_clamp():
    """progress must be 0..1 — Pydantic should enforce."""
    with pytest.raises(Exception):
        ForgeEvent.from_dict(_make_event(event_type="progress", progress=1.5))


def test_unknown_event_type_rejected():
    with pytest.raises(Exception):
        ForgeEvent.from_dict(_make_event(event_type="not_a_real_event"))
