"""
forge_agent/tests/test_librarian.py

Tests for LibrarianAgent: intake, amnesia_check, retrieve, detect_gaps.
"""
from __future__ import annotations

import pytest

from forge_agent.agents.librarian import LibrarianAgent
from forge_agent.memory.obsidian_manager import ObsidianVaultManager


@pytest.fixture()
def vault_manager(tmp_path):
    return ObsidianVaultManager(vault_path=tmp_path)


@pytest.fixture()
def librarian(vault_manager):
    return LibrarianAgent(vault_manager)


_NOTE = {
    "project": "phoenix",
    "component": "heat_exchanger",
    "domain": "thermal",
    "trace_id": "trace-001",
    "confidence": 0.92,
    "content": "Wall temperature stabilised at 450 K under nominal flow.",
}


def test_intake_returns_path(librarian):
    result = librarian.intake(_NOTE)
    assert isinstance(result, str)
    assert result.endswith(".md")
    assert "phoenix" in result
    assert "heat_exchanger" in result
    assert "trace-001" in result


def test_amnesia_check_returns_true_after_write(librarian):
    path = librarian.intake(_NOTE)
    assert librarian.amnesia_check(path) is True


def test_retrieve_finds_written_note(librarian):
    librarian.intake(_NOTE)
    results = librarian.retrieve(domain="thermal", component="heat_exchanger")
    assert len(results) > 0
    first = results[0]
    assert first["frontmatter"].get("component") == "heat_exchanger"
    assert first["frontmatter"].get("domain") == "thermal"


def test_detect_gaps_empty_blackboard(librarian):
    gaps = librarian.detect_gaps({})
    assert "no specialist output" in gaps
    assert "no FEA results" in gaps


def test_detect_gaps_complete_blackboard(librarian):
    blackboard = {
        "specialist.result": "ok",
        "tool_results.calculix": {"stress_max_mpa": 120},
        "verification.status": "pass",
    }
    gaps = librarian.detect_gaps(blackboard)
    assert gaps == []
