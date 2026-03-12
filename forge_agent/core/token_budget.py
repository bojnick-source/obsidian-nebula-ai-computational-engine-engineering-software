"""Token budget enforcement: compress → strip skills → drop tools → error."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenBudget:
    """Track and enforce the per-session token budget.

    Enforcement cascade:
      1. Compress conversation history (summarise)
      2. Strip low-priority skill system prompts
      3. Drop tool definitions
      4. Raise BudgetExhausted (cannot proceed)
    """
    total_budget: int = 180_000
    max_vault_tokens: int = 4_000
    history_soft_limit: int = 60_000    # compress history above this
    _used: int = field(default=0, init=False)

    @property
    def remaining(self) -> int:
        return max(0, self.total_budget - self._used)

    @property
    def used(self) -> int:
        return self._used

    def consume(self, tokens: int) -> None:
        self._used += tokens

    def reset(self) -> None:
        self._used = 0

    def enforce(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str,
        tools: list[dict[str, Any]],
        skill_prompts: list[str],
    ) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]], list[str]]:
        """Return (messages, system, tools, skills) pruned to fit within budget.

        Cascade: compress history → strip low-priority skills → drop tools.
        Raises BudgetExhausted if budget cannot be respected.
        """
        # Stage 0: history soft limit pre-check (compress even when under total budget)
        history_tokens = _estimate_tokens(messages, "", [], [])
        if history_tokens > self.history_soft_limit:
            messages = _compress_history(messages)

        estimated = _estimate_tokens(messages, system_prompt, tools, skill_prompts)
        if estimated <= self.remaining:
            return messages, system_prompt, tools, skill_prompts

        # 1. Compress history
        messages = _compress_history(messages)
        estimated = _estimate_tokens(messages, system_prompt, tools, skill_prompts)
        if estimated <= self.remaining:
            return messages, system_prompt, tools, skill_prompts

        # 2. Strip skill prompts (keep none — rely on base system prompt)
        skill_prompts = []
        estimated = _estimate_tokens(messages, system_prompt, tools, skill_prompts)
        if estimated <= self.remaining:
            return messages, system_prompt, tools, skill_prompts

        # 3. Drop tool definitions
        tools = []
        estimated = _estimate_tokens(messages, system_prompt, tools, skill_prompts)
        if estimated <= self.remaining:
            return messages, system_prompt, tools, skill_prompts

        raise BudgetExhausted(
            f"Token budget exhausted: need ~{estimated}, have {self.remaining}"
        )

    def _estimate_tokens(
        self,
        messages: list[dict[str, Any]],
        system: str,
        tools: list[dict[str, Any]],
        skill_prompts: list[str],
    ) -> int:
        return _estimate_tokens(messages, system, tools, skill_prompts)

    def _compress_history(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return _compress_history(messages)


class BudgetExhausted(RuntimeError):
    pass


def _estimate_tokens(
    messages: list[dict[str, Any]],
    system: str,
    tools: list[dict[str, Any]],
    skill_prompts: list[str],
) -> int:
    """Rough token count: 4 chars ≈ 1 token."""
    text = system + "".join(skill_prompts)
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text += block.get("text", "") + str(block.get("input", ""))
        else:
            text += str(content)
    for tool in tools:
        text += str(tool)
    return len(text) // 4


def _compress_history(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep first message + last 6 messages, drop the middle."""
    if len(messages) <= 8:
        return messages
    return [messages[0]] + messages[-6:]
