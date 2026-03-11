"""Unit tests for forge_agent/core/token_budget.py.

TokenBudget is pure Python with no external dependencies — ideal for unit testing.
Tests cover the enforcement cascade: compress → strip skills → drop tools → raise.
"""
from __future__ import annotations

import pytest

from forge_agent.core.token_budget import BudgetExhausted, TokenBudget, _compress_history, _estimate_tokens


# ─────────────────────────────────────────────────────────────────────────────
# Basic properties
# ─────────────────────────────────────────────────────────────────────────────


def test_initial_remaining_equals_total_budget():
    budget = TokenBudget(total_budget=10_000)
    assert budget.remaining == 10_000


def test_consume_reduces_remaining():
    budget = TokenBudget(total_budget=10_000)
    budget.consume(3_000)
    assert budget.remaining == 7_000
    assert budget.used == 3_000


def test_remaining_never_negative():
    budget = TokenBudget(total_budget=1_000)
    budget.consume(5_000)  # over-consume
    assert budget.remaining == 0  # clamped at 0


def test_reset_clears_usage():
    budget = TokenBudget(total_budget=10_000)
    budget.consume(4_000)
    budget.reset()
    assert budget.remaining == 10_000
    assert budget.used == 0


# ─────────────────────────────────────────────────────────────────────────────
# enforce() — within budget
# ─────────────────────────────────────────────────────────────────────────────


def test_enforce_returns_unchanged_when_within_budget():
    """When estimated tokens fit within the budget, enforce returns inputs unchanged."""
    budget = TokenBudget(total_budget=100_000)
    messages = [{"role": "user", "content": "hello"}]
    system = "You are an engineering assistant."
    tools = [{"name": "fea_tool"}]
    skills = ["skill prompt"]

    out_msgs, out_sys, out_tools, out_skills = budget.enforce(messages, system, tools, skills)

    assert out_msgs == messages
    assert out_sys == system
    assert out_tools == tools
    assert out_skills == skills


# ─────────────────────────────────────────────────────────────────────────────
# enforce() — over budget: cascade steps
# ─────────────────────────────────────────────────────────────────────────────


def test_enforce_strips_skills_when_over_budget():
    """When over budget, skill prompts should be dropped as part of the cascade."""
    # Tiny budget forces the cascade
    budget = TokenBudget(total_budget=5)

    messages = [{"role": "user", "content": "x"}]
    system = "y"
    tools: list = []
    skills = ["a" * 100]  # large enough to push over tiny budget

    _, _, _, out_skills = budget.enforce(messages, system, tools, skills)
    assert out_skills == [], "Skills should be stripped when over budget"


def test_enforce_drops_tools_when_over_budget():
    """When over budget and skills stripped, tools should be dropped."""
    budget = TokenBudget(total_budget=5)

    messages = [{"role": "user", "content": "x"}]
    system = "y"
    tools = [{"name": "t", "description": "a" * 100}]
    skills: list = []

    _, _, out_tools, _ = budget.enforce(messages, system, tools, skills)
    assert out_tools == [], "Tools should be dropped when over budget"


def test_enforce_raises_budget_exhausted_when_still_over():
    """When even tool-stripping is insufficient, BudgetExhausted must be raised."""
    # Budget so small nothing fits
    budget = TokenBudget(total_budget=1)

    # Content that cannot be reduced
    messages = [{"role": "user", "content": "x" * 100}]
    system = "y" * 100
    tools: list = []
    skills: list = []

    with pytest.raises(BudgetExhausted):
        budget.enforce(messages, system, tools, skills)


# ─────────────────────────────────────────────────────────────────────────────
# _compress_history()
# ─────────────────────────────────────────────────────────────────────────────


def test_compress_history_short_messages_unchanged():
    """History with ≤ 8 messages must be returned unchanged."""
    msgs = [{"role": "user", "content": f"msg{i}"} for i in range(8)]
    assert _compress_history(msgs) == msgs


def test_compress_history_long_keeps_first_and_last_six():
    """History with > 8 messages must keep first message + last 6."""
    msgs = [{"role": "user", "content": f"msg{i}"} for i in range(20)]
    compressed = _compress_history(msgs)
    assert compressed[0] == msgs[0], "First message must be preserved"
    assert compressed[-6:] == msgs[-6:], "Last 6 messages must be preserved"
    assert len(compressed) == 7  # 1 first + 6 last


def test_compress_history_exactly_9_messages():
    """Boundary: exactly 9 messages → keep first + last 6 = 7."""
    msgs = [{"role": "user", "content": f"msg{i}"} for i in range(9)]
    compressed = _compress_history(msgs)
    assert len(compressed) == 7


# ─────────────────────────────────────────────────────────────────────────────
# _estimate_tokens()
# ─────────────────────────────────────────────────────────────────────────────


def test_estimate_tokens_scales_with_content():
    """Larger content should produce a higher token estimate."""
    short = _estimate_tokens([], "short", [], [])
    long_est = _estimate_tokens([], "a" * 400, [], [])
    assert long_est > short


def test_estimate_tokens_includes_messages():
    """Token estimate must increase when messages are added."""
    base = _estimate_tokens([], "system", [], [])
    with_msg = _estimate_tokens([{"role": "user", "content": "a" * 400}], "system", [], [])
    assert with_msg > base


def test_estimate_tokens_empty_returns_small_value():
    """Empty inputs should return a small (possibly zero) token estimate."""
    result = _estimate_tokens([], "", [], [])
    assert result >= 0
