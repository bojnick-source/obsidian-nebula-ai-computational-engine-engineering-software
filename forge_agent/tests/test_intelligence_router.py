"""Unit tests for forge_agent/core/intelligence_router.py.

Tests pure trigger-detection logic in IntelligenceRouter without making
any external API calls. The plan() method and private static methods are
tested against known trigger vocabulary from the source.
"""
from __future__ import annotations

import pytest

from forge_agent.core.intelligence_router import IntelligenceRouter, PreTask, _CURRENT_INFO_TRIGGERS, _MATH_TRIGGERS


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
    from forge_agent.core.intelligence_router import PreTaskResult
    result = router.format_context([])
    assert result == ""


def test_format_context_error_result_included():
    """format_context must include error results in output."""
    from forge_agent.core.intelligence_router import PreTaskResult
    router = IntelligenceRouter()
    results = [PreTaskResult(task_type="math_compute", provider="openai", content="", error="timeout")]
    output = router.format_context(results)
    assert "ERROR" in output
    assert "timeout" in output
