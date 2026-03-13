"""Tests for forge_manufacturing.runner — build traveler and pipeline runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_manufacturing.model import BlockLevel
from forge_manufacturing.runner import package_build, run_traveler, status_build


_SPECS_DIR = Path(__file__).parent.parent / "specs"
_SFCS_SPEC = _SPECS_DIR / "sfcs_drone_mdp_v0.yaml"


# ── run_traveler ──────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not _SFCS_SPEC.exists(),
    reason="sfcs_drone_mdp_v0.yaml not present",
)
def test_run_traveler_simulate_creates_build_dir(tmp_path: Path):
    """Simulation run should create the build directory with ledger + traveler."""
    build_dir = run_traveler(
        spec_path=_SFCS_SPEC,
        build_id="TEST-001",
        rev_tag="REV_A",
        block_level=BlockLevel.BLOCK_0,
        simulate=True,
        repo_root=tmp_path,
    )
    assert build_dir.exists()
    assert (build_dir / "ledger.json").exists()
    assert (build_dir / "traveler.yaml").exists()
    assert (build_dir / "manifest.json").exists()


@pytest.mark.skipif(
    not _SFCS_SPEC.exists(),
    reason="sfcs_drone_mdp_v0.yaml not present",
)
def test_run_traveler_simulate_ledger_structure(tmp_path: Path):
    """Ledger must contain required top-level keys."""
    run_traveler(
        spec_path=_SFCS_SPEC,
        build_id="TEST-002",
        rev_tag="REV_A",
        block_level=BlockLevel.BLOCK_0,
        simulate=True,
        repo_root=tmp_path,
    )
    ledger = json.loads((tmp_path / "builds" / "TEST-002" / "ledger.json").read_text())
    assert ledger["build_id"] == "TEST-002"
    assert "spec_hash" in ledger
    assert "steps" in ledger
    assert "final_disposition" in ledger


@pytest.mark.skipif(
    not _SFCS_SPEC.exists(),
    reason="sfcs_drone_mdp_v0.yaml not present",
)
def test_run_traveler_simulate_pass_disposition(tmp_path: Path):
    """A simulation with no evidence files should still record a final disposition."""
    run_traveler(
        spec_path=_SFCS_SPEC,
        build_id="TEST-003",
        rev_tag="REV_A",
        block_level=BlockLevel.BLOCK_0,
        simulate=True,
        repo_root=tmp_path,
    )
    ledger = json.loads((tmp_path / "builds" / "TEST-003" / "ledger.json").read_text())
    assert ledger["final_disposition"] in ("PASS", "FAIL")


# ── status_build ──────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not _SFCS_SPEC.exists(),
    reason="sfcs_drone_mdp_v0.yaml not present",
)
def test_status_build_returns_ledger(tmp_path: Path):
    run_traveler(
        spec_path=_SFCS_SPEC,
        build_id="TEST-STATUS",
        rev_tag="REV_A",
        block_level=BlockLevel.BLOCK_0,
        simulate=True,
        repo_root=tmp_path,
    )
    ledger = status_build("TEST-STATUS", repo_root=tmp_path)
    assert ledger["build_id"] == "TEST-STATUS"


def test_status_build_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        status_build("NONEXISTENT", repo_root=tmp_path)


# ── package_build ─────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not _SFCS_SPEC.exists(),
    reason="sfcs_drone_mdp_v0.yaml not present",
)
def test_package_build_creates_zip(tmp_path: Path):
    run_traveler(
        spec_path=_SFCS_SPEC,
        build_id="TEST-PKG",
        rev_tag="REV_A",
        block_level=BlockLevel.BLOCK_0,
        simulate=True,
        repo_root=tmp_path,
    )
    # Patch ledger to PASS so packaging is allowed
    ledger_path = tmp_path / "builds" / "TEST-PKG" / "ledger.json"
    ledger = json.loads(ledger_path.read_text())
    ledger["final_disposition"] = "PASS"
    ledger_path.write_text(json.dumps(ledger))

    archive = package_build("TEST-PKG", repo_root=tmp_path)
    assert archive.exists()
    assert archive.suffix == ".zip"


def test_package_build_fails_without_pass(tmp_path: Path):
    """package_build must fail if the ledger has a non-PASS disposition."""
    build_dir = tmp_path / "builds" / "FAIL-BUILD"
    build_dir.mkdir(parents=True)
    ledger = {
        "build_id": "FAIL-BUILD",
        "spec_hash": "abc",
        "started_utc": "2026-01-01T00:00:00",
        "final_disposition": "FAIL",
        "steps": [],
    }
    (build_dir / "ledger.json").write_text(json.dumps(ledger))

    with pytest.raises(RuntimeError, match="disposition"):
        package_build("FAIL-BUILD", repo_root=tmp_path)
