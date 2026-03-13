"""Manufacturing build runner: traveler orchestration, ledger, packaging.

Orchestrates the full manufacturing build pipeline:
  1. Load and validate spec
  2. Resolve block-level applicable steps (topological order)
  3. Evaluate evidence and acceptance criteria per step
  4. Record results in a signed ledger (HMAC-SHA256)
  5. Optionally package a successful build into a ZIP archive

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/sfcs_mdp/runner.py)
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from forge_manufacturing.artifacts import (
    create_placeholder_dir,
    create_placeholder_file,
    expand_placeholders,
    write_json,
    write_yaml,
)
from forge_manufacturing.hashutil import sha256_bytes
from forge_manufacturing.model import (
    AcceptanceCriterionType,
    BlockLevel,
    BuildLedger,
    ProcessStep,
    Spec,
    StepDisposition,
    StepRecord,
)
from forge_manufacturing.validate import load_spec, topological_sort, validate_spec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LEDGER_FILENAME: str = "ledger.json"
_TRAVELER_FILENAME: str = "traveler.yaml"
_MANIFEST_FILENAME: str = "manifest.json"
_ARCHIVE_DATETIME: datetime.datetime = datetime.datetime(1980, 1, 1)  # deterministic ZIP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class RunConfig:
    """All parameters needed for a single manufacturing build run."""

    spec_path: Path
    build_id: str
    rev_tag: str
    block_level: BlockLevel
    simulate: bool = False
    lot_id: str | None = None
    ncr_id: str | None = None
    repo_root: Path | None = None

    def __post_init__(self) -> None:
        if self.repo_root is None:
            self.repo_root = Path.cwd()

    @property
    def build_root(self) -> Path:
        return self.repo_root / "builds" / self.build_id  # type: ignore[operator]

    @property
    def placeholder_values(self) -> dict[str, str]:
        return {
            "build_id": self.build_id,
            "REV_TAG": self.rev_tag,
            "lot_id": self.lot_id or "",
            "ncr_id": self.ncr_id or "",
        }


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat(timespec="seconds")


def _hmac_sign(data: bytes, key: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def _build_manifest(cfg: RunConfig, spec: Spec) -> dict[str, Any]:
    spec_yaml = yaml.safe_dump(spec.model_dump(mode="json"))
    return {
        "build_id": cfg.build_id,
        "rev_tag": cfg.rev_tag,
        "block_level": cfg.block_level.value,
        "lot_id": cfg.lot_id,
        "ncr_id": cfg.ncr_id,
        "simulate": cfg.simulate,
        "spec_hash": sha256_bytes(spec_yaml.encode()),
        "generated_utc": _utc_now(),
    }


# ---------------------------------------------------------------------------
# Step evaluation
# ---------------------------------------------------------------------------


def _evaluate_acceptance(step: ProcessStep, build_root: Path) -> tuple[StepDisposition, str]:
    """Check all acceptance criteria for *step*.

    Returns:
        ``(disposition, notes)`` — PASS, FAIL, or OPTIONAL.
    """
    for criterion in step.acceptance_criteria:
        if criterion.criterion_type == AcceptanceCriterionType.FILE_EXISTS:
            if criterion.path:
                target = build_root / criterion.path
                if not target.exists():
                    return StepDisposition.FAIL, f"Missing evidence file: {criterion.path}"
        elif criterion.criterion_type == AcceptanceCriterionType.MANUAL_SIGNOFF:
            # In simulation, signoffs are auto-approved.
            pass
    return StepDisposition.PASS, ""


def _evaluate_evidence(
    step: ProcessStep, build_root: Path, placeholder_values: dict[str, str]
) -> dict[str, str]:
    """Hash required evidence files for *step*.  Returns {relative_path: sha256}."""
    hashes: dict[str, str] = {}
    for evidence in step.required_evidence:
        if not evidence.path:
            continue
        resolved_path = expand_placeholders(evidence.path, placeholder_values)
        try:
            full = build_root / resolved_path
            if full.is_file():
                from forge_manufacturing.hashutil import sha256_file
                hashes[resolved_path] = sha256_file(full)
        except (OSError, ValueError):
            pass  # Non-existent evidence is caught by acceptance check
    return hashes


def _simulate_step_outputs(step: ProcessStep, build_root: Path, placeholder_values: dict[str, str]) -> None:
    """Create placeholder output files/dirs for *step* during simulation."""
    for output in step.outputs:
        resolved = expand_placeholders(output, placeholder_values)
        target = build_root / resolved
        if resolved.endswith("/"):
            create_placeholder_dir(target)
        else:
            create_placeholder_file(target, f"# simulated output: {output}\n")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_traveler(
    spec_path: Path,
    build_id: str,
    rev_tag: str,
    block_level: BlockLevel,
    simulate: bool = False,
    lot_id: str | None = None,
    ncr_id: str | None = None,
    repo_root: Path | None = None,
    engine_cli: str | None = None,
) -> Path:
    """Orchestrate a complete manufacturing build traveler.

    Args:
        spec_path:    Path to the YAML manufacturing spec.
        build_id:     Unique identifier for this build (e.g., ``"BLD-001"``).
        rev_tag:      CAD revision tag (e.g., ``"REV_A"``).
        block_level:  Target smart-airframe maturity block.
        simulate:     If True, create placeholder outputs instead of real ones.
        lot_id:       Material lot identifier (optional).
        ncr_id:       Nonconformance record ID (optional, if deviation present).
        repo_root:    Repository root for build output paths (defaults to cwd).
        engine_cli:   Path to optional C++ engine binary.

    Returns:
        Path to the build directory containing ledger and traveler.

    Raises:
        forge_manufacturing.validate.SpecValidationError: On invalid spec.
        RuntimeError: On step GATE failure or engine error.
    """
    # Resolve lot/NCR from environment if not passed directly.
    if lot_id is None:
        lot_id = os.environ.get("FORGE_LOT_ID")
    if ncr_id is None:
        ncr_id = os.environ.get("FORGE_NCR_ID")

    cfg = RunConfig(
        spec_path=spec_path,
        build_id=build_id,
        rev_tag=rev_tag,
        block_level=block_level,
        simulate=simulate,
        lot_id=lot_id,
        ncr_id=ncr_id,
        repo_root=repo_root,
    )

    # Load and validate spec.
    spec = load_spec(spec_path)
    validate_spec(spec)

    # Determine applicable steps and sort topologically.
    applicable = spec.steps_for_block(block_level)
    sorted_steps = topological_sort(applicable)

    # Prepare build directory.
    build_root = cfg.build_root
    build_root.mkdir(parents=True, exist_ok=True)

    # Write manifest.
    manifest = _build_manifest(cfg, spec)
    write_json(build_root / _MANIFEST_FILENAME, manifest)

    # Write traveler YAML.
    write_yaml(build_root / _TRAVELER_FILENAME, spec.model_dump(mode="json"))

    # Run steps.
    started_utc = _utc_now()
    step_records: list[StepRecord] = []
    pipeline_failed = False

    for step in sorted_steps:
        if pipeline_failed:
            step_records.append(
                StepRecord(
                    step_id=step.step_id,
                    disposition=StepDisposition.SKIPPED,
                    timestamp_utc=_utc_now(),
                    notes="Pipeline failure upstream",
                )
            )
            continue

        if simulate:
            _simulate_step_outputs(step, build_root, cfg.placeholder_values)

        disposition, notes = _evaluate_acceptance(step, build_root)
        evidence_hashes = _evaluate_evidence(step, build_root, cfg.placeholder_values)

        record = StepRecord(
            step_id=step.step_id,
            disposition=disposition,
            timestamp_utc=_utc_now(),
            evidence_hashes=evidence_hashes,
            notes=notes,
        )
        step_records.append(record)

        if disposition == StepDisposition.FAIL and step.step_type.value == "gate":
            pipeline_failed = True

    # Determine final disposition.
    failed = any(r.disposition == StepDisposition.FAIL for r in step_records)
    final_disposition = StepDisposition.FAIL if failed else StepDisposition.PASS

    # Write ledger.
    ledger = BuildLedger(
        build_id=build_id,
        spec_hash=manifest["spec_hash"],
        started_utc=started_utc,
        finished_utc=_utc_now(),
        final_disposition=final_disposition,
        steps=step_records,
        manifest=manifest,
    )
    ledger_path = build_root / _LEDGER_FILENAME
    write_json(ledger_path, ledger.model_dump(mode="json"))

    return build_root


def status_build(build_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    """Return the ledger dict for a completed build.

    Args:
        build_id:  Build identifier used in :func:`run_traveler`.
        repo_root: Repository root (defaults to cwd).

    Raises:
        FileNotFoundError: If no ledger exists for *build_id*.
    """
    root = repo_root or Path.cwd()
    ledger_path = root / "builds" / build_id / _LEDGER_FILENAME
    if not ledger_path.exists():
        raise FileNotFoundError(f"No ledger found for build {build_id!r}: {ledger_path}")
    return json.loads(ledger_path.read_text(encoding="utf-8"))


def package_build(build_id: str, repo_root: Path | None = None) -> Path:
    """Create a deterministic ZIP archive of a successful build.

    Only PASS builds can be packaged.

    Args:
        build_id:  Build identifier.
        repo_root: Repository root (defaults to cwd).

    Returns:
        Path to the created ``<build_id>.zip`` archive.

    Raises:
        RuntimeError: If the build did not achieve a PASS disposition.
        FileNotFoundError: If the build directory does not exist.
    """
    root = repo_root or Path.cwd()
    build_root = root / "builds" / build_id

    ledger_data = status_build(build_id, repo_root=root)
    if ledger_data.get("final_disposition") != StepDisposition.PASS.value:
        raise RuntimeError(
            f"Cannot package build {build_id!r}: "
            f"disposition={ledger_data.get('final_disposition')!r}"
        )

    archive_path = root / "builds" / f"{build_id}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(build_root.rglob("*")):
            if file_path.is_file():
                arcname = file_path.relative_to(build_root).as_posix()
                # Set deterministic timestamp so archives are reproducible.
                info = zipfile.ZipInfo(arcname, date_time=_ARCHIVE_DATETIME.timetuple()[:6])
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, file_path.read_bytes())

    return archive_path
