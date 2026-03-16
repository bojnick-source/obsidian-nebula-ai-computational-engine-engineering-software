"""
Tests for SwanlabTracker and its integration with AgentLogger.

All tests run without swanlab installed (the tracker no-ops gracefully).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from forge_agent.core.swanlab_tracker import SwanlabTracker
from forge_agent.core.logger import AgentLogger


# ── SwanlabTracker unit tests ─────────────────────────────────────────────────


def test_create_without_swanlab_returns_noop_tracker():
    """SwanlabTracker.create() should succeed even when swanlab is absent."""
    with patch("forge_agent.core.swanlab_tracker._SWANLAB_AVAILABLE", False):
        tracker = SwanlabTracker.create(project="test")
    assert tracker._run is None


def test_log_methods_noop_when_run_is_none():
    """All log methods must be safe to call with no active run."""
    tracker = SwanlabTracker()  # no _run
    tracker.log_model_call(
        iteration=1, input_tokens=100, output_tokens=50, latency_ms=300.0
    )
    tracker.log_tool_call(iteration=1, tool_name="read_vault", latency_ms=12.0)
    tracker.log_budget(iteration=1, estimated_tokens=5000, budget=180_000, action="none")
    tracker.log_phase(phase="specialist", status="started")
    tracker.finish()


def test_log_model_call_accumulates_cumulative_tokens():
    """Cumulative token counter should increase across multiple calls."""
    mock_swanlab = MagicMock()
    tracker = SwanlabTracker(_run=MagicMock(), total_budget=180_000)

    with patch("forge_agent.core.swanlab_tracker._swanlab", mock_swanlab):
        tracker.log_model_call(iteration=1, input_tokens=100, output_tokens=50, latency_ms=100.0)
        assert tracker._cumulative_tokens == 150
        tracker.log_model_call(iteration=2, input_tokens=200, output_tokens=80, latency_ms=120.0)
        assert tracker._cumulative_tokens == 430


def test_log_tool_call_sanitises_metric_key():
    """Tool names with spaces and slashes should produce valid metric keys."""
    mock_swanlab = MagicMock()
    tracker = SwanlabTracker(_run=MagicMock())

    with patch("forge_agent.core.swanlab_tracker._swanlab", mock_swanlab):
        tracker.log_tool_call(
            iteration=1, tool_name="read vault/notes", latency_ms=8.0
        )

    call_args = mock_swanlab.log.call_args
    assert call_args is not None
    metrics = call_args[0][0]
    # Key must not contain spaces or slashes
    latency_key = [k for k in metrics if k.startswith("latency_ms/tool_")][0]
    assert " " not in latency_key
    assert "/" not in latency_key.removeprefix("latency_ms/")


def test_log_budget_computes_utilisation():
    """Budget utilisation percentage should be computed correctly."""
    mock_swanlab = MagicMock()
    tracker = SwanlabTracker(_run=MagicMock(), total_budget=180_000)

    with patch("forge_agent.core.swanlab_tracker._swanlab", mock_swanlab):
        tracker.log_budget(
            iteration=3, estimated_tokens=90_000, budget=180_000, action="none"
        )

    metrics = mock_swanlab.log.call_args[0][0]
    assert metrics["budget/estimated_tokens"] == 90_000
    assert metrics["budget/remaining"] == 90_000
    assert metrics["budget/utilisation_pct"] == 50.0


def test_log_phase_maps_status_to_code():
    """Phase status strings must map to the expected integer codes."""
    mock_swanlab = MagicMock()
    tracker = SwanlabTracker(_run=MagicMock())

    with patch("forge_agent.core.swanlab_tracker._swanlab", mock_swanlab):
        tracker.log_phase(phase="verification", status="started")
        assert mock_swanlab.log.call_args[0][0]["phase/verification"] == 1

        tracker.log_phase(phase="verification", status="completed")
        assert mock_swanlab.log.call_args[0][0]["phase/verification"] == 2

        tracker.log_phase(phase="verification", status="failed")
        assert mock_swanlab.log.call_args[0][0]["phase/verification"] == 3


def test_swanlab_init_failure_returns_noop_tracker():
    """If swanlab.init() raises, create() should return a no-op tracker."""
    mock_swanlab = MagicMock()
    mock_swanlab.init.side_effect = RuntimeError("connection refused")

    with patch("forge_agent.core.swanlab_tracker._SWANLAB_AVAILABLE", True), \
         patch("forge_agent.core.swanlab_tracker._swanlab", mock_swanlab):
        tracker = SwanlabTracker.create(project="test")

    assert tracker._run is None


# ── AgentLogger integration tests ─────────────────────────────────────────────


def test_agent_logger_forwards_to_tracker(tmp_path):
    """AgentLogger should forward model_call, tool_call, phase, budget to tracker."""
    tracker = MagicMock(spec=SwanlabTracker)
    log_file = tmp_path / "run.jsonl"

    with AgentLogger(log_file, run_id="test-run", tracker=tracker) as logger:
        logger.log_model_call(
            agent_role="specialist",
            model="claude-opus-4-6",
            provider="anthropic",
            input_tokens=500,
            output_tokens=200,
            latency_ms=450.0,
            iteration=1,
        )
        logger.log_tool_call(
            tool_name="search_vault",
            tool_args={},
            result="some result",
            latency_ms=15.0,
            iteration=1,
        )
        logger.log_phase("intake", "started")
        logger.log_budget(1, 5000, 180_000, "none")

    tracker.log_model_call.assert_called_once_with(
        iteration=1,
        input_tokens=500,
        output_tokens=200,
        latency_ms=450.0,
        agent_role="specialist",
        model="claude-opus-4-6",
        provider="anthropic",
        error=None,
    )
    tracker.log_tool_call.assert_called_once_with(
        iteration=1, tool_name="search_vault", latency_ms=15.0, error=None
    )
    tracker.log_phase.assert_called_once_with(phase="intake", status="started")
    tracker.log_budget.assert_called_once_with(
        iteration=1, estimated_tokens=5000, budget=180_000, action="none"
    )


def test_agent_logger_without_tracker_unchanged(tmp_path):
    """AgentLogger without a tracker must behave identically to the original."""
    log_file = tmp_path / "run.jsonl"
    with AgentLogger(log_file, run_id="no-tracker") as logger:
        logger.log_model_call(
            agent_role="specialist",
            model="claude-opus-4-6",
            provider="anthropic",
            input_tokens=100,
            output_tokens=40,
            latency_ms=200.0,
            iteration=0,
        )
        assert logger.total_input_tokens == 100
        assert logger.total_output_tokens == 40
        assert logger.total_model_calls == 1
