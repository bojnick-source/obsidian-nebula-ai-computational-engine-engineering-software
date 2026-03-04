"""FORGE Vault Memory layer (Component C).

Reads and writes Obsidian vault notes with YAML frontmatter.
MVP: file-system I/O only (Supermemory deferred; see ADR-003).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VaultNote:
    """In-memory representation of one Obsidian vault note.

    Attributes:
        path:       Relative path inside the vault (e.g. ``domains/mechanical/beam_theory.md``).
        title:      Note title from frontmatter.
        domain:     Domain tag (``mechanical`` | ``materials`` | ``thermal`` | ``general``).
        confidence: Epistemic confidence in the content (0.0–1.0).
        sources:    Provenance references.
        gap_flags:  Known knowledge gaps.
        body:       Markdown body text (below frontmatter).
    """

    path: str = ""
    title: str = ""
    domain: str = "general"
    confidence: float = 0.0
    sources: list[str] = field(default_factory=list)
    gap_flags: list[str] = field(default_factory=list)
    body: str = ""


class VaultStore:
    """File-backed vault store rooted at *vault_root*.

    Provides read / write / list / search stubs that the Librarian
    agent delegates to.  Full implementation arrives in M3.
    """

    def __init__(self, vault_root: Path) -> None:
        self.vault_root = vault_root

    def read_note(self, rel_path: str) -> VaultNote | None:
        """Read a vault note.  Returns ``None`` if the file is absent."""
        full = self.vault_root / rel_path
        if not full.exists():
            return None
        text = full.read_text(encoding="utf-8")
        return VaultNote(path=rel_path, body=text)

    def write_note(self, note: VaultNote) -> Path:
        """Persist a ``VaultNote`` to disk and return its absolute path."""
        full = self.vault_root / note.path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(note.body, encoding="utf-8")
        return full

    def list_notes(self, domain: str | None = None) -> list[str]:
        """List relative paths of ``.md`` files, optionally filtered by *domain* sub-dir."""
        search_root = self.vault_root
        if domain:
            search_root = self.vault_root / "domains" / domain
        if not search_root.exists():
            return []
        return [
            str(p.relative_to(self.vault_root))
            for p in search_root.rglob("*.md")
        ]
