"""Entity registry + semantic auto-linking for vault notes."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


class AutoLinker:
    """Insert [[wikilinks]] for known entities in note body text.

    Loaded from configs/entity_registry_seed.yaml.
    """

    def __init__(self, registry_path: Path) -> None:
        self._entities: dict[str, str] = {}  # term → note_id
        self._load(registry_path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            return
        with path.open() as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
        for entry in data.get("entities", []):
            term: str = entry.get("term", "")
            note_id: str = entry.get("note_id", term)
            aliases: list[str] = entry.get("aliases", [])
            if term:
                self._entities[term] = note_id
            for alias in aliases:
                self._entities[alias] = note_id

    def link(self, text: str) -> str:
        """Replace entity mentions with [[note_id|term]] wikilinks."""
        # Sort longest first to avoid partial replacement (e.g. 'steel' before 'stainless steel')
        for term in sorted(self._entities, key=len, reverse=True):
            note_id = self._entities[term]
            replacement = f"[[{note_id}|{term}]]"
            # Word-boundary match, case-insensitive
            text = re.sub(
                rf"(?<!\[\[)\b{re.escape(term)}\b(?!\]\])",
                replacement,
                text,
                flags=re.IGNORECASE,
            )
        return text

    def register(self, term: str, note_id: str, aliases: list[str] | None = None) -> None:
        """Dynamically add an entity to the live registry."""
        self._entities[term] = note_id
        for alias in aliases or []:
            self._entities[alias] = note_id
