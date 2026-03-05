"""WorkingMemoryManager — 81% token offload to task memory.

Manages the active blackboard context window: when token count exceeds
threshold, summarizes and offloads to Obsidian 04-Analyses/ task memory.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import anthropic


_DEFAULT_TOKEN_THRESHOLD = 20_000  # Offload at 20k to stay within context budget


class WorkingMemoryManager:
    """Track working memory token usage and offload when threshold exceeded."""

    def __init__(
        self,
        vault_path: Path,
        token_threshold: int = _DEFAULT_TOKEN_THRESHOLD,
        model: str = "claude-haiku-4-5-20251001",
    ) -> None:
        self._vault_path = vault_path
        self._threshold = token_threshold
        self._model = model
        self._buffer: list[dict[str, Any]] = []
        self._token_count = 0

    def add_entry(self, entry: dict[str, Any], token_estimate: int) -> None:
        """Add a working memory entry. Triggers offload if threshold exceeded."""
        self._buffer.append(entry)
        self._token_count += token_estimate
        if self._token_count >= self._threshold:
            self.offload_to_task_memory()

    def offload_to_task_memory(self) -> Path | None:
        """Summarize buffer and write to vault task memory."""
        if not self._buffer:
            return None

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        buffer_text = "\n\n".join(
            f"[{e.get('agent', '?')}] {e.get('content', str(e))}"
            for e in self._buffer
        )

        response = client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Compress the following engineering analysis working memory into a "
                        "dense summary preserving all critical findings, decisions, and "
                        "numerical results. Discard repetition. Keep all assumptions explicit.\n\n"
                        f"{buffer_text}"
                    ),
                }
            ],
        )

        summary = response.content[0].text.strip()
        note_path = self._vault_path / "04-Analyses" / f"working-memory-offload-{_ts()}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(f"# Working Memory Offload\n\n{summary}\n", encoding="utf-8")

        # Clear buffer
        self._buffer.clear()
        self._token_count = 0
        return note_path

    @property
    def token_count(self) -> int:
        return self._token_count

    @property
    def buffer_size(self) -> int:
        return len(self._buffer)


def _ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
