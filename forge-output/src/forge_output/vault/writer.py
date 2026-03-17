"""VaultWriter — create Obsidian notes with FORGE frontmatter (Context 1C).

Uses python-frontmatter for note serialization.
Uses Supermemory for agent-optimized retrieval after write.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter

try:
    from supermemory import Supermemory
    _SUPERMEMORY_AVAILABLE = True
except ImportError:
    _SUPERMEMORY_AVAILABLE = False


_CONTAINER_TAG = "forge-vault"

# Vault root paths (relative to vault root, no leading slash)
NOTE_TYPE_PATHS = {
    "finding": "04-Analyses",
    "gap": "05-Gaps",
    "agent-thinking": "06-AgentThinking",
    "contradiction": "07-Contradictions",
    "verification-result": "04-Analyses",
    "project-brief": "01-Projects",
    "material-datasheet": "02-Reference/Materials",
}


class VaultWriter:
    """Write FORGE-formatted notes to an Obsidian vault directory."""

    def __init__(
        self,
        vault_root: Path,
        supermemory_api_key: str | None = None,
    ) -> None:
        self._vault_root = vault_root
        self._sm: Any | None = None
        if _SUPERMEMORY_AVAILABLE and supermemory_api_key:
            self._sm = Supermemory(api_key=supermemory_api_key)

    def write_note(
        self,
        note_type: str,
        title: str,
        body: str,
        metadata: dict[str, Any],
        run_id: str,
        trace_id: str,
        agent_id: str,
        quality_score: float = 0.0,
        task_id: str = "",
    ) -> Path:
        """Serialize and write a vault note; add to Supermemory if configured."""
        note_id = self._slug(title)
        vault_path = NOTE_TYPE_PATHS.get(note_type, "04-Analyses")
        note_dir = self._vault_root / vault_path
        note_dir.mkdir(parents=True, exist_ok=True)
        note_path = note_dir / f"{note_id}.md"

        fm: dict[str, Any] = {
            "note_id": note_id,
            "note_type": note_type,
            "title": title,
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "trace_id": trace_id,
            "task_id": task_id,
            "run_id": run_id,
            "agent_id": agent_id,
            "pathway_strength": 1.0,
            "provenance": metadata.get("provenance", ""),
            "confidence": metadata.get("confidence", 0.0),
            "quality_score": quality_score,
            "status": "active",
            "tags": metadata.get("tags", []),
        }
        fm.update({k: v for k, v in metadata.items() if k not in fm})

        post = frontmatter.Post(body, **fm)
        content = frontmatter.dumps(post)
        note_path.write_text(content, encoding="utf-8")

        if self._sm is not None:
            try:
                self._sm.add(content, container_tag=_CONTAINER_TAG)
            except Exception:
                pass

        return note_path

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _slug(title: str) -> str:
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug.strip("-")[:80]
