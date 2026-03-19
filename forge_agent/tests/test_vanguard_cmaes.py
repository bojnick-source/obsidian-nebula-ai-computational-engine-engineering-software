"""Acceptance-criteria tests for CMA-ES optimization specialist + antagonist (plan 5-003)."""
from __future__ import annotations

from forge_agent.agents.antagonist_base import AntagonistAgent
from forge_agent.agents.vanguard import cmaes_optimization
from forge_agent.agents.vanguard.cmaes_optimization_antagonist import CMAESOptimizationAntagonist


# ---------------------------------------------------------------------------
# AC 1: pytest exits 0 (implicit — all tests must pass)
# AC 2: CMAESOptimizationAntagonist is a subclass of AntagonistAgent
# ---------------------------------------------------------------------------

def test_ac2_is_subclass_of_antagonist_agent():
    """AC2: CMAESOptimizationAntagonist must be a subclass of AntagonistAgent."""
    assert issubclass(CMAESOptimizationAntagonist, AntagonistAgent)


# ---------------------------------------------------------------------------
# AC 3: default info critique path — empty specialist output
# ---------------------------------------------------------------------------

def test_ac3_critique_empty_output_returns_valid_dict():
    """AC3: critique({}, {}) returns a valid dict with all required keys."""
    agent = CMAESOptimizationAntagonist()
    result = agent.critique({}, {})
    required_keys = {"error_code", "critique_type", "severity", "detail", "evidence", "confidence_delta"}
    assert required_keys == result.keys()
    assert result["severity"] == "info"


# ---------------------------------------------------------------------------
# AC 4: cvar_pass is False → fatal
# ---------------------------------------------------------------------------

def test_ac4_cvar_pass_false_gives_fatal():
    """AC4: When cvar_pass is False, critique returns severity='fatal'."""
    agent = CMAESOptimizationAntagonist()
    result = agent.critique({"cvar_pass": False}, {})
    assert result["severity"] == "fatal"


def test_ac4_cvar_pass_none_does_not_give_fatal():
    """AC4 guard: cvar_pass=None must NOT trigger the fatal path (is False identity check)."""
    agent = CMAESOptimizationAntagonist()
    result = agent.critique({"cvar_pass": None}, {})
    assert result["severity"] != "fatal"


# ---------------------------------------------------------------------------
# AC 5: stagnation is True → warning
# ---------------------------------------------------------------------------

def test_ac5_stagnation_true_gives_warning():
    """AC5: When stagnation is True (and cvar_pass is not False), severity='warning'."""
    agent = CMAESOptimizationAntagonist()
    result = agent.critique({"cvar_pass": True, "stagnation": True}, {})
    assert result["severity"] == "warning"


def test_ac5_stagnation_truthy_non_bool_does_not_give_warning():
    """AC5 guard: stagnation=1 (truthy but not True) must NOT trigger warning (is True check)."""
    agent = CMAESOptimizationAntagonist()
    result = agent.critique({"cvar_pass": True, "stagnation": 1}, {})
    assert result["severity"] == "info"


# ---------------------------------------------------------------------------
# AC 6: cvar_pass=True, stagnation=False → info
# ---------------------------------------------------------------------------

def test_ac6_clean_output_gives_info():
    """AC6: cvar_pass=True, stagnation=False → severity='info'."""
    agent = CMAESOptimizationAntagonist()
    result = agent.critique({"cvar_pass": True, "stagnation": False}, {})
    assert result["severity"] == "info"


# ---------------------------------------------------------------------------
# AC 7: SYSTEM_PROMPT is non-empty and contains "CMA-ES"
# ---------------------------------------------------------------------------

def test_ac7_system_prompt_contains_cmaes():
    """AC7: SYSTEM_PROMPT must be a non-empty string containing 'CMA-ES'."""
    assert isinstance(cmaes_optimization.SYSTEM_PROMPT, str)
    assert len(cmaes_optimization.SYSTEM_PROMPT) > 0
    assert "CMA-ES" in cmaes_optimization.SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# AC 8: ROLE constant
# ---------------------------------------------------------------------------

def test_ac8_role_constant():
    """AC8: ROLE must equal 'cmaes_optimization_specialist'."""
    assert cmaes_optimization.ROLE == "cmaes_optimization_specialist"


# ---------------------------------------------------------------------------
# AC 9: both params reach _generate_critique (P2 guard)
# ---------------------------------------------------------------------------

def test_ac9_both_params_consumed():
    """AC9: specialist_output and context must both reach _generate_critique."""
    specialist_output = {"cvar_pass": True, "stagnation": False, "generations": 100}
    context = {"trace_id": "test-cmaes-001", "task": "PAM control optimisation"}

    agent = CMAESOptimizationAntagonist()
    # _generate_critique uses _ = context to consume; critique() passes both.
    # Verify no AttributeError and a valid result is returned.
    result = agent.critique(specialist_output=specialist_output, context=context)
    assert result["severity"] in {"fatal", "warning", "info"}
