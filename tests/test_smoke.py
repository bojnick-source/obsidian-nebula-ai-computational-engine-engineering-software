"""Smoke tests for the FORGE registry + scaffold pipeline.

These tests verify that core data files are parseable and self-consistent
without running any agent logic. Fast to run, high-value early failure signal.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
AGENTS_ROOT = REPO_ROOT / "forge-agents"
REGISTRY_FILE = AGENTS_ROOT / "registry" / "agent_registry.yaml"
PAIRS_FILE = AGENTS_ROOT / "registry" / "antagonist_pairs.yaml"


# ─────────────────────────────────────────────────────────────────────────────
# Core YAML parse smoke tests
# ─────────────────────────────────────────────────────────────────────────────


def test_agent_registry_yaml_parseable():
    """agent_registry.yaml must load without YAML parse error."""
    if not REGISTRY_FILE.exists():
        pytest.skip(f"Registry file not found: {REGISTRY_FILE}")
    data = yaml.safe_load(REGISTRY_FILE.read_text())
    assert isinstance(data, dict), "agent_registry.yaml must be a YAML mapping"
    assert "agents" in data, "agent_registry.yaml must have 'agents' key"
    assert len(data["agents"]) > 0, "agent_registry.yaml must have at least one agent"


def test_antagonist_pairs_yaml_parseable():
    """antagonist_pairs.yaml must load without YAML parse error."""
    if not PAIRS_FILE.exists():
        pytest.skip(f"Pairs file not found: {PAIRS_FILE}")
    data = yaml.safe_load(PAIRS_FILE.read_text())
    assert isinstance(data, dict), "antagonist_pairs.yaml must be a YAML mapping"
    assert "pairs" in data, "antagonist_pairs.yaml must have 'pairs' key"
    assert len(data["pairs"]) > 0, "antagonist_pairs.yaml must have at least one pair"


def test_all_agent_cards_parseable():
    """Every .yaml file in registry/agent_cards/ must be valid YAML."""
    card_dir = AGENTS_ROOT / "registry" / "agent_cards"
    if not card_dir.exists():
        pytest.skip(f"agent_cards/ directory not found: {card_dir}")

    parse_errors = []
    cards = list(card_dir.glob("*.yaml"))
    assert len(cards) > 0, "No agent card files found — something is wrong"

    for card_path in sorted(cards):
        try:
            data = yaml.safe_load(card_path.read_text())
            if not isinstance(data, dict):
                parse_errors.append(f"{card_path.name}: not a YAML mapping")
        except yaml.YAMLError as exc:
            parse_errors.append(f"{card_path.name}: {exc}")

    assert parse_errors == [], (
        "Agent cards with YAML parse errors:\n" + "\n".join(parse_errors[:10])
    )


def test_all_skill_md_files_readable():
    """Every SKILL.md in forge-agents/ must be non-empty and readable."""
    skill_files = list(AGENTS_ROOT.glob("*/SKILL.md"))
    if not skill_files:
        pytest.skip("No SKILL.md files found — possibly empty repo")

    empty_files = []
    for skill_path in sorted(skill_files):
        content = skill_path.read_text()
        if not content.strip():
            empty_files.append(skill_path.parent.name)

    assert empty_files == [], f"Empty SKILL.md files: {empty_files[:5]}"


def test_registry_agent_count():
    """Registry should have a substantial number of agents (not accidentally truncated)."""
    if not REGISTRY_FILE.exists():
        pytest.skip("Registry file not found")
    data = yaml.safe_load(REGISTRY_FILE.read_text())
    agent_count = len(data.get("agents", []))
    assert agent_count >= 50, (
        f"Registry has only {agent_count} agents — expected ≥ 50 (registry may be corrupted)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end: validate_registry.py
# ─────────────────────────────────────────────────────────────────────────────


def test_registry_validates_with_zero_errors():
    """python tools/validate_registry.py must exit 0 on the real repo."""
    validator = REPO_ROOT / "tools" / "validate_registry.py"
    if not validator.exists():
        pytest.skip("validate_registry.py not found")

    result = subprocess.run(
        [sys.executable, str(validator), "--agents-root", str(AGENTS_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Registry validation produced errors:\n{result.stdout}\n{result.stderr}"
    )
