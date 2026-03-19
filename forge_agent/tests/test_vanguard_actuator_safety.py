"""Acceptance-criteria tests for plan 5-004: Actuator safety specialist + antagonist."""
from __future__ import annotations

import pytest

from forge_agent.agents.antagonist_base import AntagonistAgent
from forge_agent.agents.vanguard import actuator_safety
from forge_agent.agents.vanguard.actuator_safety_antagonist import (
    ActuatorSafetyAntagonist,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def antagonist() -> ActuatorSafetyAntagonist:
    return ActuatorSafetyAntagonist()


# ---------------------------------------------------------------------------
# AC 1: pytest exits 0 — covered implicitly by this file running without error
# ---------------------------------------------------------------------------


# AC 2: ActuatorSafetyAntagonist is a subclass of AntagonistAgent
def test_ac2_is_subclass_of_antagonist_agent() -> None:
    assert issubclass(ActuatorSafetyAntagonist, AntagonistAgent)


# AC 3: critique() with empty specialist output returns a valid dict (missing safety_factor → fatal)
def test_ac3_critique_empty_output_returns_valid_dict(
    antagonist: ActuatorSafetyAntagonist,
) -> None:
    result = antagonist.critique({}, {})
    assert isinstance(result, dict)
    required_keys = {
        "error_code",
        "critique_type",
        "severity",
        "detail",
        "evidence",
        "confidence_delta",
    }
    assert required_keys == result.keys()
    assert result["severity"] == "fatal"


# AC 4: safety_factor=1.5 (< 2.0) → severity="fatal"
def test_ac4_low_safety_factor_returns_fatal(
    antagonist: ActuatorSafetyAntagonist,
) -> None:
    result = antagonist.critique({"safety_factor": 1.5}, {})
    assert result["severity"] == "fatal"


# AC 5: safety_factor=2.5 but no burst_pressure_kPa → severity="warning"
def test_ac5_missing_burst_pressure_returns_warning(
    antagonist: ActuatorSafetyAntagonist,
) -> None:
    result = antagonist.critique({"safety_factor": 2.5}, {})
    assert result["severity"] == "warning"


# AC 6: safety_factor=2.5, burst_pressure_kPa=800, failure_modes present → severity="info"
def test_ac6_complete_output_returns_info(
    antagonist: ActuatorSafetyAntagonist,
) -> None:
    result = antagonist.critique(
        {
            "safety_factor": 2.5,
            "burst_pressure_kPa": 800,
            "failure_modes": ["burst", "braid_failure"],
        },
        {},
    )
    assert result["severity"] == "info"


# AC 7: SYSTEM_PROMPT is a non-empty string containing "safety" or "Safety"
def test_ac7_system_prompt_contains_safety() -> None:
    prompt = actuator_safety.SYSTEM_PROMPT
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "safety" in prompt or "Safety" in prompt


# AC 8: ROLE == "actuator_safety_specialist"
def test_ac8_role_constant() -> None:
    assert actuator_safety.ROLE == "actuator_safety_specialist"


# AC 9: both specialist_output and context reach _generate_critique (P2 guard)
def test_ac9_both_params_consumed(antagonist: ActuatorSafetyAntagonist) -> None:
    """Verify _generate_critique uses specialist_output (inspects 'safety_factor') and
    consumes context (assigned to _ without raising). We call with a sentinel
    context and confirm no AttributeError is raised and specialist_output is
    actually read (safety_factor=2.5, no burst_pressure → warning)."""
    sentinel_context = {"trace_id": "test-sentinel-9"}
    result = antagonist.critique({"safety_factor": 2.5}, sentinel_context)
    # specialist_output was read (safety_factor present and ≥ 2.0 → no fatal;
    # burst_pressure_kPa absent → warning)
    assert result["severity"] == "warning"
    # context was consumed without error — _ = context in the implementation is the P2 guard
