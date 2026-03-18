"""Tests for ILCDetector — 8 acceptance criteria from plan 4-005."""

from __future__ import annotations

from unittest.mock import MagicMock

from forge_agent.core.ilc_detector import ILCCandidate, ILCDetector


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_detector() -> tuple[ILCDetector, MagicMock]:
    """Return an ILCDetector wired to a MagicMock vault_manager."""
    mock_vault = MagicMock()
    mock_vault.upsert_note.return_value = "ilc/links/test.md"
    detector = ILCDetector(mock_vault)
    return detector, mock_vault


# Sample notes with two shared terms: "von Mises stress" and "200 MPa"
NOTE_STRESS_A = {
    "path": "engineering/stress-analysis.md",
    "content": (
        "The component experiences von Mises stress of 200 MPa under load. "
        "FEA confirms yield strength is not exceeded."
    ),
    "frontmatter": {"domain": "structural"},
}

NOTE_STRESS_B = {
    "path": "engineering/thermal-fatigue.md",
    "content": (
        "Cyclic thermal loading induces von Mises stress peaks at 200 MPa. "
        "Fatigue limit must be verified via FEA."
    ),
    "frontmatter": {"domain": "thermal"},
}

NOTE_UNRELATED = {
    "path": "engineering/aerodynamics.md",
    "content": "The drag coefficient is measured at Mach number 0.8 in the wind tunnel.",
    "frontmatter": {"domain": "aerodynamics"},
}


# ---------------------------------------------------------------------------
# AC 1: Two notes sharing "von Mises stress" and "MPa" produce a candidate
#        with those terms in shared_terms.
# ---------------------------------------------------------------------------


def test_shared_terms_von_mises_and_mpa() -> None:
    detector, _ = make_detector()
    candidates = detector.detect_candidates([NOTE_STRESS_A, NOTE_STRESS_B])
    assert len(candidates) >= 1
    c = candidates[0]
    shared_lower = [t.lower() for t in c.shared_terms]
    # Both "von mises stress" and a term containing "mpa" must be present
    assert any("von mises stress" in t for t in shared_lower), (
        f"Expected 'von Mises stress' in shared_terms, got: {c.shared_terms}"
    )
    mpa_found = any("mpa" in t for t in shared_lower)
    assert mpa_found, f"Expected an MPa term in shared_terms, got: {c.shared_terms}"


# ---------------------------------------------------------------------------
# AC 2: A single note (no pair) produces no candidates.
# ---------------------------------------------------------------------------


def test_single_note_no_candidates() -> None:
    detector, _ = make_detector()
    candidates = detector.detect_candidates([NOTE_STRESS_A])
    assert candidates == []


# ---------------------------------------------------------------------------
# AC 3: Empty notes list produces no candidates.
# ---------------------------------------------------------------------------


def test_empty_notes_no_candidates() -> None:
    detector, _ = make_detector()
    candidates = detector.detect_candidates([])
    assert candidates == []


# ---------------------------------------------------------------------------
# AC 4: ILCCandidate.confidence is always a float in [0.0, 1.0].
# ---------------------------------------------------------------------------


def test_confidence_in_range() -> None:
    detector, _ = make_detector()
    candidates = detector.detect_candidates([NOTE_STRESS_A, NOTE_STRESS_B])
    assert len(candidates) >= 1
    for c in candidates:
        assert isinstance(c.confidence, float), f"confidence is not float: {type(c.confidence)}"
        assert 0.0 <= c.confidence <= 1.0, f"confidence out of range: {c.confidence}"


# ---------------------------------------------------------------------------
# AC 5: ILCCandidate.link_type is always one of the allowed values.
# ---------------------------------------------------------------------------

VALID_LINK_TYPES = {"cross-domain", "reinforcing", "contradicting"}


def test_link_type_valid_values() -> None:
    detector, _ = make_detector()
    # Notes with same domain → reinforcing
    note_a = {
        "path": "a.md",
        "content": "von Mises stress 250 MPa yield strength",
        "frontmatter": {"domain": "structural"},
    }
    note_b = {
        "path": "b.md",
        "content": "von Mises stress 250 MPa finite element",
        "frontmatter": {"domain": "structural"},
    }
    note_c = {
        "path": "c.md",
        "content": "von Mises stress 250 MPa thermal conductivity",
        "frontmatter": {"domain": "thermal"},
    }
    all_notes = [note_a, note_b, note_c]
    candidates = detector.detect_candidates(all_notes)
    assert len(candidates) >= 1
    for c in candidates:
        assert c.link_type in VALID_LINK_TYPES, f"Unexpected link_type: {c.link_type!r}"


# ---------------------------------------------------------------------------
# AC 6: write_candidates() calls upsert_note() with path beginning "ilc/links/".
# ---------------------------------------------------------------------------


def test_write_candidates_path_prefix() -> None:
    detector, mock_vault = make_detector()
    candidate = ILCCandidate(
        note_a_path="engineering/stress.md",
        note_b_path="engineering/thermal.md",
        shared_terms=["von Mises stress", "250 MPa"],
        link_type="cross-domain",
        confidence=0.75,
    )
    detector.write_candidates([candidate])
    assert mock_vault.upsert_note.called
    call_args = mock_vault.upsert_note.call_args
    path_arg = call_args[0][0]  # first positional arg
    assert path_arg.startswith("ilc/links/"), (
        f"Expected path starting with 'ilc/links/', got: {path_arg!r}"
    )


# ---------------------------------------------------------------------------
# AC 7: min_shared_terms=3 with only 2 shared terms → no candidates.
# ---------------------------------------------------------------------------


def test_min_shared_terms_threshold() -> None:
    detector, _ = make_detector()
    # NOTE_STRESS_A and NOTE_STRESS_B share exactly 2 terms (von Mises stress + 200 MPa)
    # plus FEA. Let's use notes that share exactly 2 known terms.
    note_a = {
        "path": "a.md",
        "content": "von Mises stress is 300 MPa.",
        "frontmatter": {},
    }
    note_b = {
        "path": "b.md",
        "content": "von Mises stress reaches 300 MPa under load.",
        "frontmatter": {},
    }
    # With default min_shared_terms=2, should find candidates
    candidates_default = detector.detect_candidates([note_a, note_b], min_shared_terms=2)
    assert len(candidates_default) >= 1, "Expected at least one candidate with min_shared_terms=2"

    # With min_shared_terms=3, should find no candidates (only 2 shared terms)
    candidates_high = detector.detect_candidates([note_a, note_b], min_shared_terms=3)
    assert candidates_high == [], (
        f"Expected no candidates with min_shared_terms=3, got: {candidates_high}"
    )


# ---------------------------------------------------------------------------
# AC 8: Cross-domain classification when notes have different domain frontmatter.
# ---------------------------------------------------------------------------


def test_cross_domain_classification() -> None:
    detector, _ = make_detector()
    note_structural = {
        "path": "engineering/structural.md",
        "content": "von Mises stress 200 MPa yield strength buckling load",
        "frontmatter": {"domain": "structural"},
    }
    note_thermal = {
        "path": "engineering/thermal.md",
        "content": "von Mises stress 200 MPa thermal conductivity heat transfer",
        "frontmatter": {"domain": "thermal"},
    }
    candidates = detector.detect_candidates([note_structural, note_thermal])
    assert len(candidates) >= 1
    cross_domain = [c for c in candidates if c.link_type == "cross-domain"]
    assert len(cross_domain) >= 1, (
        f"Expected at least one cross-domain candidate. Candidates: {candidates}"
    )
