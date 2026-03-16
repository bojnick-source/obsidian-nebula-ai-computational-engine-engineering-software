#!/usr/bin/env python3
"""
tools/check_stale_vault_index.py

Checks that forge-vault/indexes/stale-index.md exists and is up to date.

A note is considered STALE when its frontmatter `updated_at` is more than
STALE_DAYS days in the past (default: 90 days).

The stale index is UP TO DATE when every stale note is already listed in it.
A stale-index that lists fewer stale notes than the vault actually has is a CI
failure — it means the Librarian agent has not refreshed the index.

Exit 0 on clean. Exit 1 with details on any failure.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
VAULT = ROOT / "forge-vault"
STALE_INDEX = VAULT / "indexes" / "stale-index.md"
STALE_DAYS = 90

SKIP_DIRS = {".obsidian"}


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
        return yaml.safe_load(text[3:end].strip()) or {}
    except (ValueError, yaml.YAMLError):
        return {}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(str(value)[:19], fmt[:len(fmt)])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _collect_stale(cutoff: datetime) -> list[Path]:
    """Return vault notes whose updated_at is older than cutoff."""
    stale: list[Path] = []
    for md in sorted(VAULT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in md.parts):
            continue
        if md == STALE_INDEX:
            continue
        # Skip template-style and HOME notes
        if md.name in ("HOME.md",):
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)
        if not fm:
            continue  # no frontmatter — not an agent note
        dt = _parse_dt(str(fm.get("updated_at", "")))
        if dt and dt < cutoff:
            stale.append(md)
    return stale


def _indexed_paths(index_text: str) -> set[str]:
    """Extract note paths already listed in the stale index."""
    lines = index_text.splitlines()
    paths: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            # Expect lines like:  - [[engineering/materials/al7075.md]] or - path/to/note.md
            content = stripped[2:]
            content = content.strip("[]").split("|")[0].strip()
            if content:
                paths.add(content)
    return paths


def main() -> int:
    if not VAULT.exists():
        print(f"WARN: vault not found at {VAULT} — skipping stale check")
        return 0

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=STALE_DAYS)
    stale_notes = _collect_stale(cutoff)

    if not stale_notes:
        print(f"OK: no vault notes older than {STALE_DAYS} days")
        return 0

    # Stale index must exist once any stale notes are present
    if not STALE_INDEX.exists():
        print(f"FAIL: {len(stale_notes)} stale note(s) found but {STALE_INDEX.relative_to(ROOT)} does not exist")
        print("\nStale notes:")
        for p in stale_notes:
            print(f"  {p.relative_to(ROOT)}")
        return 1

    index_text = STALE_INDEX.read_text(encoding="utf-8")
    indexed = _indexed_paths(index_text)

    missing_from_index = [
        p for p in stale_notes
        if str(p.relative_to(VAULT)) not in indexed
        and p.name not in indexed
    ]

    if missing_from_index:
        print(
            f"FAIL: {len(missing_from_index)} stale note(s) not listed in "
            f"{STALE_INDEX.relative_to(ROOT)}:"
        )
        for p in missing_from_index:
            print(f"  {p.relative_to(ROOT)}")
        print("\nRun the Librarian agent to refresh the stale index.")
        return 1

    print(
        f"OK: {len(stale_notes)} stale note(s) — all recorded in stale-index.md"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
