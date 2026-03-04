"""Tests for forge.blackboard — Blackboard inter-agent communication."""

from __future__ import annotations

import pytest

from forge.blackboard import Blackboard, BlackboardEntry


class TestBlackboard:
    """Tests for Blackboard read/write operations."""

    def test_put_get_works(self) -> None:
        """Blackboard put/get round-trip works."""
        bb = Blackboard()
        bb.put("stress", 250.0)
        assert bb.get("stress") == 250.0

    def test_get_missing_key_returns_none(self) -> None:
        """Blackboard returns None for missing key."""
        bb = Blackboard()
        assert bb.get("nonexistent") is None

    def test_has_works(self) -> None:
        """Blackboard.has() returns correct boolean."""
        bb = Blackboard()
        assert bb.has("key") is False
        bb.put("key", "value")
        assert bb.has("key") is True

    def test_keys_returns_all_keys(self) -> None:
        """Blackboard.keys() returns all keys."""
        bb = Blackboard()
        bb.put("a", 1)
        bb.put("b", 2)
        bb.put("c", 3)
        assert sorted(bb.keys()) == ["a", "b", "c"]

    def test_clear_empties_store(self) -> None:
        """Blackboard.clear() empties the store."""
        bb = Blackboard()
        bb.put("x", 10)
        bb.put("y", 20)
        assert len(bb.keys()) == 2
        bb.clear()
        assert len(bb.keys()) == 0
        assert bb.get("x") is None

    def test_snapshot_returns_all_values(self) -> None:
        """Blackboard.snapshot() returns all values as a dict."""
        bb = Blackboard()
        bb.put("temp", 300.0)
        bb.put("pressure", 101.3)
        snap = bb.snapshot()
        assert snap == {"temp": 300.0, "pressure": 101.3}

    def test_entry_stores_metadata(self) -> None:
        """BlackboardEntry stores written_by and timestamp."""
        bb = Blackboard()
        bb.put("result", 42, written_by="E-01")
        entry = bb.get_entry("result")
        assert entry is not None
        assert isinstance(entry, BlackboardEntry)
        assert entry.written_by == "E-01"
        assert entry.timestamp  # non-empty ISO string
        assert entry.key == "result"
        assert entry.value == 42
