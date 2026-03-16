#!/usr/bin/env python3
"""
tools/validate_vault_frontmatter.py

Validates the YAML frontmatter of every *.md file under forge-vault/
against forge-memory/schemas/vault_frontmatter.schema.yaml.

Rules checked
-------------
1. File has a valid frontmatter block (--- … ---)
2. Required fields are all present (id, type, domain, created_at, updated_at,
   trace_id, agent_id, agent_version, confidence, pathway_strength)
3. `type` is one of the allowed enum values
4. `domain` is one of the allowed enum values
5. `confidence` and `pathway_strength` are floats in [0.0, 1.0]

Files in .obsidian/ and .gitkeep-only dirs are skipped.
HOME.md is skipped (vault index note, not an agent-written note).

Exit 0 on clean. Exit 1 and print violations on any failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
VAULT = ROOT / "forge-vault"
SCHEMA_PATH = ROOT / "forge-memory" / "schemas" / "vault_frontmatter.schema.yaml"

SKIP_PATHS = {
    VAULT / "HOME.md",
}

REQUIRED_FIELDS = [
    "id", "type", "domain", "created_at", "updated_at",
    "trace_id", "agent_id", "agent_version", "confidence", "pathway_strength",
]

TYPE_ENUM = {
    "finding", "derivation", "decision", "gap",
    "synthesis", "agent-thinking", "ilc-link",
}

DOMAIN_ENUM = {
    "mechanical_engineering", "materials", "electrical_engineering",
    "plasma", "magnetics", "controls", "thermal_fluids", "acoustics",
    "safety_se", "biomedical", "mathematics", "cross_domain",
}


def _parse_frontmatter(text: str) -> dict | None:
    """Return parsed frontmatter dict, or None if not present."""
    if not text.startswith("---"):
        return None
    try:
        end = text.index("---", 3)
    except ValueError:
        return None
    fm_text = text[3:end].strip()
    try:
        return yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return None


def _validate_note(path: Path) -> list[str] | None:
    """Return list of violations (empty = OK), or None if note has no frontmatter (skip)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(text)

    violations: list[str] = []

    if fm is None:
        # No frontmatter — structural/meta note (README, indexes, HOME).  Skip.
        return None

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in fm:
            violations.append(f"missing required field: {field!r}")

    # type enum
    if "type" in fm and fm["type"] not in TYPE_ENUM:
        violations.append(f"invalid type: {fm['type']!r} not in {sorted(TYPE_ENUM)}")

    # domain enum
    if "domain" in fm and fm["domain"] not in DOMAIN_ENUM:
        violations.append(f"invalid domain: {fm['domain']!r} not in {sorted(DOMAIN_ENUM)}")

    # confidence range
    if "confidence" in fm:
        try:
            c = float(fm["confidence"])
            if not (0.0 <= c <= 1.0):
                violations.append(f"confidence={c} out of [0.0, 1.0]")
        except (TypeError, ValueError):
            violations.append(f"confidence must be a float, got {fm['confidence']!r}")

    # pathway_strength range
    if "pathway_strength" in fm:
        try:
            ps = float(fm["pathway_strength"])
            if not (0.0 <= ps <= 1.0):
                violations.append(f"pathway_strength={ps} out of [0.0, 1.0]")
        except (TypeError, ValueError):
            violations.append(
                f"pathway_strength must be a float, got {fm['pathway_strength']!r}"
            )

    return violations


def main() -> int:
    if not VAULT.exists():
        print(f"WARN: vault directory not found at {VAULT} — nothing to validate")
        return 0

    all_violations: list[tuple[Path, list[str]]] = []
    checked = 0

    for md in sorted(VAULT.rglob("*.md")):
        # Skip Obsidian config notes, HOME.md
        if ".obsidian" in md.parts:
            continue
        if md in SKIP_PATHS:
            continue
        # Skip template-style notes (contain {{}} placeholders)
        text = md.read_text(encoding="utf-8", errors="replace")
        if re.search(r"\{\{[^}]+\}\}", text):
            continue

        violations = _validate_note(md)
        if violations is None:
            continue  # structural note, no frontmatter — not counted
        checked += 1
        if violations:
            all_violations.append((md, violations))

    if checked == 0:
        print("OK: no agent-written notes found in forge-vault/ — nothing to validate")
        return 0

    if not all_violations:
        print(f"OK: {checked} vault note(s) passed frontmatter validation")
        return 0

    print(f"FAIL: {len(all_violations)} of {checked} note(s) have frontmatter violations:\n")
    for path, viols in all_violations:
        rel = path.relative_to(ROOT)
        for v in viols:
            print(f"  {rel}: {v}")

    print(f"\n{len(all_violations)} file(s) failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
