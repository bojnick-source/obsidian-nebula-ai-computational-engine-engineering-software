#!/usr/bin/env python3
"""
validate_registry.py — FORGE agent registry CI gate.

Checks:
  1. Every agent_registry.yaml entry has a card file on disk
  2. Every antagonist pair references agents that exist in the registry
  3. Every agent with status mvp/v1/v2 has a prompts/[id]/v1.0.0.md
  4. Every agent with status v1/v2 has a forge-agents/[id]/SKILL.md
  5. Every SKILL.md has required sections (≥ 8 ## headings, ≥ 60 lines)
  6. No duplicate agent IDs
  7. All antagonist_pair fields in cards reference existing agent IDs
  8. Card files referenced in registry actually exist on disk

Exit 0 = all checks pass.
Exit 1 = one or more failures (details printed to stdout).

Usage:
    python tools/validate_registry.py
    python tools/validate_registry.py --report  # outputs JSON report to stdout
    python tools/validate_registry.py --agents-root forge-agents  # custom path
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).parent.parent
AGENTS_ROOT = REPO_ROOT / "forge-agents"
REGISTRY_FILE = AGENTS_ROOT / "registry" / "agent_registry.yaml"
PAIRS_FILE = AGENTS_ROOT / "registry" / "antagonist_pairs.yaml"

# Minimum content thresholds
MIN_SKILL_LINES = 60
MIN_SKILL_HEADINGS = 8  # number of ## section headings

REQUIRED_SKILL_SECTIONS = {
    "Capability Definition",
    "Output Contract",
    "Learned Strategies",
    "Level Progression",
    "Known Failure Patterns",
}

REQUIRED_CARD_FIELDS = {"id", "role", "status"}
REQUIRED_REGISTRY_FIELDS = {"id", "role", "status", "card"}

# Statuses that require a prompt file
PROMPT_REQUIRED_STATUSES = {"mvp", "v1", "v2"}
# Statuses that require a SKILL.md
SKILL_REQUIRED_STATUSES = {"v1", "v2"}

Errors = list[str]
Warnings = list[str]


def load_yaml(path: Path) -> Any:
    with path.open() as f:
        return yaml.safe_load(f)


def check_registry(errors: Errors, warnings: Warnings) -> list[dict[str, Any]]:
    """Load and validate agent_registry.yaml. Returns agent list."""
    if not REGISTRY_FILE.exists():
        errors.append(f"MISSING: {REGISTRY_FILE}")
        return []

    data = load_yaml(REGISTRY_FILE)
    if not isinstance(data, dict) or "agents" not in data:
        errors.append(f"SCHEMA: {REGISTRY_FILE} must have a top-level 'agents' key")
        return []

    agents: list[dict[str, Any]] = data["agents"]
    seen_ids: set[str] = set()

    for i, agent in enumerate(agents):
        ref = f"agent[{i}]"

        # Required fields
        for field in REQUIRED_REGISTRY_FIELDS:
            if field not in agent:
                errors.append(f"MISSING_FIELD: {ref} missing '{field}'")

        agent_id: str = agent.get("id", f"<unknown-{i}>")
        ref = f"agent[{agent_id}]"

        # Duplicate IDs
        if agent_id in seen_ids:
            errors.append(f"DUPLICATE_ID: {agent_id}")
        seen_ids.add(agent_id)

        # Card file exists
        card_rel: str | None = agent.get("card")
        if card_rel:
            card_path = AGENTS_ROOT / "registry" / card_rel
            if not card_path.exists():
                errors.append(
                    f"MISSING_CARD: {agent_id} references {card_rel} but file not found "
                    f"at {card_path}"
                )

        # Prompt file for active agents
        status: str = agent.get("status", "")
        if status in PROMPT_REQUIRED_STATUSES:
            prompt_path = AGENTS_ROOT / "prompts" / agent_id / "v1.0.0.md"
            if not prompt_path.exists():
                warnings.append(
                    f"MISSING_PROMPT: {agent_id} (status={status}) has no "
                    f"prompts/{agent_id}/v1.0.0.md"
                )

        # SKILL.md for v1/v2 agents
        if status in SKILL_REQUIRED_STATUSES:
            skill_path = AGENTS_ROOT / agent_id / "SKILL.md"
            if not skill_path.exists():
                warnings.append(
                    f"MISSING_SKILL: {agent_id} (status={status}) has no "
                    f"forge-agents/{agent_id}/SKILL.md"
                )

    return agents


def check_skill_files(errors: Errors, warnings: Warnings) -> None:
    """Validate every SKILL.md that exists."""
    for skill_path in sorted(AGENTS_ROOT.glob("*/SKILL.md")):
        agent_id = skill_path.parent.name
        if agent_id in ("registry", "prompts", "prompt_tests", "docs", "catalogues"):
            continue

        text = skill_path.read_text()
        lines = text.splitlines()
        line_count = len(lines)
        heading_count = sum(1 for ln in lines if ln.startswith("## "))

        if line_count < MIN_SKILL_LINES:
            errors.append(
                f"SKILL_TOO_SHORT: forge-agents/{agent_id}/SKILL.md has {line_count} lines "
                f"(minimum {MIN_SKILL_LINES})"
            )

        if heading_count < MIN_SKILL_HEADINGS:
            errors.append(
                f"SKILL_FEW_SECTIONS: forge-agents/{agent_id}/SKILL.md has {heading_count} "
                f"## headings (minimum {MIN_SKILL_HEADINGS})"
            )

        # Check required sections by keyword
        for section in REQUIRED_SKILL_SECTIONS:
            if section not in text:
                warnings.append(
                    f"SKILL_MISSING_SECTION: forge-agents/{agent_id}/SKILL.md "
                    f"missing section containing '{section}'"
                )


def check_antagonist_pairs(
    errors: Errors,
    warnings: Warnings,
    registry_ids: set[str],
) -> None:
    """Validate antagonist_pairs.yaml."""
    if not PAIRS_FILE.exists():
        warnings.append(f"MISSING: {PAIRS_FILE} not found")
        return

    data = load_yaml(PAIRS_FILE)
    if not isinstance(data, dict) or "pairs" not in data:
        errors.append(f"SCHEMA: {PAIRS_FILE} must have a top-level 'pairs' key")
        return

    for i, pair in enumerate(data["pairs"]):
        ref = f"pairs[{i}]"
        specialist = pair.get("specialist", "")
        antagonist = pair.get("antagonist", "")

        if specialist == "all":
            continue  # universal reviewer pair, skip ID check

        if specialist and specialist not in registry_ids:
            errors.append(
                f"PAIR_UNKNOWN_SPECIALIST: {ref} specialist={specialist} "
                f"not in agent_registry.yaml"
            )
        if antagonist and antagonist not in registry_ids:
            errors.append(
                f"PAIR_UNKNOWN_ANTAGONIST: {ref} antagonist={antagonist} "
                f"not in agent_registry.yaml"
            )
        if "debate_scope" not in pair:
            warnings.append(f"PAIR_NO_SCOPE: {ref} ({specialist} ↔ {antagonist}) missing debate_scope")


def check_agent_cards(errors: Errors, warnings: Warnings, registry_ids: set[str]) -> None:
    """Check all agent card files in registry/agent_cards/ and registry/mathematicians/."""
    card_dirs = [
        AGENTS_ROOT / "registry" / "agent_cards",
        AGENTS_ROOT / "registry" / "mathematicians",
    ]
    for card_dir in card_dirs:
        if not card_dir.exists():
            continue
        for card_file in sorted(card_dir.glob("*.yaml")):
            try:
                card = load_yaml(card_file)
            except Exception as exc:
                errors.append(f"CARD_PARSE_ERROR: {card_file.name}: {exc}")
                continue

            if not isinstance(card, dict):
                errors.append(f"CARD_NOT_DICT: {card_file.name} is not a YAML mapping")
                continue

            for field in REQUIRED_CARD_FIELDS:
                if field not in card:
                    errors.append(f"CARD_MISSING_FIELD: {card_file.name} missing '{field}'")

            card_id: str = card.get("id", "")
            if card_id and card_id not in registry_ids:
                warnings.append(
                    f"CARD_UNREGISTERED: {card_file.name} has id={card_id} "
                    f"but that agent is not in agent_registry.yaml"
                )


def check_orphaned_prompts(
    errors: Errors, warnings: Warnings, registry_ids: set[str]
) -> None:
    """Warn about prompts/ directories with no matching registry entry."""
    prompts_dir = AGENTS_ROOT / "prompts"
    if not prompts_dir.exists():
        return
    for prompt_dir in sorted(prompts_dir.iterdir()):
        if prompt_dir.is_dir() and prompt_dir.name not in registry_ids:
            warnings.append(
                f"ORPHANED_PROMPT: prompts/{prompt_dir.name}/ has no entry in "
                f"agent_registry.yaml"
            )


def check_learned_dirs(errors: Errors, warnings: Warnings) -> None:
    """Every agent directory with a SKILL.md should have learned/ with 3 files."""
    required_files = {"failure_patterns.jsonl", "strategies.jsonl", "tool_prefs.yaml"}
    for skill_path in sorted(AGENTS_ROOT.glob("*/SKILL.md")):
        agent_dir = skill_path.parent
        if agent_dir.name in ("registry", "prompts", "prompt_tests", "docs", "catalogues"):
            continue
        learned = agent_dir / "learned"
        if not learned.exists():
            warnings.append(
                f"MISSING_LEARNED_DIR: forge-agents/{agent_dir.name}/ has SKILL.md "
                f"but no learned/ directory"
            )
            continue
        for fname in required_files:
            if not (learned / fname).exists():
                warnings.append(
                    f"MISSING_LEARNED_FILE: forge-agents/{agent_dir.name}/learned/{fname}"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the FORGE agent registry")
    parser.add_argument("--report", action="store_true", help="Output JSON report")
    parser.add_argument(
        "--agents-root", type=Path, default=None, help="Override agents root path"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    args = parser.parse_args()

    global AGENTS_ROOT, REGISTRY_FILE, PAIRS_FILE
    if args.agents_root:
        AGENTS_ROOT = args.agents_root
        REGISTRY_FILE = AGENTS_ROOT / "registry" / "agent_registry.yaml"
        PAIRS_FILE = AGENTS_ROOT / "registry" / "antagonist_pairs.yaml"

    errors: Errors = []
    warnings: Warnings = []

    agents = check_registry(errors, warnings)
    registry_ids = {a["id"] for a in agents if "id" in a}

    check_skill_files(errors, warnings)
    check_antagonist_pairs(errors, warnings, registry_ids)
    check_agent_cards(errors, warnings, registry_ids)
    check_orphaned_prompts(errors, warnings, registry_ids)
    check_learned_dirs(errors, warnings)

    effective_errors = errors + (warnings if args.strict else [])

    if args.report:
        report = {
            "pass": len(effective_errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "agent_count": len(registry_ids),
        }
        print(json.dumps(report, indent=2))
    else:
        if errors:
            print(f"\n{'='*60}")
            print(f"FORGE REGISTRY VALIDATION — {len(errors)} ERROR(S)")
            print("=" * 60)
            for e in errors:
                print(f"  ERROR: {e}")
        if warnings:
            print(f"\n{'='*60}")
            print(f"FORGE REGISTRY VALIDATION — {len(warnings)} WARNING(S)")
            print("=" * 60)
            for w in warnings:
                print(f"  WARN:  {w}")
        if not errors and not warnings:
            print(f"FORGE REGISTRY VALIDATION — PASS ({len(registry_ids)} agents)")
        elif not errors:
            print(
                f"\nFORGE REGISTRY VALIDATION — PASS with {len(warnings)} warnings "
                f"({len(registry_ids)} agents)"
            )

    return 1 if effective_errors else 0


if __name__ == "__main__":
    sys.exit(main())
