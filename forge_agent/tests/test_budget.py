"""Tests for TokenBudget enforcement cascade."""
import pytest
from forge_agent.core.token_budget import BudgetExhausted, TokenBudget


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
        budget = TokenBudget(total_budget=180_000, history_soft_limit=100)
        # 20 messages × 100 chars = 2000 chars → estimated 500 tokens → over soft limit
        msgs = _make_messages(20, chars_each=100)
        system = "s"
        out_msgs, _, _, _ = budget.enforce(msgs, system, [], [])
        # Should compress to first + last 6
        assert len(out_msgs) <= 8

    def test_skill_prompts_stripped_when_over_budget(self):
        # total ≈ 663 tokens (2×500 chars msgs + 400 sys + 1200 skills + 53 tools) / 4
        # budget=600 < 663 → cascade fires; after stripping skills ≈ 363 ≤ 600
        budget = TokenBudget(total_budget=600)
        msgs = _make_messages(2, chars_each=500)  # 1000 chars → 250 tokens
        system = "s" * 400  # 100 tokens
        skill_prompts = ["x" * 1200]  # 300 tokens
        tools = [{"name": "t", "description": "d", "input_schema": {}}]
        out_msgs, out_sys, out_tools, out_sp = budget.enforce(msgs, system, tools, skill_prompts)
        assert out_sp == []

    def test_tools_dropped_after_skill_strip(self):
        # total ≈ 313 tokens (2×400 chars msgs + 200 sys + 252 tools) / 4
        # budget=300 < 313 → cascade fires; after dropping tools ≈ 250 ≤ 300
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
        budget = TokenBudget()
        msgs = [{"role": "user", "content": "a" * 400}]
        system = "b" * 400
        # 800 chars total → ~200 tokens
        result = budget._estimate_tokens(msgs, system, [], [])
        assert 150 <= result <= 250

    def test_compress_history_keeps_first_and_last(self):
        budget = TokenBudget()
        msgs = _make_messages(12)
        compressed = budget._compress_history(msgs)
        assert compressed[0] == msgs[0]
        assert compressed[-1] == msgs[-1]
        assert len(compressed) == 7  # first + last 6

    def test_compress_history_no_op_when_short(self):
        budget = TokenBudget()
        msgs = _make_messages(5)
        assert budget._compress_history(msgs) == msgs
