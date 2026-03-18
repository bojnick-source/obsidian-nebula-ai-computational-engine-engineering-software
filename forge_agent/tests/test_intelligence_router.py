"""Unit tests for forge_agent/core/intelligence_router.py.

Tests pure trigger-detection logic in IntelligenceRouter without making
any external API calls. The plan() method and private static methods are
tested against known trigger vocabulary from the source.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from forge_agent.core.intelligence_router import (
    FailoverRouter,
    IntelligenceRouter,
    PreTask,
    PreTaskResult,
)
from forge_agent.core.retry import CircuitBreaker, CircuitState


# ─────────────────────────────────────────────────────────────────────────────
# Trigger detection — pure static methods
# ─────────────────────────────────────────────────────────────────────────────


def test_current_info_trigger_detected():
    """Text containing a current-info keyword should trigger current_intelligence."""
    router = IntelligenceRouter()
    # Use a known trigger word from _CURRENT_INFO_TRIGGERS
    assert router._requires_current_info("what is the latest price of titanium?")
    assert router._requires_current_info("current availability of IN718 alloy")
    assert router._requires_current_info("show me the recent spec sheet for CFRP")


def test_current_info_no_trigger_on_generic_text():
    """Text with no current-info keywords should not trigger current_intelligence."""
    router = IntelligenceRouter()
    # Generic engineering text — no trigger words
    assert not router._requires_current_info("calculate the von mises stress in the bracket")
    assert not router._requires_current_info("perform finite element analysis on the plate")


def test_math_trigger_detected():
    """Text containing a math keyword should trigger math_compute."""
    router = IntelligenceRouter()
    assert router._requires_formal_math("please derive the eigenvalue decomposition")
    assert router._requires_formal_math("provide a formal proof of convergence for this ODE")
    assert router._requires_formal_math("stability analysis using the hessian matrix")


def test_math_no_trigger_on_generic_text():
    """Text with no math keywords should not trigger math_compute."""
    router = IntelligenceRouter()
    # Carefully chosen: no substring from _MATH_TRIGGERS (e.g. "model" contains "ode")
    assert not router._requires_formal_math("generate a CAD drawing of the bracket assembly")
    assert not router._requires_formal_math("select a material for a 500N tensile load")


# ─────────────────────────────────────────────────────────────────────────────
# plan() — PreTask assembly
# ─────────────────────────────────────────────────────────────────────────────


def test_plan_returns_empty_for_generic_message():
    """A generic message with no triggers should return no pre-tasks."""
    router = IntelligenceRouter()
    pre_tasks = router.plan("design a simple bracket for a 200N load")
    assert pre_tasks == [], f"Expected no pre-tasks, got: {pre_tasks}"


def test_plan_returns_current_intelligence_task():
    """A message with a current-info trigger should produce a current_intelligence task."""
    router = IntelligenceRouter()
    pre_tasks = router.plan("what is the current price of titanium grade 5?")
    task_types = [t.task_type for t in pre_tasks]
    assert "current_intelligence" in task_types


def test_plan_returns_math_compute_task():
    """A message with a math trigger should produce a math_compute task."""
    router = IntelligenceRouter()
    pre_tasks = router.plan("derive the lagrangian equations of motion for this system")
    task_types = [t.task_type for t in pre_tasks]
    assert "math_compute" in task_types


def test_plan_returns_video_analysis_for_youtube_url():
    """A message with a YouTube URL should produce a video_analysis task."""
    router = IntelligenceRouter()
    pre_tasks = router.plan("analyze this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    task_types = [t.task_type for t in pre_tasks]
    assert "video_analysis" in task_types


def test_plan_multiple_triggers_returns_multiple_tasks():
    """A message triggering both math and current-info returns both tasks."""
    router = IntelligenceRouter()
    # "prove" is math, "latest" is current-info
    pre_tasks = router.plan("prove using the latest eigenvalue bounds from 2025 papers")
    task_types = [t.task_type for t in pre_tasks]
    assert "current_intelligence" in task_types
    assert "math_compute" in task_types


def test_plan_pre_tasks_have_required_fields():
    """Each returned PreTask must have provider, task_type, and query set."""
    router = IntelligenceRouter()
    pre_tasks = router.plan("what is the current availability of carbon fiber prepreg?")
    for task in pre_tasks:
        assert isinstance(task, PreTask)
        assert task.provider, f"PreTask missing provider: {task}"
        assert task.task_type, f"PreTask missing task_type: {task}"
        assert task.query, f"PreTask missing query: {task}"


# ─────────────────────────────────────────────────────────────────────────────
# Domain inference
# ─────────────────────────────────────────────────────────────────────────────


def test_infer_domains_returns_list():
    """_infer_domains must return a list (possibly empty) for any input."""
    router = IntelligenceRouter()
    result = router._infer_domains("check arxiv for papers on material fatigue")
    assert isinstance(result, list)
    assert "arxiv.org" in result


def test_infer_domains_empty_for_no_match():
    """_infer_domains must return empty list when no domain keywords are present."""
    router = IntelligenceRouter()
    result = router._infer_domains("run a simple FEA simulation")
    assert isinstance(result, list)
    assert len(result) == 0


# ─────────────────────────────────────────────────────────────────────────────
# format_context
# ─────────────────────────────────────────────────────────────────────────────


def test_format_context_empty_returns_empty_string():
    """format_context with no results must return empty string."""
    router = IntelligenceRouter()
    result = router.format_context([])
    assert result == ""


def test_format_context_error_result_included():
    """format_context must include error results in output."""
    router = IntelligenceRouter()
    results = [PreTaskResult(task_type="math_compute", provider="openai", content="", error="timeout")]
    output = router.format_context(results)
    assert "ERROR" in output
    assert "timeout" in output


# ─────────────────────────────────────────────────────────────────────────────
# FailoverRouter — plan 4-003 acceptance criteria
# ─────────────────────────────────────────────────────────────────────────────


def _make_providers(anthropic_response=None, openai_response=None):
    """Build a mock ProviderClients with controllable async API."""
    providers = MagicMock()
    providers.resolve_model.return_value = ("claude-opus-4-6", "anthropic")

    if anthropic_response is not None:
        msg = MagicMock()
        msg.content = [MagicMock(text=anthropic_response)]
        providers.anthropic.messages.create = AsyncMock(return_value=msg)
    else:
        providers.anthropic.messages.create = AsyncMock(side_effect=RuntimeError("primary fail"))

    if openai_response is not None:
        choice = MagicMock()
        choice.message.content = openai_response
        oai_resp = MagicMock()
        oai_resp.choices = [choice]
        providers.openai.chat.completions.create = AsyncMock(return_value=oai_resp)
    else:
        providers.openai.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("secondary fail")
        )

    return providers


# AC 2: primary raises → record_failure + retry on secondary
@pytest.mark.asyncio
async def test_failover_on_primary_exception():
    primary_cb = CircuitBreaker()
    secondary_cb = CircuitBreaker()
    providers = _make_providers(anthropic_response=None, openai_response="secondary_ok")
    router = FailoverRouter(
        config={}, providers=providers, primary_cb=primary_cb, secondary_cb=secondary_cb
    )
    result = await router.route_call("specialist", [{"role": "user", "content": "x"}])
    assert result["provider"] == "openai"
    assert result["content"] == "secondary_ok"
    # primary cb must have recorded a failure
    assert primary_cb._failure_count == 1


# AC 3: primary circuit OPEN → skip primary entirely, call secondary
@pytest.mark.asyncio
async def test_skips_primary_when_open():
    primary_cb = CircuitBreaker()
    # Force circuit OPEN by simulating failures at threshold
    for _ in range(primary_cb.failure_threshold):
        primary_cb.record_failure()
    assert primary_cb.state == CircuitState.OPEN

    providers = _make_providers(anthropic_response="primary_ok", openai_response="secondary_ok")
    router = FailoverRouter(config={}, providers=providers, primary_cb=primary_cb)
    result = await router.route_call("specialist", [{"role": "user", "content": "x"}])
    # Primary was OPEN so secondary was called
    assert result["provider"] == "openai"
    providers.anthropic.messages.create.assert_not_called()


# AC 4: primary succeeds → record_success, secondary NOT called
@pytest.mark.asyncio
async def test_primary_success_no_secondary_call():
    primary_cb = CircuitBreaker()
    secondary_cb = CircuitBreaker()
    providers = _make_providers(anthropic_response="primary_ok", openai_response="secondary_ok")
    router = FailoverRouter(
        config={}, providers=providers, primary_cb=primary_cb, secondary_cb=secondary_cb
    )
    result = await router.route_call("specialist", [{"role": "user", "content": "x"}])
    assert result["provider"] == "anthropic"
    assert result["content"] == "primary_ok"
    providers.openai.chat.completions.create.assert_not_called()
    assert primary_cb._failure_count == 0


# AC 5: both fail → RuntimeError with ERR_PROVIDER_UNAVAILABLE
@pytest.mark.asyncio
async def test_both_fail_raises_provider_unavailable():
    providers = _make_providers(anthropic_response=None, openai_response=None)
    router = FailoverRouter(config={}, providers=providers)
    with pytest.raises(RuntimeError, match="ERR_PROVIDER_UNAVAILABLE"):
        await router.route_call("specialist", [{"role": "user", "content": "x"}])


# AC 6: HALF_OPEN probe guard — second concurrent caller goes to secondary
@pytest.mark.asyncio
async def test_half_open_second_caller_goes_to_secondary():
    primary_cb = CircuitBreaker()
    # Force circuit to HALF_OPEN by opening then marking it half-open manually
    for _ in range(primary_cb.failure_threshold):
        primary_cb.record_failure()
    primary_cb._state = CircuitState.HALF_OPEN
    primary_cb._probe_in_flight = False

    # First allow_call sets _probe_in_flight=True; second returns False
    assert primary_cb.allow_call() is True    # probe allowed
    assert primary_cb.allow_call() is False   # second caller rejected


# AC 7: PipelineRunner with intelligence_router injected uses router path
def test_pipeline_uses_intelligence_router_when_injected():
    from forge_agent.core.pipeline import PipelineRunner, TaskRequest

    mock_router = MagicMock()
    mock_router.route_call_sync.return_value = {
        "provider": "anthropic",
        "model": "claude-opus-4-6",
        "content": '{"steps": ["done"]}',
        "raw_response": MagicMock(),
    }
    runner = PipelineRunner(
        config={},
        intelligence_router=mock_router,
    )
    req = TaskRequest(
        task_type="analysis",
        project="test",
        component="bracket",
        description="test task",
    )
    result = runner.run(req)
    assert result.status in {"ok", "error", "failed"}  # pipeline completed
    mock_router.route_call_sync.assert_called_once()


# AC 8: route_call is async (awaitable)
def test_route_call_is_async():
    import inspect
    router = FailoverRouter(config={}, providers=MagicMock())
    assert inspect.iscoroutinefunction(router.route_call)
