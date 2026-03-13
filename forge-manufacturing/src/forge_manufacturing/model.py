"""Pydantic data models for smart airframe manufacturing specifications.

Models represent the FORGE digital thread for smart airframe builds:
  - Maturity progression (BLOCK_0 → BLOCK_4)
  - Quality management (MRB dispositions, NCR tracking)
  - Process flow (topologically-ordered gate/process steps)
  - Risk register

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/sfcs_mdp/model.py)
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class StepType(str, Enum):
    """Whether a workflow step is a quality gate or a production process."""

    GATE = "gate"
    PROCESS = "process"


class AcceptanceCriterionType(str, Enum):
    """How an acceptance criterion is evaluated."""

    FILE_EXISTS = "file_exists"
    MANUAL_SIGNOFF = "manual_signoff"


class StepDisposition(str, Enum):
    """Recorded outcome of a process step execution."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    OPTIONAL = "OPTIONAL"


class BlockLevel(str, Enum):
    """Smart airframe maturity block level.

    Progression:
      BLOCK_0 — composite structure + metallic interfaces
      BLOCK_1 — adds structural health monitoring (optical sensing)
      BLOCK_2 — integrates embedded power distribution
      BLOCK_3 — distributed sensor tiles + deterministic comms
      BLOCK_4 — conformal energy modules (post-cure)
    """

    BLOCK_0 = "BLOCK_0"
    BLOCK_1 = "BLOCK_1"
    BLOCK_2 = "BLOCK_2"
    BLOCK_3 = "BLOCK_3"
    BLOCK_4 = "BLOCK_4"


# Ordered list used for block-level comparisons (>= semantics).
_BLOCK_ORDER: list[BlockLevel] = [
    BlockLevel.BLOCK_0,
    BlockLevel.BLOCK_1,
    BlockLevel.BLOCK_2,
    BlockLevel.BLOCK_3,
    BlockLevel.BLOCK_4,
]


def block_index(level: BlockLevel) -> int:
    """Return the numeric index of *level* (0 = BLOCK_0, 4 = BLOCK_4)."""
    return _BLOCK_ORDER.index(level)


def block_gte(level: BlockLevel, minimum: BlockLevel) -> bool:
    """Return True if *level* is at least as advanced as *minimum*."""
    return block_index(level) >= block_index(minimum)


# ---------------------------------------------------------------------------
# Base model config
# ---------------------------------------------------------------------------


class _StrictModel(BaseModel):
    """Shared base: ignore unknown fields so external YAML specs load cleanly."""

    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class MaturityLevel(_StrictModel):
    """Current and target maturity levels for the program."""

    current: BlockLevel
    target: BlockLevel


class MaturityModel(_StrictModel):
    """Full maturity model descriptor."""

    levels: list[str] = Field(default_factory=list)
    current: BlockLevel
    target: BlockLevel


class Meta(_StrictModel):
    """Program-level metadata."""

    program_name: str = ""
    owner: str = ""
    scope: str = ""
    exclusions: list[str] = Field(default_factory=list)
    maturity: MaturityLevel | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_program_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "program_name" not in data and "program" in data:
            data = dict(data)
            data["program_name"] = data["program"]
        return data


# ---------------------------------------------------------------------------
# Digital thread
# ---------------------------------------------------------------------------


class SingleSourceOfTruth(_StrictModel):
    """References to the canonical parameter and artifact stores."""

    parameter_registry: str = ""
    requirements: str = ""
    cad_revisions: str = ""
    toolpaths: str = ""
    process_parameter_sets: str | dict[str, str] = ""


class BuildManifestSpec(_StrictModel):
    """Schema for what a frozen build manifest must contain."""

    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)


class DigitalThread(_StrictModel):
    """Digital-thread infrastructure for a manufacturing program."""

    single_source_of_truth: SingleSourceOfTruth = Field(
        default_factory=SingleSourceOfTruth
    )
    build_manifest_spec: BuildManifestSpec = Field(default_factory=BuildManifestSpec)


# ---------------------------------------------------------------------------
# Quality system
# ---------------------------------------------------------------------------


class ConfigurationManagement(_StrictModel):
    """Configuration management policy."""

    policy: str | list[str] = ""
    frozen_manifest_required: bool = True
    signed_traveler_required: bool = True


class MRBDisposition(str, Enum):
    """Material Review Board disposition options for nonconformances."""

    USE_AS_IS = "use_as_is"
    REWORK = "rework"
    REPAIR = "repair"
    SCRAP = "scrap"


class NonconformanceSystem(_StrictModel):
    """Nonconformance record (NCR) and MRB handling configuration."""

    ncr_required: bool = True
    mrb_dispositions: list[MRBDisposition] = Field(default_factory=list)


class QualitySystem(_StrictModel):
    """Full quality management framework for the manufacturing program."""

    configuration_management: ConfigurationManagement = Field(
        default_factory=ConfigurationManagement
    )
    nonconformance: NonconformanceSystem = Field(default_factory=NonconformanceSystem)
    first_article_inspection: bool = False
    acceptance_data_package: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Process flow
# ---------------------------------------------------------------------------


class WhenCondition(_StrictModel):
    """Conditional execution gate based on block level."""

    block_level_gte: BlockLevel | None = None


class AcceptanceCriterion(_StrictModel):
    """Single acceptance check for a process step."""

    criterion_type: AcceptanceCriterionType
    description: str = ""
    path: str | None = None  # Used when criterion_type == FILE_EXISTS


class Evidence(_StrictModel):
    """Required evidence artifact for step completion."""

    name: str
    path: str = ""


class ProcessStep(_StrictModel):
    """A single step (gate or process) in the manufacturing workflow."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    step_type: StepType
    description: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    when: WhenCondition | None = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    required_evidence: list[Evidence] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Risk register
# ---------------------------------------------------------------------------


class RiskItem(_StrictModel):
    """An identified program risk with mitigation strategy."""

    risk_id: str
    description: str
    mitigation: str = ""
    owner: str = ""


# ---------------------------------------------------------------------------
# Instrumentation
# ---------------------------------------------------------------------------


class InstrumentationMinimum(_StrictModel):
    """Minimum instrumentation required for the program."""

    manufacturing: list[str] = Field(default_factory=list)
    embedded_systems: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level spec
# ---------------------------------------------------------------------------


class Spec(_StrictModel):
    """Root manufacturing specification document.

    Loaded from YAML via :func:`forge_manufacturing.validate.load_spec`.
    """

    meta: Meta
    digital_thread: DigitalThread = Field(default_factory=DigitalThread)
    quality_system: QualitySystem = Field(default_factory=QualitySystem)
    process_flow: list[ProcessStep] = Field(default_factory=list)
    instrumentation: InstrumentationMinimum = Field(
        default_factory=InstrumentationMinimum
    )
    risks: list[RiskItem] = Field(default_factory=list)

    # Allow extra top-level keys (e.g., spec_version, revision) in YAML
    model_config = ConfigDict(extra="allow")

    def steps_for_block(self, level: BlockLevel) -> list[ProcessStep]:
        """Return only the steps applicable to *level* (respecting WhenCondition)."""
        result: list[ProcessStep] = []
        for step in self.process_flow:
            if step.when is None:
                result.append(step)
            elif step.when.block_level_gte is not None:
                if block_gte(level, step.when.block_level_gte):
                    result.append(step)
            else:
                result.append(step)
        return result


# ---------------------------------------------------------------------------
# Ledger entry (runtime artifact — not loaded from YAML)
# ---------------------------------------------------------------------------


class StepRecord(BaseModel):
    """Immutable record of a single step execution, stored in the build ledger."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    disposition: StepDisposition
    timestamp_utc: str
    evidence_hashes: dict[str, str] = Field(default_factory=dict)
    notes: str = ""
    error: str | None = None


class BuildLedger(BaseModel):
    """Complete execution record for a manufacturing build."""

    model_config = ConfigDict(extra="forbid")

    build_id: str
    spec_hash: str
    started_utc: str
    finished_utc: str | None = None
    final_disposition: StepDisposition | None = None
    steps: list[StepRecord] = Field(default_factory=list)
    manifest: dict[str, Any] = Field(default_factory=dict)
