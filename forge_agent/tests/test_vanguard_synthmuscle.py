"""Acceptance tests for the Synthmuscle specialist + antagonist agents (plan 5-001).

AC1  pytest exits 0
AC2  SynthmuscleAntagonist is a subclass of AntagonistAgent
AC3  critique({}, {}) returns a valid dict with all 6 keys (info path)
AC4  rmse_pct=8.5 → severity="fatal", critique_type="methodology"
AC5  r2=0.92 → severity="warning"
AC6  empty specialist_output → severity="info"
AC7  synthmuscle.SYSTEM_PROMPT is non-empty and contains "PAM" or "McKibben"
AC8  synthmuscle.ROLE == "synthmuscle_specialist"
AC9  both specialist_output and context params reach _generate_critique (P2 guard)
"""
from __future__ import annotations

import pytest

from forge_agent.agents.antagonist_base import AntagonistAgent
from forge_agent.agents.vanguard import synthmuscle
from forge_agent.agents.vanguard.synthmuscle_antagonist import SynthmuscleAntagonist

REQUIRED_KEYS = frozenset(
    {"error_code", "critique_type", "severity", "detail", "evidence", "confidence_delta"}
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def antagonist() -> SynthmuscleAntagonist:
    return SynthmuscleAntagonist()


# ---------------------------------------------------------------------------
# AC2 — subclass check
# ---------------------------------------------------------------------------


def test_ac2_is_subclass_of_antagonist_agent():
    """AC2: SynthmuscleAntagonist must be a subclass of AntagonistAgent."""
    assert issubclass(SynthmuscleAntagonist, AntagonistAgent)


# ---------------------------------------------------------------------------
# AC3 — default info path returns all 6 keys
# ---------------------------------------------------------------------------


def test_ac3_critique_empty_output_returns_all_keys(antagonist):
    """AC3: critique({}, {}) must return dict with exactly the 6 required keys."""
    result = antagonist.critique(specialist_output={}, context={})
    assert REQUIRED_KEYS == result.keys()


# ---------------------------------------------------------------------------
# AC4 — rmse_pct > 5 → fatal, methodology
# ---------------------------------------------------------------------------


def test_ac4_high_rmse_returns_fatal(antagonist):
    """AC4: rmse_pct=8.5 must produce severity='fatal' and critique_type='methodology'."""
    result = antagonist.critique(specialist_output={"rmse_pct": 8.5}, context={})
    assert result["severity"] == "fatal"
    assert result["critique_type"] == "methodology"


def test_ac4_rmse_exactly_at_threshold_is_not_fatal(antagonist):
    """rmse_pct=5.0 (not > 5.0) must NOT trigger the fatal path."""
    result = antagonist.critique(specialist_output={"rmse_pct": 5.0}, context={})
    assert result["severity"] != "fatal"


def test_ac4_rmse_below_threshold_is_not_fatal(antagonist):
    """rmse_pct=3.0 must NOT trigger the fatal path."""
    result = antagonist.critique(specialist_output={"rmse_pct": 3.0}, context={})
    assert result["severity"] != "fatal"


# ---------------------------------------------------------------------------
# AC5 — r2 < 0.95 → warning
# ---------------------------------------------------------------------------


def test_ac5_low_r2_returns_warning(antagonist):
    """AC5: r2=0.92 must produce severity='warning'."""
    result = antagonist.critique(specialist_output={"r2": 0.92}, context={})
    assert result["severity"] == "warning"


def test_ac5_r2_at_threshold_is_not_warning(antagonist):
    """r2=0.95 (not < 0.95) must NOT trigger the warning path."""
    result = antagonist.critique(specialist_output={"r2": 0.95}, context={})
    assert result["severity"] != "warning"


# ---------------------------------------------------------------------------
# AC6 — empty output → info
# ---------------------------------------------------------------------------


def test_ac6_empty_specialist_output_returns_info(antagonist):
    """AC6: Empty specialist_output must produce severity='info'."""
    result = antagonist.critique(specialist_output={}, context={})
    assert result["severity"] == "info"


# ---------------------------------------------------------------------------
# AC7 — SYSTEM_PROMPT contains "PAM" or "McKibben"
# ---------------------------------------------------------------------------


def test_ac7_system_prompt_nonempty_and_contains_pam_or_mckibben():
    """AC7: synthmuscle.SYSTEM_PROMPT must be a non-empty string mentioning PAM or McKibben."""
    assert isinstance(synthmuscle.SYSTEM_PROMPT, str)
    assert len(synthmuscle.SYSTEM_PROMPT) > 0
    assert "PAM" in synthmuscle.SYSTEM_PROMPT or "McKibben" in synthmuscle.SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# AC8 — ROLE
# ---------------------------------------------------------------------------


def test_ac8_role_constant():
    """AC8: synthmuscle.ROLE must equal 'synthmuscle_specialist'."""
    assert synthmuscle.ROLE == "synthmuscle_specialist"


# ---------------------------------------------------------------------------
# AC9 — both params reach _generate_critique (P2 guard)
# ---------------------------------------------------------------------------


def test_ac9_both_params_reach_generate_critique():
    """AC9: specialist_output and context must both reach _generate_critique (P2 guard)."""

    received: dict = {}

    class InstrumentedAntagonist(SynthmuscleAntagonist):
        def _generate_critique(self, specialist_output: dict, context: dict) -> dict:
            received["specialist_output"] = specialist_output
            received["context"] = context
            return super()._generate_critique(specialist_output, context)

    agent = InstrumentedAntagonist()
    so = {"rmse_pct": 2.0, "r2": 0.98}
    ctx = {"trace_id": "test-001", "task": "PAM characterisation"}
    agent.critique(specialist_output=so, context=ctx)

    assert received["specialist_output"] is so
    assert received["context"] is ctx
