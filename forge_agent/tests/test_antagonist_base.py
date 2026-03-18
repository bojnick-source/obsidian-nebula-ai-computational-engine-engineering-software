"""Unit tests for AntagonistAgent base class (plan 4-001)."""
from __future__ import annotations

import pytest

from forge_agent.agents.antagonist_base import AntagonistAgent, VALID_SEVERITIES


# ---------------------------------------------------------------------------
# Minimal concrete subclass used throughout the test suite
# ---------------------------------------------------------------------------

class ConcreteAntagonist(AntagonistAgent):
    """Thin concrete subclass for testing. Accepts a `_return` dict to control output."""

    def __init__(self, return_dict: dict | None = None) -> None:
        super().__init__(agent_id="test_antagonist", domain="testing")
        self._return = return_dict or _valid_critique()

    def _generate_critique(self, specialist_output: dict, context: dict) -> dict:
        # Both params are consumed: store them so tests can inspect (P2 guard)
        self.last_specialist_output = specialist_output
        self.last_context = context
        return self._return


def _valid_critique(**overrides) -> dict:
    """Return a fully-valid critique dict, optionally overriding individual keys."""
    base = {
        "error_code": None,
        "critique_type": "factual",
        "severity": "warning",
        "detail": "This is a detailed critique explanation that is definitely fifty characters or more.",
        "evidence": "AISC 360-22 Section E3",
        "confidence_delta": -0.15,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_critique_returns_required_fields():
    """critique() must return a dict containing all 6 required keys."""
    agent = ConcreteAntagonist()
    result = agent.critique(specialist_output={}, context={})
    required_keys = {"error_code", "critique_type", "severity", "detail", "evidence", "confidence_delta"}
    assert required_keys == result.keys()


def test_severity_in_valid_set():
    """Each of the three valid severity values must be accepted without error."""
    for sev in ("fatal", "warning", "info"):
        agent = ConcreteAntagonist(return_dict=_valid_critique(severity=sev))
        result = agent.critique(specialist_output={}, context={})
        assert result["severity"] == sev
    assert VALID_SEVERITIES == {"fatal", "warning", "info"}


def test_invalid_severity_raises():
    """A severity value outside the allowed set must raise ValueError."""
    agent = ConcreteAntagonist(return_dict=_valid_critique(severity="critical"))
    with pytest.raises(ValueError, match="severity="):
        agent.critique(specialist_output={}, context={})


def test_confidence_delta_le_zero():
    """confidence_delta values of 0.0 and negative floats must both be accepted."""
    for delta in (0.0, -0.01, -1.0):
        agent = ConcreteAntagonist(return_dict=_valid_critique(confidence_delta=delta))
        result = agent.critique(specialist_output={}, context={})
        assert result["confidence_delta"] <= 0.0


def test_positive_confidence_delta_raises():
    """A confidence_delta > 0 must raise ValueError."""
    agent = ConcreteAntagonist(return_dict=_valid_critique(confidence_delta=0.1))
    with pytest.raises(ValueError, match="confidence_delta"):
        agent.critique(specialist_output={}, context={})


def test_detail_min_length_enforced():
    """A detail string of exactly 49 characters must raise ValueError."""
    short_detail = "x" * 49
    agent = ConcreteAntagonist(return_dict=_valid_critique(detail=short_detail))
    with pytest.raises(ValueError, match="detail must be str"):
        agent.critique(specialist_output={}, context={})


def test_detail_at_boundary_accepted():
    """A detail string of exactly 50 characters must be accepted."""
    boundary_detail = "y" * 50
    agent = ConcreteAntagonist(return_dict=_valid_critique(detail=boundary_detail))
    result = agent.critique(specialist_output={}, context={})
    assert len(result["detail"]) == 50


def test_missing_key_raises():
    """Omitting 'evidence' from the generated dict must raise ValueError naming the key."""
    raw = _valid_critique()
    del raw["evidence"]
    agent = ConcreteAntagonist(return_dict=raw)
    with pytest.raises(ValueError, match="missing required keys"):
        agent.critique(specialist_output={}, context={})


def test_both_params_consumed():
    """Both specialist_output and context must reach _generate_critique (P2 guard)."""
    specialist_output = {"numerical_answer": "42 N"}
    context = {"trace_id": "abc-123", "task": "load analysis"}

    agent = ConcreteAntagonist()
    agent.critique(specialist_output=specialist_output, context=context)

    assert agent.last_specialist_output is specialist_output
    assert agent.last_context is context
