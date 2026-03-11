"""Tests for TokenBudget enforcement cascade."""
import pytest
from forge_agent.core.token_budget import (
    BudgetExhausted,
    TokenBudget,
    _compress_history,
    _estimate_tokens,
)


def _make_messages(n: int, chars_each: int = 100) -> list[dict]:
    return [{"role": "user" if i % 2 == 0 else "assistant", "content": "x" * chars_each}
            for i in range(n)]


class TestTokenBudget:
    def test_no_enforcement_needed_within_budget(self):
        budget = TokenBudget(total_budget=180_000)
        msgs = _make_messages(4, chars_each=100)
        system = "short system prompt"
        tools: list = []
        skill_prompts: list = []
        out_msgs, out_sys, out_tools, out_sp = budget.enforce(msgs, system, tools, skill_prompts)
        assert out_msgs == msgs
        assert out_sys == system
        assert out_tools == tools

    def test_history_compression_on_long_messages(self):
        # 20 msgs × 100 chars = 2000 chars → ~500 tokens. Budget of 200 forces compression.
        # After compression: 7 msgs × 100 chars = ~175 tokens < 200 → fits.
        budget = TokenBudget(total_budget=200)
        msgs = _make_messages(20, chars_each=100)
        system = "s"
        out_msgs, _, _, _ = budget.enforce(msgs, system, [], [])
        # Should compress to first + last 6 = 7 messages
        assert len(out_msgs) <= 8

    def test_skill_prompts_stripped_when_over_budget(self):
        # msgs=2×500=1000chars~250tok, system=400chars~100tok, skill=1200chars~300tok → ~650 total
        # Budget 600 < 650: compress (no-op on 2 msgs) → still >600 → strip skills → ~350 < 600
        budget = TokenBudget(total_budget=600)
        msgs = _make_messages(2, chars_each=500)
        system = "s" * 400
        skill_prompts = ["x" * 1200]
        tools = [{"name": "t", "description": "d", "input_schema": {}}]
        out_msgs, out_sys, out_tools, out_sp = budget.enforce(msgs, system, tools, skill_prompts)
        assert out_sp == []

    def test_tools_dropped_after_skill_strip(self):
        # msgs=2×400=800chars~200tok, system=200chars~50tok, tools~80tok → ~330 total
        # Budget 300 < 330: compress (no-op), strip skills (none), drop tools → ~250 < 300
        budget = TokenBudget(total_budget=300)
        msgs = _make_messages(2, chars_each=400)
        system = "s" * 200
        tools = [{"name": "t", "description": "d" * 200, "input_schema": {}}]
        out_msgs, out_sys, out_tools, out_sp = budget.enforce(msgs, system, tools, [])
        assert out_tools == []

    def test_budget_exhausted_raises(self):
        budget = TokenBudget(total_budget=10)  # impossibly small
        msgs = [{"role": "user", "content": "x" * 1000}]
        system = "x" * 1000
        with pytest.raises(BudgetExhausted):
            budget.enforce(msgs, system, [], [])

    def test_estimate_tokens_proportional(self):
        # _estimate_tokens is a module-level function, not an instance method
        msgs = [{"role": "user", "content": "a" * 400}]
        system = "b" * 400
        # 800 chars total → ~200 tokens (800 // 4 = 200)
        result = _estimate_tokens(msgs, system, [], [])
        assert 150 <= result <= 250

    def test_compress_history_keeps_first_and_last(self):
        # _compress_history is a module-level function, not an instance method
        msgs = _make_messages(12)
        compressed = _compress_history(msgs)
        assert compressed[0] == msgs[0]
        assert compressed[-1] == msgs[-1]
        assert len(compressed) == 7  # first + last 6

    def test_compress_history_no_op_when_short(self):
        msgs = _make_messages(5)
        assert _compress_history(msgs) == msgs
