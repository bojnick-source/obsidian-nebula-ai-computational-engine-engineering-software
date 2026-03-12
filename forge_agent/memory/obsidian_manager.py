"""
ObsidianVaultManager — async, lazy-indexed, filesystem-direct vault interface.

Provides:
  - search(query, top_k) → list[dict]  (TF-IDF fallback when no embedding service)
  - read_note(title) → str | None
  - write_note(title, content, frontmatter) → Path
  - distill(notes, prompt) → str        (LLM-powered summarisation)
  - flush()                              (drain write queue — for GracefulShutdown)
"""

from __future__ import annotations

import asyncio
import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VaultNote:
    title: str
    path: Path
    content: str
    frontmatter: dict = field(default_factory=dict)
    indexed_at: float = field(default_factory=time.time)


class ObsidianVaultManager:
    def __init__(
        self,
        vault_path: str | Path,
        llm_client: Any | None = None,
    ) -> None:
        self.vault_path = Path(vault_path)
        self._client = llm_client
        self._index: dict[str, VaultNote] = {}
        self._indexed = False
        self._index_lock = asyncio.Lock()
        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._write_task: asyncio.Task | None = None

    # ---------------------------------------------------------------- lifecycle

    async def start(self) -> None:
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self._write_task = asyncio.create_task(self._write_worker(), name="vault-write")
        await self._ensure_indexed()

    async def flush(self) -> None:
        """Drain the write queue (used by GracefulShutdown)."""
        await self._write_queue.join()

    async def stop(self) -> None:
        await self.flush()
        if self._write_task:
            self._write_task.cancel()

    # ---------------------------------------------------------------- read

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        await self._ensure_indexed()
        if not self._index:
            return []
        scores = _tfidf_score(query, list(self._index.values()))
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for title, score in ranked:
            note = self._index[title]
            results.append({
                "title": note.title,
                "content": note.content[:2000],
                "score": round(score, 4),
                "path": str(note.path),
            })
        return results

    async def read_note(self, title: str) -> str | None:
        await self._ensure_indexed()
        note = self._index.get(_slug(title))
        if note is None:
            return None
        return note.content

    # ---------------------------------------------------------------- MCP server API (sync)
    # These synchronous methods are called by obsidian_mcp_server.py via FastMCP tools.
    # They use the in-memory index directly after ensuring it is built.

    def _ensure_indexed_sync(self) -> None:
        """Build the index synchronously if not yet done (used by sync MCP tools)."""
        if not self._indexed:
            self._build_index()
            self._indexed = True

    def search_notes(
        self,
        query: str,
        top_k: int = 5,
        domain: str | None = None,
        tags: list[str] | None = None,
        min_confidence: float | None = None,
    ) -> list[Any]:
        """Synchronous full-text search with optional domain/tag/confidence filters.

        Returns a list of result objects with .path, .title, .excerpt,
        .frontmatter, .score, and .backlinks attributes.
        """
        self._ensure_indexed_sync()
        if not self._index:
            return []

        notes = list(self._index.values())

        # Apply domain filter (vault-relative directory prefix)
        if domain:
            notes = [n for n in notes if str(n.path).replace("\\", "/").find(domain) >= 0]

        # Apply tag filter
        if tags:
            tag_set = set(tags)
            notes = [
                n for n in notes
                if tag_set.intersection(
                    t.strip() for t in str(n.frontmatter.get("tags", "")).split(",")
                )
            ]

        # Apply minimum confidence filter
        if min_confidence is not None:
            notes = [
                n for n in notes
                if float(n.frontmatter.get("confidence", 1.0)) >= min_confidence
            ]

        scores = _tfidf_score(query, notes) if notes else {}
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Build backlink map once
        backlink_map: dict[str, list[str]] = {}
        for n in self._index.values():
            for link in _extract_wikilinks(n.content):
                backlink_map.setdefault(link, []).append(str(n.path))

        results = []
        for slug, score in ranked:
            note = self._index.get(slug)
            if note is None:
                continue
            path_str = str(note.path)
            results.append(_NoteResult(
                path=path_str,
                title=note.title,
                excerpt=note.content[:300],
                frontmatter=note.frontmatter,
                score=round(score, 4),
                backlinks=backlink_map.get(note.title, []),
            ))
        return results

    def get_note(self, path: str) -> Any | None:
        """Return a note by vault-relative path, or None if not found.

        Returns an object with .path, .title, .frontmatter, .body,
        .sections, .tags, .outgoing_links, and .modified attributes.
        """
        self._ensure_indexed_sync()
        # Search by exact path match across the index
        target = Path(path)
        for note in self._index.values():
            try:
                if note.path.resolve() == (self.vault_path / target).resolve():
                    return _FullNote(
                        path=str(note.path.relative_to(self.vault_path)),
                        title=note.title,
                        frontmatter=note.frontmatter,
                        body=note.content,
                        sections=_extract_sections(note.content),
                        tags=[
                            t.strip()
                            for t in str(note.frontmatter.get("tags", "")).split(",")
                            if t.strip()
                        ],
                        outgoing_links=_extract_wikilinks(note.content),
                        modified=note.indexed_at,
                    )
            except ValueError:
                pass
        return None

    def get_backlinks(self, path: str) -> list[str]:
        """Return all vault-relative paths whose notes contain [[wiki links]] to path."""
        self._ensure_indexed_sync()
        target_stem = Path(path).stem
        return [
            str(n.path)
            for n in self._index.values()
            if target_stem in _extract_wikilinks(n.content)
        ]

    def get_tags(self, tag: str) -> list[str]:
        """Return vault-relative paths of all notes that carry the given tag."""
        self._ensure_indexed_sync()
        return [
            str(n.path)
            for n in self._index.values()
            if tag in [
                t.strip()
                for t in str(n.frontmatter.get("tags", "")).split(",")
            ]
        ]

    def upsert_note(
        self,
        path: str,
        markdown: str,
        frontmatter: dict | None = None,
        provenance: dict | None = None,
    ) -> str:
        """Create or overwrite a vault note synchronously.

        Returns the absolute path of the written file.
        """
        self._ensure_indexed_sync()
        fm = dict(frontmatter or {})
        if provenance:
            fm["_provenance"] = str(provenance)
        file_path = self.vault_path / path
        self._write_sync(Path(path).stem, markdown, fm, file_path)
        slug = _slug(Path(path).stem)
        self._index[slug] = VaultNote(
            title=Path(path).stem,
            path=file_path,
            content=markdown,
            frontmatter=fm,
        )
        return str(file_path)

    def append_to_note(self, path: str, markdown: str) -> str:
        """Append markdown to an existing note (creates it if missing).

        Returns the absolute path of the modified file.
        """
        self._ensure_indexed_sync()
        file_path = self.vault_path / path
        if file_path.exists():
            existing = file_path.read_text(encoding="utf-8")
            combined = existing.rstrip() + "\n\n" + markdown
        else:
            combined = markdown
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(combined, encoding="utf-8")
        slug = _slug(Path(path).stem)
        note = self._index.get(slug)
        if note:
            note.content = combined
        return str(file_path)

    def add_frontmatter(self, path: str, yaml_patch: dict) -> str:
        """Patch frontmatter fields without touching the note body.

        Returns the absolute path of the modified file.
        """
        self._ensure_indexed_sync()
        file_path = self.vault_path / path
        if file_path.exists():
            raw = file_path.read_text(encoding="utf-8")
            fm, body = _parse_frontmatter(raw)
        else:
            fm, body = {}, ""
        fm.update(yaml_patch)
        self._write_sync(Path(path).stem, body, fm, file_path)
        slug = _slug(Path(path).stem)
        note = self._index.get(slug)
        if note:
            note.frontmatter = fm
        return str(file_path)

    # ---------------------------------------------------------------- write

    async def write_note(
        self,
        title: str,
        content: str,
        frontmatter: dict | None = None,
        folder: str = "",
    ) -> Path:
        """Queue a vault write; returns the target path immediately."""
        folder_path = self.vault_path / folder if folder else self.vault_path
        file_path = folder_path / f"{_slug(title)}.md"
        await self._write_queue.put((title, content, frontmatter or {}, file_path))
        return file_path

    # ---------------------------------------------------------------- distill

    async def distill(self, notes: list[dict], prompt: str) -> str:
        """LLM-powered summarisation of vault notes."""
        if not notes or self._client is None:
            return "\n\n".join(n.get("content", "") for n in notes[:3])

        combined = "\n\n---\n\n".join(
            f"# {n['title']}\n{n['content'][:1500]}" for n in notes
        )
        msg = await self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        f"Vault notes:\n{combined}\n\n"
                        "Provide a concise technical summary."
                    ),
                }
            ],
        )
        return msg.content[0].text

    # ---------------------------------------------------------------- private

    async def _ensure_indexed(self) -> None:
        if self._indexed:
            return
        async with self._index_lock:
            if self._indexed:
                return
            await asyncio.get_event_loop().run_in_executor(None, self._build_index)
            self._indexed = True

    def _build_index(self) -> None:
        """Synchronous index build — run in executor."""
        for md_file in self.vault_path.rglob("*.md"):
            try:
                raw = md_file.read_text(encoding="utf-8", errors="replace")
                fm, body = _parse_frontmatter(raw)
                title = fm.get("title", md_file.stem)
                slug = _slug(title)
                self._index[slug] = VaultNote(
                    title=title,
                    path=md_file,
                    content=body,
                    frontmatter=fm,
                )
            except Exception:
                pass

    async def _write_worker(self) -> None:
        while True:
            try:
                title, content, fm, file_path = await self._write_queue.get()
                await asyncio.get_event_loop().run_in_executor(
                    None, self._write_sync, title, content, fm, file_path
                )
                # Update in-memory index
                slug = _slug(title)
                self._index[slug] = VaultNote(
                    title=title, path=file_path, content=content, frontmatter=fm
                )
                self._write_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                self._write_queue.task_done()

    def _write_sync(self, title: str, content: str, fm: dict, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fm_lines = ["---"]
        for k, v in fm.items():
            fm_lines.append(f"{k}: {v!r}")
        fm_lines.append("---\n")
        fm_text = "\n".join(fm_lines)
        file_path.write_text(fm_text + content, encoding="utf-8")


# ------------------------------------------------------------------ helpers


def _slug(title: str) -> str:
    return re.sub(r"[^\w-]", "_", title.lower().strip())


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown."""
    if not raw.startswith("---"):
        return {}, raw
    try:
        end = raw.index("---", 3)
        fm_text = raw[3:end].strip()
        body = raw[end + 3:].strip()
        fm: dict = {}
        for line in fm_text.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()
        return fm, body
    except ValueError:
        return {}, raw


def _tfidf_score(query: str, notes: list[VaultNote]) -> dict[str, float]:
    """Simple TF-IDF scoring for search."""
    tokens = _tokenize(query)
    if not tokens:
        return {}

    # IDF
    N = len(notes)
    df: dict[str, int] = defaultdict(int)
    doc_tokens: dict[str, list[str]] = {}
    for note in notes:
        note_toks = _tokenize(note.content + " " + note.title)
        doc_tokens[note.title] = note_toks
        for t in set(note_toks):
            df[t] += 1

    scores: dict[str, float] = {}
    for note in notes:
        toks = doc_tokens[note.title]
        if not toks:
            continue
        tf_idf = 0.0
        for token in tokens:
            tf = toks.count(token) / len(toks)
            idf = math.log((N + 1) / (df.get(token, 0) + 1)) + 1
            tf_idf += tf * idf
        scores[_slug(note.title)] = tf_idf

    return scores


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _extract_wikilinks(content: str) -> list[str]:
    """Return unique page names referenced as [[page name]] in content."""
    return list(dict.fromkeys(re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]", content)))


def _extract_sections(content: str) -> list[str]:
    """Return list of heading text found in markdown content."""
    return re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)


@dataclass
class _NoteResult:
    """Lightweight result object returned by search_notes()."""
    path: str
    title: str
    excerpt: str
    frontmatter: dict
    score: float
    backlinks: list[str]


@dataclass
class _FullNote:
    """Full note object returned by get_note()."""
    path: str
    title: str
    frontmatter: dict
    body: str
    sections: list[str]
    tags: list[str]
    outgoing_links: list[str]
    modified: float
