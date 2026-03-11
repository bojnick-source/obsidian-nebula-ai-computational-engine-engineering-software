"""Unit tests for tools/validate_registry.py.

Uses tmp_path filesystem fixtures + subprocess to invoke the validator
against controlled registry structures. Tests the CI gate logic in isolation.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

VALIDATOR = Path(__file__).parent.parent / "validate_registry.py"


def _run(agents_root: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(VALIDATOR), "--agents-root", str(agents_root)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data))


def _minimal_registry(agents_root: Path, agents: list[dict]) -> None:
    """Write a minimal valid registry YAML."""
    registry_path = agents_root / "registry" / "agent_registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(yaml.dump({"schema_version": "v2", "agents": agents}))


def _minimal_card(agents_root: Path, card_rel: str, agent_id: str) -> None:
    """Write a minimal valid agent card."""
    card_path = agents_root / "registry" / card_rel
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(yaml.dump({"id": agent_id, "role": "specialist", "status": "planned"}))


def _minimal_skill_md(agents_root: Path, agent_id: str, lines: int = 65, headings: int = 9) -> None:
    """Write a SKILL.md with specified line count and ## heading count."""
    skill_path = agents_root / agent_id / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)

    # Build content: headings + padding lines
    content_lines = []
    # Add required section keywords
    for section in [
        "## Capability Definition",
        "## Output Contract",
        "## Learned Strategies",
        "## Level Progression",
        "## Known Failure Patterns",
    ]:
        content_lines.append(section)
        content_lines.append("placeholder content line")

    # Add extra headings to hit the required count
    extra_headings = headings - 5
    for i in range(max(0, extra_headings)):
        content_lines.append(f"## Extra Section {i + 1}")
        content_lines.append("placeholder")

    # Pad to reach required line count
    while len(content_lines) < lines:
        content_lines.append("padding line")

    skill_path.write_text("\n".join(content_lines))


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_valid_registry_passes(tmp_path):
    """A well-formed minimal registry with card files should exit 0."""
    agent_id = "test_specialist"
    card_rel = "agent_cards/test_specialist.yaml"
    _minimal_registry(tmp_path, [{"id": agent_id, "role": "specialist", "status": "planned", "card": card_rel}])
    _minimal_card(tmp_path, card_rel, agent_id)

    result = _run(tmp_path)
    assert result.returncode == 0, f"Expected pass but got errors:\n{result.stdout}\n{result.stderr}"


def test_missing_card_fails(tmp_path):
    """Registry entry pointing to a non-existent card file should exit 1."""
    _minimal_registry(tmp_path, [{
        "id": "ghost_specialist",
        "role": "specialist",
        "status": "planned",
        "card": "agent_cards/ghost_specialist.yaml",  # file not created
    }])

    result = _run(tmp_path)
    assert result.returncode == 1, "Expected failure for missing card"
    assert "MISSING_CARD" in result.stdout


def test_duplicate_agent_id_fails(tmp_path):
    """Two agents with the same ID should exit 1."""
    card_rel = "agent_cards/dup_agent.yaml"
    _minimal_registry(tmp_path, [
        {"id": "dup_agent", "role": "specialist", "status": "planned", "card": card_rel},
        {"id": "dup_agent", "role": "antagonist", "status": "planned", "card": card_rel},
    ])
    _minimal_card(tmp_path, card_rel, "dup_agent")

    result = _run(tmp_path)
    assert result.returncode == 1, "Expected failure for duplicate IDs"
    assert "DUPLICATE_ID" in result.stdout


def test_skill_md_too_short_fails(tmp_path):
    """A SKILL.md with fewer than 60 lines should exit 1."""
    agent_id = "short_skill_agent"
    card_rel = f"agent_cards/{agent_id}.yaml"
    _minimal_registry(tmp_path, [{"id": agent_id, "role": "specialist", "status": "v1", "card": card_rel}])
    _minimal_card(tmp_path, card_rel, agent_id)
    _minimal_skill_md(tmp_path, agent_id, lines=30, headings=9)

    result = _run(tmp_path)
    assert result.returncode == 1, "Expected failure for SKILL.md too short"
    assert "SKILL_TOO_SHORT" in result.stdout


def test_skill_md_missing_headings_fails(tmp_path):
    """A SKILL.md with fewer than 8 ## headings should exit 1."""
    agent_id = "few_headings_agent"
    card_rel = f"agent_cards/{agent_id}.yaml"
    _minimal_registry(tmp_path, [{"id": agent_id, "role": "specialist", "status": "v1", "card": card_rel}])
    _minimal_card(tmp_path, card_rel, agent_id)
    _minimal_skill_md(tmp_path, agent_id, lines=70, headings=4)

    result = _run(tmp_path)
    assert result.returncode == 1, "Expected failure for too few ## headings"
    assert "SKILL_FEW_SECTIONS" in result.stdout


def test_antagonist_pair_unknown_agent_fails(tmp_path):
    """A pair referencing an agent not in the registry should exit 1."""
    agent_id = "known_specialist"
    card_rel = f"agent_cards/{agent_id}.yaml"
    _minimal_registry(tmp_path, [{"id": agent_id, "role": "specialist", "status": "planned", "card": card_rel}])
    _minimal_card(tmp_path, card_rel, agent_id)

    # Write pairs file referencing an unknown antagonist
    pairs_path = tmp_path / "registry" / "antagonist_pairs.yaml"
    pairs_path.write_text(yaml.dump({
        "pairs": [{
            "specialist": agent_id,
            "antagonist": "nonexistent_antagonist",
            "debate_scope": ["test"],
        }]
    }))

    result = _run(tmp_path)
    assert result.returncode == 1, "Expected failure for unknown pair member"
    assert "PAIR_UNKNOWN" in result.stdout


def test_214_agents_pass():
    """Smoke test: the real repo registry validates with exit 0."""
    repo_root = Path(__file__).parent.parent.parent
    agents_root = repo_root / "forge-agents"
    if not agents_root.exists():
        pytest.skip("forge-agents/ not found relative to tools/tests/")

    result = _run(agents_root)
    assert result.returncode == 0, (
        f"Registry validation failed on real repo:\n{result.stdout}\n{result.stderr}"
    )


def test_report_flag_outputs_json(tmp_path):
    """--report flag should produce valid JSON output."""
    import json

    agent_id = "json_test_agent"
    card_rel = f"agent_cards/{agent_id}.yaml"
    _minimal_registry(tmp_path, [{"id": agent_id, "role": "specialist", "status": "planned", "card": card_rel}])
    _minimal_card(tmp_path, card_rel, agent_id)

    result = _run(tmp_path, ["--report"])
    assert result.returncode == 0

    report = json.loads(result.stdout)
    assert "pass" in report
    assert "errors" in report
    assert "warnings" in report
    assert "agent_count" in report
    assert report["pass"] is True
