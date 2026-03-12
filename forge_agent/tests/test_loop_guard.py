"""Tests for AgentLoopGuard."""
import pytest
from forge_agent.core.loop_guard import (
    AgentLoopGuard,
    LoopDivergenceError,
    LoopLimitError,
)


class TestAgentLoopGuard:
    def test_tick_increments_iteration(self):
        guard = AgentLoopGuard(max_iterations=25)
        assert guard.tick() == 1
        assert guard.tick() == 2
        assert guard.iteration == 2

    def test_tick_raises_on_limit(self):
        guard = AgentLoopGuard(max_iterations=3)
        guard.tick()
        guard.tick()
        guard.tick()
        with pytest.raises(LoopLimitError):
            guard.tick()  # 4th tick exceeds max=3

    def test_remaining_decreases(self):
        guard = AgentLoopGuard(max_iterations=10)
        guard.tick()
        guard.tick()
        assert guard.remaining == 8

    def test_record_tool_call_no_error_on_first(self):
        guard = AgentLoopGuard()
        guard.record_tool_call("run_fea", {"mesh": "fine"})  # no error

    def test_divergence_on_repeated_calls(self):
        guard = AgentLoopGuard(divergence_threshold=3)
        guard.record_tool_call("fea_run", {"mesh": "coarse"})
        guard.record_tool_call("fea_run", {"mesh": "coarse"})
        with pytest.raises(LoopDivergenceError):
            guard.record_tool_call("fea_run", {"mesh": "coarse"})  # 3rd identical call

    def test_different_args_no_divergence(self):
        guard = AgentLoopGuard(divergence_threshold=3)
        guard.record_tool_call("fea_run", {"mesh": "coarse"})
        guard.record_tool_call("fea_run", {"mesh": "fine"})  # different args
        guard.record_tool_call("fea_run", {"mesh": "coarse"})  # same as first but not 3rd consecutive
        # Should not raise

    def test_different_tools_no_divergence(self):
        guard = AgentLoopGuard(divergence_threshold=3)
        # Different tools have independent counters; same args on different tools don't interfere
        guard.record_tool_call("tool_a", {"x": 1})
        guard.record_tool_call("tool_b", {"x": 1})
        guard.record_tool_call("tool_c", {"x": 1})
        guard.record_tool_call("tool_a", {"x": 1})
        guard.record_tool_call("tool_b", {"x": 1})
        # Each tool called ≤ 2 times; threshold=3 not yet reached for any
        # Third call to tool_a triggers divergence:
        with pytest.raises(LoopDivergenceError):
            guard.record_tool_call("tool_a", {"x": 1})  # 3rd call to tool_a raises

    def test_reset_clears_state(self):
        guard = AgentLoopGuard(max_iterations=5)
        guard.tick()
        guard.tick()
        guard.record_tool_call("t", {"a": 1})
        guard.reset()
        assert guard.iteration == 0
        assert guard.remaining == 5
        # Should not raise after reset
        guard.record_tool_call("t", {"a": 1})
        guard.record_tool_call("t", {"a": 1})
