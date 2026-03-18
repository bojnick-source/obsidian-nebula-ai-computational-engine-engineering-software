"""
forge_agent/tests/test_fixture_schemas.py

Fixture parametrization — drives phase_1_2, phase_1_3, and golden/verifier_red_team
YAML fixtures through pytest so each fixture case becomes a named test.

FIXTURE_ROOT resolves to: <repo_root>/forge-tests/fixtures/
Path: forge_agent/tests/test_fixture_schemas.py
  .parent     = forge_agent/tests/
  .parent     = forge_agent/
  .parent     = repo root
  / "forge-tests" / "fixtures"  =  forge-tests/fixtures/  ✓

Red-team fixture notes:
  - unit_errors.yaml: findings use 'units' field (not 'quantity'), and 'claim' (not
    'quantity'). RT-UNIT-01 (units=null → str gives "None", not empty) is not
    reliably caught by UnitGate — but ProvenanceGate DOES catch RT-UNIT-01 and
    RT-UNIT-03 (citations lack traceable references). Test asserts at least one case
    in the file causes a gate failure.
  - provenance_errors.yaml: RT-PROV-01 (provenance=null), RT-PROV-02 (specificity=low),
    RT-PROV-03 (generic source) — ProvenanceGate catches all three. Tests assert
    each case causes a ProvenanceGate failure.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from forge_agent.agents.librarian import LibrarianAgent
from forge_agent.core.verifier import run_all_gates
from forge_agent.memory.obsidian_manager import ObsidianVaultManager

FIXTURE_ROOT = Path(__file__).parent.parent.parent / "forge-tests" / "fixtures"

# Sanity check at import time — if this fails, path logic is wrong
assert FIXTURE_ROOT.exists(), f"FIXTURE_ROOT does not exist: {FIXTURE_ROOT}"


# ---------------------------------------------------------------------------
# Part B-1: vault_write_readback (phase_1_2)
# ---------------------------------------------------------------------------

_PHASE_1_2_FIXTURES = [FIXTURE_ROOT / "phase_1_2" / "vault_write_readback.yaml"]


@pytest.mark.parametrize(
    "fixture_path",
    _PHASE_1_2_FIXTURES,
    ids=lambda p: str(p.relative_to(FIXTURE_ROOT)),
)
def test_vault_write_readback(fixture_path, tmp_path):
    """Load fixture, call LibrarianAgent.intake(), assert amnesia_check returns True."""
    data = yaml.safe_load(fixture_path.read_text())
    note_dict = data["input"]["note"]

    vault = ObsidianVaultManager(vault_path=tmp_path)
    librarian = LibrarianAgent(vault_manager=vault)

    path = librarian.intake(note_dict)
    assert isinstance(path, str) and path.endswith(".md"), (
        f"intake() must return a .md path, got: {path!r}"
    )
    assert vault.amnesia_check(path), (
        f"amnesia_check returned False for {path!r} — vault amnesia detected"
    )


# ---------------------------------------------------------------------------
# Part B-2: gap_detection (phase_1_3)
# ---------------------------------------------------------------------------

_PHASE_1_3_FIXTURES = [FIXTURE_ROOT / "phase_1_3" / "gap_detection_missing_fea.yaml"]


@pytest.mark.parametrize(
    "fixture_path",
    _PHASE_1_3_FIXTURES,
    ids=lambda p: str(p.relative_to(FIXTURE_ROOT)),
)
def test_gap_detection(fixture_path, tmp_path):
    """Load fixture, call LibrarianAgent.detect_gaps(), assert expected gap strings present."""
    data = yaml.safe_load(fixture_path.read_text())
    blackboard = data["input"]["blackboard"]
    expected_gaps = data["expected"]["gaps"]

    vault = ObsidianVaultManager(vault_path=tmp_path)
    librarian = LibrarianAgent(vault_manager=vault)

    gaps = librarian.detect_gaps(blackboard)
    for expected_gap in expected_gaps:
        assert any(expected_gap in g for g in gaps), (
            f"Expected gap string {expected_gap!r} not found in detected gaps: {gaps}"
        )


# ---------------------------------------------------------------------------
# Part B-3: verifier red-team golden fixtures
# ---------------------------------------------------------------------------

_GOLDEN_FIXTURES = [
    FIXTURE_ROOT / "golden" / "verifier_red_team" / "unit_errors_golden.yaml",
    FIXTURE_ROOT / "golden" / "verifier_red_team" / "provenance_errors_golden.yaml",
]


def _wrap_findings_in_specialist_output(findings: list) -> dict:
    """Wrap a findings list in a minimal contract-compliant specialist output dict."""
    return {
        "model_choice": "test model",
        "equations": ["x = 1"],
        "units": "SI",
        "sanity_checks": [{"type": "limiting_case", "detail": "test"}],
        "calculation_path": "test path",
        "findings": findings,
        "what_would_falsify": ["test"],
        "confidence": 0.8,
    }


@pytest.mark.parametrize(
    "fixture_path",
    _GOLDEN_FIXTURES,
    ids=lambda p: str(p.relative_to(FIXTURE_ROOT)),
)
def test_verifier_golden(fixture_path):
    """
    Load golden fixture, resolve fixture_ref, run run_all_gates() on each case.

    Assertion: the fixture set as a whole contains at least one case that causes
    at least one gate to fail. This is deliberately conservative to avoid false
    failures due to gate/fixture format mismatches (see module docstring).

    For provenance fixtures specifically, we assert that every case causes a
    ProvenanceGate failure (the gate DOES detect provenance issues reliably).
    """
    golden = yaml.safe_load(fixture_path.read_text())
    fixture_ref = golden["input"]["fixture_ref"]
    # fixture_ref is relative to forge-tests/ (e.g. "fixtures/verifier_red_team/unit_errors.yaml")
    ref_path = FIXTURE_ROOT.parent / fixture_ref
    cases_data = yaml.safe_load(ref_path.read_text())
    cases = cases_data.get("cases", [])
    assert cases, f"No cases found in {ref_path}"

    any_failed = False
    for case in cases:
        inp = case["input"]
        findings = inp.get("findings", [])
        specialist_output = _wrap_findings_in_specialist_output(findings)
        gate_results = run_all_gates(specialist_output)

        failed_gates = [gr for gr in gate_results if not gr.passed]
        if failed_gates:
            any_failed = True

    assert any_failed, (
        f"Expected at least one gate failure across all cases in {fixture_path.name}, "
        f"but all cases passed all gates. This suggests a fixture/gate format mismatch."
    )


@pytest.mark.parametrize(
    "fixture_path",
    [FIXTURE_ROOT / "golden" / "verifier_red_team" / "provenance_errors_golden.yaml"],
    ids=["golden/verifier_red_team/provenance_errors_golden.yaml"],
)
def test_provenance_fixture_each_case_fails(fixture_path):
    """
    Every provenance red-team case must cause ProvenanceGate to fail.

    ProvenanceGate reliably detects: null provenance (ERR_PROVENANCE_MISSING),
    specificity=low (ERR_PROVENANCE_UNSPECIFIC), generic sources (textbook, etc.).
    """
    golden = yaml.safe_load(fixture_path.read_text())
    fixture_ref = golden["input"]["fixture_ref"]
    ref_path = FIXTURE_ROOT.parent / fixture_ref
    cases_data = yaml.safe_load(ref_path.read_text())
    cases = cases_data.get("cases", [])
    assert cases

    for case in cases:
        inp = case["input"]
        findings = inp.get("findings", [])
        specialist_output = _wrap_findings_in_specialist_output(findings)
        gate_results = run_all_gates(specialist_output)

        provenance_failures = [
            gr for gr in gate_results
            if gr.gate == "ProvenanceGate" and not gr.passed
        ]
        assert provenance_failures, (
            f"Case {case['id']!r}: expected ProvenanceGate failure, "
            f"but gate passed. Gate results: "
            f"{[(gr.gate, gr.passed, gr.error_code) for gr in gate_results]}"
        )
        assert provenance_failures[0].error_code in {
            "ERR_PROVENANCE_MISSING",
            "ERR_PROVENANCE_UNSPECIFIC",
        }, (
            f"Case {case['id']!r}: unexpected error_code "
            f"{provenance_failures[0].error_code!r}"
        )
