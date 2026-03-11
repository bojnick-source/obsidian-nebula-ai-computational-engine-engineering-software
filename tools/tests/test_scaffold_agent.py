"""Unit tests for tools/scaffold_agent.py.

Tests the generate_agent() function end-to-end by patching AGENTS_ROOT to a
tmp_path, so file content is checked after all post-processing (including the
8-space indentation fix that lives in generate_agent itself).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

# Allow importing from tools/ without installation
sys.path.insert(0, str(Path(__file__).parent.parent))
import scaffold_agent  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_SPECIALIST_SPEC = {
    "id": "test_materials_specialist",
    "role": "specialist",
    "domain": "Materials Science — Alloys, Composites, Failure",
    "domain_short": "Materials Science",
    "pair": "test_materials_antagonist",
    "status": "planned",
}

MINIMAL_ANTAGONIST_SPEC = {
    "id": "test_materials_antagonist",
    "role": "antagonist",
    "domain": "Materials Science Critique",
    "domain_short": "Materials Science",
    "pair": "test_materials_specialist",
    "status": "planned",
}


def _generate(spec: dict, tmp_path: Path) -> Path:
    """Call generate_agent() with AGENTS_ROOT patched to tmp_path."""
    original_agents_root = scaffold_agent.AGENTS_ROOT
    original_repo_root = scaffold_agent.REPO_ROOT
    try:
        scaffold_agent.AGENTS_ROOT = tmp_path
        scaffold_agent.REPO_ROOT = tmp_path.parent
        scaffold_agent.generate_agent(spec, overwrite=True)
    finally:
        scaffold_agent.AGENTS_ROOT = original_agents_root
        scaffold_agent.REPO_ROOT = original_repo_root
    return tmp_path


# ─────────────────────────────────────────────────────────────────────────────
# SKILL.md correctness (via generate_agent, includes post-processing)
# ─────────────────────────────────────────────────────────────────────────────


def test_specialist_skill_md_has_8_headings(tmp_path):
    """Generated specialist SKILL.md must have at least 8 ## headings."""
    _generate(MINIMAL_SPECIALIST_SPEC, tmp_path)
    skill_path = tmp_path / MINIMAL_SPECIALIST_SPEC["id"] / "SKILL.md"
    assert skill_path.exists(), "SKILL.md was not generated"
    lines = skill_path.read_text().splitlines()
    h2_count = sum(1 for ln in lines if ln.startswith("## "))
    assert h2_count >= 8, f"Only {h2_count} ## headings found (need ≥ 8)"


def test_specialist_skill_md_at_least_60_lines(tmp_path):
    """Generated specialist SKILL.md must have at least 60 lines."""
    _generate(MINIMAL_SPECIALIST_SPEC, tmp_path)
    skill_path = tmp_path / MINIMAL_SPECIALIST_SPEC["id"] / "SKILL.md"
    line_count = len(skill_path.read_text().splitlines())
    assert line_count >= 60, f"Only {line_count} lines (need ≥ 60)"


def test_specialist_skill_md_no_indentation_bug(tmp_path):
    """Generated SKILL.md must not have ## headings with 8-space prefix."""
    _generate(MINIMAL_SPECIALIST_SPEC, tmp_path)
    skill_path = tmp_path / MINIMAL_SPECIALIST_SPEC["id"] / "SKILL.md"
    bad_lines = [ln for ln in skill_path.read_text().splitlines() if ln.startswith("        ## ")]
    assert bad_lines == [], (
        f"SKILL.md has {len(bad_lines)} 8-space-indented heading(s): {bad_lines[:3]}"
    )


def test_antagonist_skill_md_has_8_headings(tmp_path):
    """Generated antagonist SKILL.md must have at least 8 ## headings."""
    _generate(MINIMAL_ANTAGONIST_SPEC, tmp_path)
    skill_path = tmp_path / MINIMAL_ANTAGONIST_SPEC["id"] / "SKILL.md"
    assert skill_path.exists(), "SKILL.md was not generated"
    lines = skill_path.read_text().splitlines()
    h2_count = sum(1 for ln in lines if ln.startswith("## "))
    assert h2_count >= 8, f"Only {h2_count} ## headings found (need ≥ 8)"


def test_antagonist_skill_md_at_least_60_lines(tmp_path):
    """Generated antagonist SKILL.md must have at least 60 lines."""
    _generate(MINIMAL_ANTAGONIST_SPEC, tmp_path)
    skill_path = tmp_path / MINIMAL_ANTAGONIST_SPEC["id"] / "SKILL.md"
    line_count = len(skill_path.read_text().splitlines())
    assert line_count >= 60, f"Only {line_count} lines (need ≥ 60)"


# ─────────────────────────────────────────────────────────────────────────────
# Agent card correctness
# ─────────────────────────────────────────────────────────────────────────────


def test_agent_card_list_items_are_indented(tmp_path):
    """Agent card YAML must have list items indented with at least 2 spaces."""
    _generate(MINIMAL_SPECIALIST_SPEC, tmp_path)
    card_path = tmp_path / "registry" / "agent_cards" / f"{MINIMAL_SPECIALIST_SPEC['id']}.yaml"
    assert card_path.exists(), "Agent card was not generated"
    for line in card_path.read_text().splitlines():
        stripped = line.lstrip()
        if stripped.startswith("- "):
            indent = len(line) - len(stripped)
            assert indent >= 2, (
                f"List item has {indent}-space indent (need ≥ 2): {repr(line)}"
            )


def test_agent_card_is_valid_yaml(tmp_path):
    """Agent card content must be parseable YAML with correct id field."""
    _generate(MINIMAL_SPECIALIST_SPEC, tmp_path)
    card_path = tmp_path / "registry" / "agent_cards" / f"{MINIMAL_SPECIALIST_SPEC['id']}.yaml"
    parsed = yaml.safe_load(card_path.read_text())
    assert isinstance(parsed, dict)
    assert parsed.get("id") == MINIMAL_SPECIALIST_SPEC["id"]


# ─────────────────────────────────────────────────────────────────────────────
# tool_prefs.yaml schema
# ─────────────────────────────────────────────────────────────────────────────


def test_learned_tool_prefs_has_required_schema_keys(tmp_path):
    """Generated tool_prefs.yaml must contain agent_id, level, and analysis keys."""
    _generate(MINIMAL_SPECIALIST_SPEC, tmp_path)
    prefs_path = tmp_path / MINIMAL_SPECIALIST_SPEC["id"] / "learned" / "tool_prefs.yaml"
    assert prefs_path.exists(), "tool_prefs.yaml was not generated"
    parsed = yaml.safe_load(prefs_path.read_text())
    assert isinstance(parsed, dict), "tool_prefs.yaml must be a YAML mapping"
    for key in ("agent_id", "level", "analysis"):
        assert key in parsed, f"tool_prefs.yaml missing '{key}' key"


def test_learned_tool_prefs_agent_id_matches(tmp_path):
    """tool_prefs.yaml agent_id must match the spec id."""
    _generate(MINIMAL_SPECIALIST_SPEC, tmp_path)
    prefs_path = tmp_path / MINIMAL_SPECIALIST_SPEC["id"] / "learned" / "tool_prefs.yaml"
    parsed = yaml.safe_load(prefs_path.read_text())
    assert parsed.get("agent_id") == MINIMAL_SPECIALIST_SPEC["id"]


# ─────────────────────────────────────────────────────────────────────────────
# Idempotency
# ─────────────────────────────────────────────────────────────────────────────


def test_skill_md_generation_is_idempotent(tmp_path):
    """Running generate_agent twice with overwrite=True must produce identical SKILL.md."""
    original_agents_root = scaffold_agent.AGENTS_ROOT
    original_repo_root = scaffold_agent.REPO_ROOT
    try:
        scaffold_agent.AGENTS_ROOT = tmp_path
        scaffold_agent.REPO_ROOT = tmp_path.parent
        scaffold_agent.generate_agent(MINIMAL_SPECIALIST_SPEC, overwrite=True)
        content1 = (tmp_path / MINIMAL_SPECIALIST_SPEC["id"] / "SKILL.md").read_text()
        scaffold_agent.generate_agent(MINIMAL_SPECIALIST_SPEC, overwrite=True)
        content2 = (tmp_path / MINIMAL_SPECIALIST_SPEC["id"] / "SKILL.md").read_text()
    finally:
        scaffold_agent.AGENTS_ROOT = original_agents_root
        scaffold_agent.REPO_ROOT = original_repo_root

    assert hashlib.md5(content1.encode()).hexdigest() == hashlib.md5(content2.encode()).hexdigest(), (
        "generate_agent() produced different SKILL.md on second run (not idempotent)"
    )
