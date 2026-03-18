"""Tests for DebateOrchestrator — plan 4-002 acceptance criteria."""

from __future__ import annotations

from unittest.mock import MagicMock

from forge_agent.core.debate_orchestrator import DebateOrchestrator
from forge_agent.core.pipeline import PipelineRunner, TaskRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_antagonist(severity: str) -> MagicMock:
    """Return a mock antagonist whose critique() returns given severity."""
    ant = MagicMock()
    ant.critique.return_value = {
        "error_code": None,
        "critique_type": "factual",
        "severity": severity,
        "detail": "A" * 60,
        "evidence": "test evidence",
        "confidence_delta": -0.1,
    }
    return ant


def _make_specialist() -> MagicMock:
    return MagicMock()


SPECIALIST_OUTPUT = {
    "numerical_answer": "42 N",
    "model_choice": "Euler-Bernoulli",
    "what_would_falsify": [],
}


# ---------------------------------------------------------------------------
# AC 2: info severity → verdict "consensus"
# ---------------------------------------------------------------------------


def test_info_severity_yields_consensus():
    ant = _make_antagonist("info")
    spec = _make_specialist()
    orchestrator = DebateOrchestrator(specialist=spec, antagonist=ant)
    result = orchestrator.run_debate(SPECIALIST_OUTPUT, {})
    assert result.verdict == "consensus"


# ---------------------------------------------------------------------------
# AC 3: fatal severity → verdict "maintained_disagreement"
# ---------------------------------------------------------------------------


def test_fatal_severity_yields_maintained_disagreement():
    ant = _make_antagonist("fatal")
    spec = _make_specialist()
    orchestrator = DebateOrchestrator(specialist=spec, antagonist=ant)
    result = orchestrator.run_debate(SPECIALIST_OUTPUT, {})
    assert result.verdict == "maintained_disagreement"


# ---------------------------------------------------------------------------
# AC 4: pipeline with DebateOrchestrator injected → TaskResult includes debate_verdict
# ---------------------------------------------------------------------------


def test_pipeline_debate_verdict_present_when_orchestrator_injected():
    ant = _make_antagonist("warning")
    spec = _make_specialist()
    orchestrator = DebateOrchestrator(specialist=spec, antagonist=ant)
    runner = PipelineRunner(config={}, debate_orchestrator=orchestrator)
    req = TaskRequest(
        task_type="analysis", project="test", component="bracket", description="test"
    )
    result = runner.run(req)
    # debate_verdict must be set (not None)
    assert result.debate_verdict is not None
    assert result.debate_verdict in {"consensus", "maintained_disagreement"}


# ---------------------------------------------------------------------------
# AC 5: pipeline with no antagonist → debate_verdict is None
# ---------------------------------------------------------------------------


def test_pipeline_no_debate_verdict_when_no_orchestrator():
    runner = PipelineRunner(config={})
    req = TaskRequest(
        task_type="analysis", project="test", component="bracket", description="test"
    )
    result = runner.run(req)
    assert result.debate_verdict is None


# ---------------------------------------------------------------------------
# AC 6: DebateResult.rounds >= 1
# ---------------------------------------------------------------------------


def test_debate_result_rounds_at_least_one():
    ant = _make_antagonist("info")
    spec = _make_specialist()
    orchestrator = DebateOrchestrator(specialist=spec, antagonist=ant)
    result = orchestrator.run_debate(SPECIALIST_OUTPUT, {})
    assert isinstance(result.rounds, int)
    assert result.rounds >= 1


# ---------------------------------------------------------------------------
# AC 7: DebateResult.critiques is a list
# ---------------------------------------------------------------------------


def test_debate_result_critiques_is_list():
    ant = _make_antagonist("warning")
    spec = _make_specialist()
    orchestrator = DebateOrchestrator(specialist=spec, antagonist=ant)
    result = orchestrator.run_debate(SPECIALIST_OUTPUT, {})
    assert isinstance(result.critiques, list)


# ---------------------------------------------------------------------------
# AC 8: maintained_disagreement + fatal → TaskResult.status == "disputed"
# ---------------------------------------------------------------------------


def test_fatal_dispute_sets_status_disputed():
    ant = _make_antagonist("fatal")
    spec = _make_specialist()
    orchestrator = DebateOrchestrator(specialist=spec, antagonist=ant)
    runner = PipelineRunner(config={}, debate_orchestrator=orchestrator)
    req = TaskRequest(
        task_type="analysis", project="test", component="bracket", description="test"
    )
    result = runner.run(req)
    assert result.debate_verdict == "maintained_disagreement"
    assert result.status == "disputed"
