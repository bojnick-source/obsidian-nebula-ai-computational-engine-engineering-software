"""
forge_agent/tests/test_vanguard_pipeline.py

Acceptance-criteria tests for 5-005: VanguardPipelineRunner + specialist_prompt param.

All 9 ACs covered. No Anthropic API key required — stub specialist path used throughout.
"""

from __future__ import annotations

import pytest

from forge_agent.core.pipeline import PipelineRunner, TaskRequest, TaskResult
from forge_agent.core.vanguard_pipeline import VanguardPipelineRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request() -> TaskRequest:
    return TaskRequest(
        task_type="analysis",
        project="vanguard",
        component="pam",
        description="test",
    )


# ---------------------------------------------------------------------------
# AC1: all tests in this file pass (implicit — if the suite exits 0, AC1 is met)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# AC2: specialist_prompt stored and used when set
# ---------------------------------------------------------------------------


def test_pipeline_stores_custom_specialist_prompt():
    """AC2: PipelineRunner stores a custom specialist_prompt."""
    runner = PipelineRunner(config={}, specialist_prompt="custom prompt")
    assert runner._specialist_prompt == "custom prompt"


# ---------------------------------------------------------------------------
# AC3: backward compatibility — ME_SYSTEM_PROMPT used when not set
# ---------------------------------------------------------------------------


def test_pipeline_uses_me_prompt_by_default():
    """AC3: PipelineRunner falls back to ME_SYSTEM_PROMPT when specialist_prompt is None."""
    from forge_agent.agents.engineers.mechanical_engineer import SYSTEM_PROMPT as ME
    runner = PipelineRunner(config={})
    assert runner._specialist_prompt == ME


# ---------------------------------------------------------------------------
# AC4-AC7: each domain runs without raising and returns a TaskResult
# ---------------------------------------------------------------------------


def test_vanguard_synthmuscle_runs():
    """AC4: synthmuscle domain runs end-to-end (stub specialist path)."""
    runner = VanguardPipelineRunner("synthmuscle", config={})
    result = runner.run(_make_request())
    assert result is not None
    assert isinstance(result, TaskResult)


def test_vanguard_mujoco_sim_runs():
    """AC5: mujoco_sim domain runs end-to-end (stub specialist path)."""
    runner = VanguardPipelineRunner("mujoco_sim", config={})
    result = runner.run(_make_request())
    assert result is not None
    assert isinstance(result, TaskResult)


def test_vanguard_cmaes_opt_runs():
    """AC6: cmaes_opt domain runs end-to-end (stub specialist path)."""
    runner = VanguardPipelineRunner("cmaes_opt", config={})
    result = runner.run(_make_request())
    assert result is not None
    assert isinstance(result, TaskResult)


def test_vanguard_actuator_safety_runs():
    """AC7: actuator_safety domain runs end-to-end (stub specialist path)."""
    runner = VanguardPipelineRunner("actuator_safety", config={})
    result = runner.run(_make_request())
    assert result is not None
    assert isinstance(result, TaskResult)


# ---------------------------------------------------------------------------
# AC8: unknown domain raises ValueError with descriptive message
# ---------------------------------------------------------------------------


def test_unknown_domain_raises():
    """AC8: VanguardPipelineRunner raises ValueError for unknown domain."""
    with pytest.raises(ValueError, match="unknown domain"):
        VanguardPipelineRunner("unknown_domain", config={})


def test_unknown_domain_error_lists_valid_domains():
    """AC8 (supplemental): error message contains at least one valid domain name."""
    with pytest.raises(ValueError, match="synthmuscle"):
        VanguardPipelineRunner("bad_domain", config={})


# ---------------------------------------------------------------------------
# AC9: debate_verdict is not None (DebateOrchestrator is wired in)
# ---------------------------------------------------------------------------


def test_vanguard_pipeline_has_debate_verdict():
    """AC9: TaskResult.debate_verdict is not None — DebateOrchestrator is wired."""
    runner = VanguardPipelineRunner("synthmuscle", config={})
    result = runner.run(_make_request())
    assert result.debate_verdict is not None
