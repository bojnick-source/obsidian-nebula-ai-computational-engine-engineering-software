"""Regression tests for known CI bugs that were fixed.

Each test documents a real bug that was caught and fixed. If these tests fail
it means a regression has been introduced. Do not delete them without a clear
reason — they are historical guards.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# Bug: yamllint ran without config, flagging intentional alignment as errors
# Fix: .yamllint.yml added at repo root with colons: max-spaces-after: -1
# ─────────────────────────────────────────────────────────────────────────────


def test_yamllint_config_exists():
    """.yamllint.yml must exist at repo root."""
    assert (REPO_ROOT / ".yamllint.yml").exists(), ".yamllint.yml missing from repo root"


def test_yamllint_colons_rule_allows_alignment():
    """.yamllint.yml must configure colons to allow alignment spacing."""
    config_path = REPO_ROOT / ".yamllint.yml"
    if not config_path.exists():
        pytest.skip(".yamllint.yml not found")
    content = config_path.read_text()
    assert "max-spaces-after" in content, (
        ".yamllint.yml missing colons max-spaces-after rule (needed for aligned config files)"
    )
    # The value -1 disables the check (unlimited spaces allowed)
    assert "-1" in content, (
        ".yamllint.yml colons rule must use -1 to allow alignment spacing"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Bug: `|| true` in ci.yml swallowed yamllint and ruff failures silently
# Fix: removed || true from both lint steps
# ─────────────────────────────────────────────────────────────────────────────


def test_ci_no_or_true_masking_lint():
    """ci.yml must not mask lint failures with `|| true`."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci_path.exists():
        pytest.skip("ci.yml not found")
    content = ci_path.read_text()
    lines = content.splitlines()

    for line in lines:
        stripped = line.strip()
        if ("yamllint" in stripped or "ruff check" in stripped) and "|| true" in stripped:
            pytest.fail(
                f"CI step masks failure with '|| true': {repr(stripped)}"
            )


def test_ci_has_pytest_job():
    """ci.yml must include a run-tests job that executes pytest."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci_path.exists():
        pytest.skip("ci.yml not found")
    content = ci_path.read_text()
    assert "pytest" in content, "ci.yml does not contain a pytest step"
    assert "run-tests" in content, "ci.yml does not contain run-tests job"


# ─────────────────────────────────────────────────────────────────────────────
# Bug: SKILL.md headings had 8-space indentation due to textwrap.dedent failure
# Fix: scaffold_agent.py post-processes output to strip the 8-space prefix
# ─────────────────────────────────────────────────────────────────────────────


def test_skill_md_no_indentation_bug():
    """No SKILL.md in the repo should have ## headings with 8-space prefix."""
    bad_files = []
    for skill_path in sorted((REPO_ROOT / "forge-agents").glob("*/SKILL.md")):
        for line in skill_path.read_text().splitlines():
            if line.startswith("        ## "):  # 8 spaces
                bad_files.append(skill_path.name)
                break

    assert bad_files == [], (
        f"SKILL.md files with 8-space indentation bug: {bad_files[:5]}"
    )


def test_skill_md_heading_count():
    """Every SKILL.md in the repo must have at least 8 ## headings."""
    failing = []
    for skill_path in sorted((REPO_ROOT / "forge-agents").glob("*/SKILL.md")):
        lines = skill_path.read_text().splitlines()
        h2_count = sum(1 for ln in lines if ln.startswith("## "))
        if h2_count < 8:
            failing.append(f"{skill_path.parent.name}: {h2_count} headings")

    assert failing == [], (
        "SKILL.md files with fewer than 8 ## headings:\n" + "\n".join(failing[:10])
    )


# ─────────────────────────────────────────────────────────────────────────────
# Bug: Agent card YAML list items lacked indentation (PyYAML dump default)
# Fix: batch-fixed all 9 affected cards; scaffold_agent.py now generates correctly
# ─────────────────────────────────────────────────────────────────────────────


def test_agent_cards_list_items_indented():
    """Agent card YAML files must not have list items at column 0 under a mapping key."""
    card_dir = REPO_ROOT / "forge-agents" / "registry" / "agent_cards"
    if not card_dir.exists():
        pytest.skip("agent_cards/ directory not found")

    bad_files = []
    for card_path in sorted(card_dir.glob("*.yaml")):
        lines = card_path.read_text().splitlines()
        for i, line in enumerate(lines):
            # A list item at column 0 that follows a non-list line is the bug pattern
            if line.startswith("- ") and i > 0 and not lines[i - 1].startswith("- "):
                # Check that the previous non-empty line is a mapping key
                prev = lines[i - 1].strip()
                if prev.endswith(":") or prev == "":
                    bad_files.append(card_path.name)
                    break

    assert bad_files == [], (
        f"Agent cards with unindented list items: {bad_files[:5]}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Bug: Error code ERR_HIDDEN_ASSUMPTION was renamed to ERR_VERIFY_HIDDEN_ASSUMPTION
# Fix: updated verifier-architecture.md with canonical code
# ─────────────────────────────────────────────────────────────────────────────


def test_error_code_naming_verifier_architecture():
    """verifier-architecture.md must use canonical ERR_VERIFY_HIDDEN_ASSUMPTION."""
    doc_path = REPO_ROOT / "docs" / "architecture" / "verifier-architecture.md"
    if not doc_path.exists():
        pytest.skip("verifier-architecture.md not found")
    content = doc_path.read_text()
    assert "ERR_VERIFY_HIDDEN_ASSUMPTION" in content, (
        "verifier-architecture.md missing canonical error code ERR_VERIFY_HIDDEN_ASSUMPTION"
    )
    assert "ERR_HIDDEN_ASSUMPTION" not in content.replace("ERR_VERIFY_HIDDEN_ASSUMPTION", ""), (
        "verifier-architecture.md still uses old error code ERR_HIDDEN_ASSUMPTION"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Bug: mcp-wrapper-envelope.md had ambiguous retry count language
# Fix: clarified as "4 total attempts (1 initial + up to 3 retries)"
# ─────────────────────────────────────────────────────────────────────────────


def test_mcp_wrapper_retry_count():
    """mcp-wrapper-envelope.md must document 4 total attempts."""
    doc_path = REPO_ROOT / "docs" / "contracts" / "mcp-wrapper-envelope.md"
    if not doc_path.exists():
        pytest.skip("mcp-wrapper-envelope.md not found")
    content = doc_path.read_text()
    assert "4 total attempts" in content, (
        "mcp-wrapper-envelope.md must state '4 total attempts' in retry policy"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Bug: .secrets.baseline check in security.yml silently created missing baseline
# Fix: explicit check — fail if baseline does not exist
# ─────────────────────────────────────────────────────────────────────────────


def test_secrets_baseline_exists():
    """.secrets.baseline must exist so security CI can run."""
    baseline = REPO_ROOT / ".secrets.baseline"
    assert baseline.exists(), (
        ".secrets.baseline missing — security CI will fail. "
        "Run: detect-secrets scan --baseline .secrets.baseline"
    )
