"""
forge_agent/agents/librarian.py

Librarian agent — gatekeeper between blackboard and Obsidian vault.

Implements:
  - intake(note_dict) → str path
  - retrieve(domain, component, top_k) → list[dict]
  - amnesia_check(path) → bool
  - detect_gaps(blackboard) → list[str]
"""
from __future__ import annotations

from datetime import datetime, timezone

from forge_agent.memory.obsidian_manager import ObsidianVaultManager


class LibrarianAgent:
    def __init__(self, vault_manager: ObsidianVaultManager) -> None:
        self._vault = vault_manager

    def intake(self, note_dict: dict) -> str:
        """Classify and write note to vault; return the vault-relative path."""
        project = note_dict.get("project", "unknown")
        component = note_dict.get("component", "unknown")
        trace_id = note_dict.get("trace_id", "untitled")
        path = f"projects/{project}/components/{component}/{trace_id}.md"

        frontmatter = {
            "type": "finding",
            "domain": note_dict.get("domain", ""),
            "component": component,
            "project": project,
            "trace_id": trace_id,
            "confidence": note_dict.get("confidence", 0.0),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        markdown_body = note_dict.get("content", "")
        self._vault.upsert_note(path, markdown_body, frontmatter)
        return path

    def retrieve(self, domain: str, component: str, top_k: int = 5) -> list[dict]:
        """Search vault and return notes matching domain and component.

        Never raises — returns an empty list on any error.
        """
        try:
            results = self._vault.search_notes(query=component)
            filtered = []
            for item in results:
                fm = item.frontmatter if hasattr(item, "frontmatter") else {}
                if fm.get("domain") == domain and fm.get("component") == component:
                    filtered.append({
                        "path": item.path if hasattr(item, "path") else "",
                        "title": item.title if hasattr(item, "title") else "",
                        "frontmatter": fm,
                        "excerpt": item.excerpt if hasattr(item, "excerpt") else "",
                        "score": item.score if hasattr(item, "score") else 0.0,
                    })
            return filtered[:top_k]
        except Exception:
            return []

    def amnesia_check(self, path: str) -> bool:
        """Return True iff path is immediately retrievable post-write."""
        return self._vault.amnesia_check(path)

    def detect_gaps(self, blackboard: dict) -> list[str]:
        """Identify knowledge gaps from blackboard state.

        Returns a list of gap description strings; empty list means no gaps.
        """
        gaps: list[str] = []
        if not blackboard.get("specialist.result"):
            gaps.append("no specialist output")
        if "tool_results.calculix" not in blackboard:
            gaps.append("no FEA results")
        if blackboard.get("verification.status") == "failed":
            gaps.append("verification failed")
        return gaps
