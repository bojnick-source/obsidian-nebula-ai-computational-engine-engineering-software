"""
ObsidianAwareContextAssembler — builds the full system prompt + conversation
context for the agent, injecting relevant vault excerpts up to max_vault_tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AssembledContext:
    system_prompt: str
    messages: list[dict]
    vault_notes_used: list[str]
    estimated_tokens: int


class ObsidianAwareContextAssembler:
    """
    Assembles context for a model call:
      1. Base system prompt (from forge.yaml)
      2. Skill-specific sections (from SKILL.md files)
      3. Vault excerpts (top-K semantic matches, truncated to max_vault_tokens)
      4. Blackboard snapshot
      5. Conversation history (already token-budget-compressed)
    """

    def __init__(
        self,
        base_prompt: str,
        max_vault_tokens: int = 4_000,
        vault_top_k: int = 5,
    ) -> None:
        self.base_prompt = base_prompt
        self.max_vault_tokens = max_vault_tokens
        self.vault_top_k = vault_top_k

    async def assemble(
        self,
        problem: str,
        messages: list[dict],
        skills: list[str],
        skill_prompts: dict[str, str],
        blackboard: dict,
        vault_manager: Any | None = None,
    ) -> AssembledContext:
        sections: list[str] = [self.base_prompt]
        vault_notes_used: list[str] = []

        # --- skill sections ---
        for skill in skills:
            if skill in skill_prompts:
                sections.append(f"\n## Skill: {skill}\n{skill_prompts[skill]}")

        # --- vault excerpts ---
        if vault_manager is not None:
            try:
                notes = await vault_manager.search(problem, top_k=self.vault_top_k)
                vault_text_budget = self.max_vault_tokens * 4  # chars
                vault_section = "\n## Relevant Vault Notes\n"
                for note in notes:
                    excerpt = _truncate(note.get("content", ""), 800)
                    title = note.get("title", "untitled")
                    entry = f"\n### {title}\n{excerpt}\n"
                    if len(vault_section) + len(entry) > vault_text_budget:
                        break
                    vault_section += entry
                    vault_notes_used.append(title)
                if vault_notes_used:
                    sections.append(vault_section)
            except Exception:
                pass

        # --- blackboard snapshot ---
        if blackboard:
            bb_text = _format_blackboard(blackboard)
            sections.append(f"\n## Current Blackboard\n```json\n{bb_text}\n```")

        system_prompt = "\n".join(sections)
        estimated = _estimate_tokens(system_prompt, messages)

        return AssembledContext(
            system_prompt=system_prompt,
            messages=messages,
            vault_notes_used=vault_notes_used,
            estimated_tokens=estimated,
        )

    def build_tool_result_message(self, tool_use_id: str, content: Any) -> dict:
        """Wrap a tool result into an Anthropic-format user message."""
        import json
        if isinstance(content, (dict, list)):
            text = json.dumps(content, indent=2, default=str)
        else:
            text = str(content)
        return {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": text}],
        }


# ------------------------------------------------------------------ helpers


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n…[truncated]"


def _format_blackboard(bb: dict) -> str:
    import json
    try:
        return json.dumps(bb, indent=2, default=str)
    except Exception:
        return str(bb)


def _estimate_tokens(system: str, messages: list[dict]) -> int:
    total = len(system)
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += len(str(block))
    return total // 4
