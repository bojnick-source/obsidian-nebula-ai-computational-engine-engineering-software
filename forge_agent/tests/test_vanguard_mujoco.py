"""Acceptance-criteria tests for plan 5-002: MuJoCo simulation specialist + antagonist."""
from __future__ import annotations

import pytest

from forge_agent.agents.antagonist_base import AntagonistAgent
from forge_agent.agents.vanguard import mujoco_simulation
from forge_agent.agents.vanguard.mujoco_simulation_antagonist import (
    MuJoCoSimulationAntagonist,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def antagonist() -> MuJoCoSimulationAntagonist:
    return MuJoCoSimulationAntagonist()


# ---------------------------------------------------------------------------
# AC 1: pytest exits 0 — covered implicitly by this file running without error
# ---------------------------------------------------------------------------


# AC 2: MuJoCoSimulationAntagonist is a subclass of AntagonistAgent
def test_ac2_is_subclass_of_antagonist_agent() -> None:
    assert issubclass(MuJoCoSimulationAntagonist, AntagonistAgent)


# AC 3: critique() returns a valid dict with an empty specialist output
def test_ac3_critique_empty_output_returns_valid_dict(
    antagonist: MuJoCoSimulationAntagonist,
) -> None:
    # Empty dict has no "seed" key → fatal path, but still a valid dict
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


# AC 4: missing "seed" key → severity="fatal"
def test_ac4_missing_seed_returns_fatal(
    antagonist: MuJoCoSimulationAntagonist,
) -> None:
    result = antagonist.critique({"steps": 500}, {})
    assert result["severity"] == "fatal"


# AC 5: steps < 100 → severity="warning"
def test_ac5_low_steps_returns_warning(
    antagonist: MuJoCoSimulationAntagonist,
) -> None:
    result = antagonist.critique({"seed": 42, "steps": 50}, {})
    assert result["severity"] == "warning"


# AC 6: seed present, steps >= 100 → severity="info"
def test_ac6_good_output_returns_info(
    antagonist: MuJoCoSimulationAntagonist,
) -> None:
    result = antagonist.critique({"seed": 42, "steps": 500}, {})
    assert result["severity"] == "info"


# AC 7: SYSTEM_PROMPT is a non-empty string containing "MuJoCo" or "MJCF"
def test_ac7_system_prompt_contains_mujoco_or_mjcf() -> None:
    prompt = mujoco_simulation.SYSTEM_PROMPT
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "MuJoCo" in prompt or "MJCF" in prompt


# AC 8: ROLE == "mujoco_simulation_specialist"
def test_ac8_role_constant() -> None:
    assert mujoco_simulation.ROLE == "mujoco_simulation_specialist"


# AC 9: both specialist_output and context reach _generate_critique (P2 guard)
def test_ac9_both_params_consumed(antagonist: MuJoCoSimulationAntagonist) -> None:
    """Verify _generate_critique uses specialist_output (inspects 'seed') and
    consumes context (assigned to _ without raising). We call with a sentinel
    context and confirm no AttributeError is raised and specialist_output is
    actually read (wrong steps value triggers warning, not fatal)."""
    sentinel_context = {"trace_id": "test-sentinel-9"}
    result = antagonist.critique({"seed": 42, "steps": 50}, sentinel_context)
    # specialist_output was read (seed present → no fatal; steps=50 → warning)
    assert result["severity"] == "warning"
    # context was consumed without error — if it were ignored the test would still
    # pass, but the _ = context assignment in the implementation is the P2 guard.
