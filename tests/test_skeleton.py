"""Tests for the FORGE scaffolding skeleton — Components A through L.

Validates that every package, module, and key class defined in the
master skeleton can be imported and instantiated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# A. Core Runtime
# ---------------------------------------------------------------------------

class TestCoreRuntime:
    """Component A — runtime orchestration spine."""

    def test_import_pipeline_run(self) -> None:
        from forge.runtime import PipelineRun, PipelineStatus
        run = PipelineRun(run_id="test-run-1")
        assert run.status == PipelineStatus.PENDING

    def test_init_steps_creates_twelve_steps(self) -> None:
        from forge.runtime import PipelineRun
        run = PipelineRun(run_id="r1")
        run.init_steps()
        assert len(run.steps) == 12
        assert run.steps[0].name == "receive_query"
        assert run.steps[11].name == "return_response"

    def test_step_result_defaults_pending(self) -> None:
        from forge.runtime import StepResult, PipelineStatus
        step = StepResult(step=1, name="receive_query")
        assert step.status == PipelineStatus.PENDING
        assert step.output is None


# ---------------------------------------------------------------------------
# B. Agent System
# ---------------------------------------------------------------------------

class TestAgentSystem:
    """Component B — agent base class and AgentResult."""

    def test_agent_result_creation(self) -> None:
        from forge.agents.base import AgentResult
        res = AgentResult(agent_id="E-01", status="ok")
        assert res.agent_id == "E-01"
        assert res.payload == {}
        assert res.sources == []

    def test_base_agent_is_abstract(self) -> None:
        from forge.agents.base import BaseAgent
        with pytest.raises(TypeError):
            BaseAgent(agent_id="X", role="test")  # type: ignore[abstract]

    def test_concrete_agent_can_run(self) -> None:
        from forge.agents.base import BaseAgent, AgentResult

        class Stub(BaseAgent):
            def run(self, context: dict[str, Any]) -> AgentResult:
                return AgentResult(agent_id=self.agent_id, payload=context)

        agent = Stub(agent_id="STUB-01", role="stub")
        result = agent.run({"key": "value"})
        assert result.agent_id == "STUB-01"
        assert result.payload == {"key": "value"}


# ---------------------------------------------------------------------------
# C. Memory System
# ---------------------------------------------------------------------------

class TestMemorySystem:
    """Component C — vault memory layer."""

    def test_vault_note_defaults(self) -> None:
        from forge.memory.vault import VaultNote
        note = VaultNote()
        assert note.domain == "general"
        assert note.confidence == 0.0

    def test_vault_store_read_missing(self, tmp_path: Path) -> None:
        from forge.memory.vault import VaultStore
        store = VaultStore(vault_root=tmp_path)
        assert store.read_note("nonexistent.md") is None

    def test_vault_store_write_read_roundtrip(self, tmp_path: Path) -> None:
        from forge.memory.vault import VaultStore, VaultNote
        store = VaultStore(vault_root=tmp_path)
        note = VaultNote(path="test/note.md", body="# Hello")
        store.write_note(note)
        loaded = store.read_note("test/note.md")
        assert loaded is not None
        assert loaded.body == "# Hello"

    def test_vault_store_list_notes(self, tmp_path: Path) -> None:
        from forge.memory.vault import VaultStore, VaultNote
        store = VaultStore(vault_root=tmp_path)
        store.write_note(VaultNote(path="a.md", body="a"))
        store.write_note(VaultNote(path="b.md", body="b"))
        notes = store.list_notes()
        assert len(notes) == 2


# ---------------------------------------------------------------------------
# D. Tooling Layer
# ---------------------------------------------------------------------------

class TestToolingLayer:
    """Component D — tool wrapper base."""

    def test_tool_result_defaults(self) -> None:
        from forge.tools.base import ToolResult
        res = ToolResult(tool_id="T-01")
        assert res.success is False
        assert res.exit_code is None

    def test_tool_wrapper_is_abstract(self) -> None:
        from forge.tools.base import ToolWrapper
        with pytest.raises(TypeError):
            ToolWrapper(tool_id="T-99")  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# E. Verification Layer
# ---------------------------------------------------------------------------

class TestVerificationLayer:
    """Component E — structural and adversarial verification."""

    def test_structural_check_passes_complete_output(self) -> None:
        from forge.verification.structural import (
            check_mandatory_fields,
            MANDATORY_FIELDS,
        )
        output = {f: "value" for f in MANDATORY_FIELDS}
        verdict = check_mandatory_fields(output)
        assert verdict.passed is True
        assert verdict.missing_fields == []

    def test_structural_check_detects_missing_fields(self) -> None:
        from forge.verification.structural import check_mandatory_fields
        verdict = check_mandatory_fields({"analysis_id": "x"})
        assert verdict.passed is False
        assert len(verdict.missing_fields) == 10

    def test_adversarial_score_computation(self) -> None:
        from forge.verification.adversarial import (
            AdversarialVerdict,
            AdversarialChallenge,
        )
        v = AdversarialVerdict(challenges=[
            AdversarialChallenge(description="edge-case-1", survived=True),
            AdversarialChallenge(description="edge-case-2", survived=False),
        ])
        score = v.compute_score()
        assert score == pytest.approx(0.5)

    def test_adversarial_empty_challenges(self) -> None:
        from forge.verification.adversarial import AdversarialVerdict
        v = AdversarialVerdict()
        assert v.compute_score() == 0.0


# ---------------------------------------------------------------------------
# F. Data Contracts
# ---------------------------------------------------------------------------

class TestDataContracts:
    """Component F — Pydantic contract models."""

    def test_analysis_output_has_mandatory_fields(self) -> None:
        from forge.contracts import AnalysisOutput
        ao = AnalysisOutput(
            analysis_id="test-1",
            query="What is the stress?",
            methodology="beam theory",
        )
        assert ao.confidence == 0.0
        assert ao.verification_status == "pending"

    def test_trace_record_creation(self) -> None:
        from forge.contracts import TraceRecord
        tr = TraceRecord(
            trace_id="abc123", agent_id="E-01", step=5, event="analysis"
        )
        assert tr.trace_id == "abc123"
        assert tr.step == 5

    def test_tool_response_creation(self) -> None:
        from forge.contracts import ToolResponse
        tr = ToolResponse(tool_id="T-01", success=True)
        assert tr.success is True


# ---------------------------------------------------------------------------
# G. Observability & Ops
# ---------------------------------------------------------------------------

class TestObservability:
    """Component G — metrics and error codes."""

    def test_error_codes_exist(self) -> None:
        from forge.observability import ErrorCode
        assert ErrorCode.BUDGET_EXCEEDED.value == "E-BDG-001"
        assert ErrorCode.PROVIDER_UNREACHABLE.value == "E-PRV-001"

    def test_metrics_counter_api_calls(self) -> None:
        from forge.observability import MetricsCounter
        m = MetricsCounter()
        m.record_api_call(cost_usd=0.05)
        m.record_api_call(cost_usd=0.03)
        assert m.api_calls == 2
        assert m.total_cost_usd == pytest.approx(0.08)

    def test_metrics_counter_agent_runs(self) -> None:
        from forge.observability import MetricsCounter
        m = MetricsCounter()
        m.record_agent_run("E-01")
        m.record_agent_run("E-01")
        m.record_agent_run("V-ADV")
        assert m.agent_runs["E-01"] == 2
        assert m.agent_runs["V-ADV"] == 1


# ---------------------------------------------------------------------------
# H. Build/Test Harness
# ---------------------------------------------------------------------------

class TestBuildTestHarness:
    """Component H — fixtures infrastructure."""

    def test_golden_fixture_file_exists(self) -> None:
        fixture = (
            Path(__file__).resolve().parent / "fixtures" / "cantilever_beam.yaml"
        )
        assert fixture.exists(), "Golden fixture file missing"

    def test_golden_fixture_is_valid_yaml(self) -> None:
        import yaml
        fixture = (
            Path(__file__).resolve().parent / "fixtures" / "cantilever_beam.yaml"
        )
        data = yaml.safe_load(fixture.read_text())
        assert "fixture" in data
        assert data["fixture"]["id"] == "GF-001"
        assert "expected" in data


# ---------------------------------------------------------------------------
# I. Project Pipelines
# ---------------------------------------------------------------------------

class TestProjectPipelines:
    """Component I — pipeline registry."""

    def test_pipeline_registry_roundtrip(self) -> None:
        from forge.pipelines.registry import PipelineRegistry, PipelineSpec
        reg = PipelineRegistry()
        spec = PipelineSpec(name="aladdin-3b", agents=["ORCH-01", "E-01"])
        reg.register(spec)
        assert reg.get("aladdin-3b") is spec
        assert "aladdin-3b" in reg.list_names()

    def test_registry_get_missing_returns_none(self) -> None:
        from forge.pipelines.registry import PipelineRegistry
        reg = PipelineRegistry()
        assert reg.get("nonexistent") is None


# ---------------------------------------------------------------------------
# J. External Ecosystem Bridges
# ---------------------------------------------------------------------------

class TestEcosystemBridges:
    """Component J — bridge base class."""

    def test_bridge_result_defaults(self) -> None:
        from forge.bridges.base import BridgeResult
        br = BridgeResult(bridge_id="CAD-01")
        assert br.success is False

    def test_base_bridge_is_abstract(self) -> None:
        from forge.bridges.base import BaseBridge
        with pytest.raises(TypeError):
            BaseBridge(bridge_id="X")  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# K. Planning Corpus — already exists; verify presence only
# ---------------------------------------------------------------------------

class TestPlanningCorpus:
    """Component K — verify canonical planning docs exist."""

    def test_planning_docs_exist(self, repo_root: Path) -> None:
        planning = repo_root / "docs" / "planning"
        assert (planning / "FORGE_CATALOG.md").exists()
        assert (planning / "FORGE_EXECUTION_PLAN.md").exists()
        assert (planning / "DECISIONS.md").exists()


# ---------------------------------------------------------------------------
# L. Recovery / Continuity
# ---------------------------------------------------------------------------

class TestRecoveryContinuity:
    """Component L — snapshot and recovery manager."""

    def test_snapshot_creation(self) -> None:
        from forge.recovery import Snapshot
        snap = Snapshot(snapshot_id="snap-1", blackboard={"key": "val"})
        assert snap.snapshot_id == "snap-1"
        assert snap.created_at  # non-empty timestamp

    def test_recovery_manager_save_restore(self) -> None:
        from forge.recovery import RecoveryManager, Snapshot
        mgr = RecoveryManager()
        snap = Snapshot(snapshot_id="s1", blackboard={"x": 1})
        mgr.save(snap)
        restored = mgr.restore("s1")
        assert restored is not None
        assert restored.blackboard == {"x": 1}

    def test_recovery_manager_missing_returns_none(self) -> None:
        from forge.recovery import RecoveryManager
        mgr = RecoveryManager()
        assert mgr.restore("missing") is None

    def test_recovery_manager_list_ids(self) -> None:
        from forge.recovery import RecoveryManager, Snapshot
        mgr = RecoveryManager()
        mgr.save(Snapshot(snapshot_id="a"))
        mgr.save(Snapshot(snapshot_id="b"))
        assert sorted(mgr.list_ids()) == ["a", "b"]
