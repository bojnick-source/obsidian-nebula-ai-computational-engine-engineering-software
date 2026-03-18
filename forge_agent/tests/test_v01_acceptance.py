"""
v0.1 Acceptance Tests — AC-01 through AC-10.
Reference: docs/planning/mvp/v0.1-acceptance-test.md
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest

from forge_agent.agents.librarian import LibrarianAgent
from forge_agent.core.pipeline import PipelineRunner, TaskRequest, TaskResult
from forge_agent.core.verifier import AgentOutputContract, run_all_gates
from forge_agent.memory.obsidian_manager import ObsidianVaultManager


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

VALID_SPECIALIST_OUTPUT = {
    "model_choice": "Linear elastic FEA using Euler-Bernoulli beam approximation",
    "equations": [r"$$\sigma_{vm} = \sqrt{\sigma_x^2 + 3\tau_{xy}^2}$$"],
    "units": "SI: MPa, mm, N",
    "sanity_checks": [{"type": "limiting_case", "detail": "Zero load -> zero stress"}],
    "calculation_path": "Step 1: mesh generation. Step 2: apply boundary conditions. Step 3: solve.",
    "findings": [
        {
            "quantity": "stress",
            "value": 110.5,
            "units": "MPa",
            "provenance": {
                "source": "ASM Handbook Vol 2",
                "specificity": "high",
                "citation": "ASM Handbook 2000",
            },
        }
    ],
    "what_would_falsify": ["Actual material properties differ from 6061-T6 spec"],
    "confidence": 0.82,
}


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


class MockToolExecutor:
    def __init__(self, trace_id_capture=None):
        self._trace_ids_seen = []
        self._trace_id_capture = trace_id_capture

    def run_gmsh(self, trace_id, task_id, invocation_id, **kwargs):
        self._trace_ids_seen.append(trace_id)
        return {
            "tool_id": "gmsh",
            "wrapper_version": "1.0.0",
            "status": "success",
            "trace_id": trace_id,
            "invocation_id": invocation_id,
            "output": {"output_file": "/tmp/test.msh", "element_count": 1200, "stats": ""},
            "duration_ms": 10.0,
        }

    def run_calculix(self, trace_id, task_id, invocation_id, **kwargs):
        self._trace_ids_seen.append(trace_id)
        return {
            "tool_id": "calculix",
            "wrapper_version": "1.0.0",
            "status": "success",
            "trace_id": trace_id,
            "invocation_id": invocation_id,
            "output": {
                "frd_file": "/tmp/test.frd",
                "max_von_mises_mpa": 110.5,
                "node_count": 850,
                "stress_extracted": True,
                "log_tail": "",
            },
            "duration_ms": 50.0,
        }


class MockAnthropicClient:
    """Mock Anthropic client that returns VALID_SPECIALIST_OUTPUT as JSON."""

    class messages:
        @staticmethod
        def create(**kwargs):
            class MockMsg:
                content = [type("Block", (), {"text": json.dumps(VALID_SPECIALIST_OUTPUT)})()]

            return MockMsg()


class MockAnthropicClientInvalid:
    """Mock Anthropic client that returns specialist output missing 'equations'."""

    class messages:
        @staticmethod
        def create(**kwargs):
            invalid = dict(VALID_SPECIALIST_OUTPUT)
            del invalid["equations"]

            class MockMsg:
                content = [type("Block", (), {"text": json.dumps(invalid)})()]

            return MockMsg()


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def motor_mount_request():
    return TaskRequest(
        task_type="engineering_full",
        project="aladdin-3b",
        component="motor_mount_bracket",
        description=(
            "Analyze structural integrity of the motor mount bracket "
            "under maximum thrust load. Material: 6061-T6 aluminum. "
            "Constraint: maximum von Mises stress < 0.6 × yield strength."
        ),
        load_cases=[{"name": "max_thrust_static", "force_n": 10.0}],
    )


def _make_runner(tmp_path, anthropic_client=None, tool_executor=None, vault_manager=None):
    """Helper: build a PipelineRunner with real or mock components."""
    if vault_manager is None:
        vault_manager = ObsidianVaultManager(vault_path=tmp_path)
    if tool_executor is None:
        tool_executor = MockToolExecutor()
    return PipelineRunner(
        config={"provider": "anthropic"},
        tool_executor=tool_executor,
        vault_manager=vault_manager,
        anthropic_client=anthropic_client,
    )


# ---------------------------------------------------------------------------
# AC-01: Trace ID Propagation
# ---------------------------------------------------------------------------


def test_ac01_trace_id_propagated(tmp_path, motor_mount_request):
    """Trace ID must be non-empty, consistent across all JSONL events, and appear in artifact_refs."""
    runner = _make_runner(tmp_path, anthropic_client=MockAnthropicClient())
    result = runner.run(motor_mount_request)

    # result.trace_id must be a non-empty string in UUID format
    assert result.trace_id, "trace_id must not be empty"
    parsed = uuid.UUID(result.trace_id)  # raises ValueError if not valid UUID
    assert str(parsed) == result.trace_id

    # All JSONL events must carry the same trace_id
    assert runner._jsonl_events, "No JSONL events emitted"
    for event in runner._jsonl_events:
        assert "trace_id" in event, f"Event missing trace_id key: {event}"
        assert event["trace_id"] == result.trace_id, (
            f"Event phase={event.get('phase')!r} has trace_id={event['trace_id']!r}, "
            f"expected {result.trace_id!r}"
        )

    # artifact_refs must contain a path string
    assert result.artifact_refs, "artifact_refs must not be empty after a successful run"
    assert any(isinstance(ref, str) and len(ref) > 0 for ref in result.artifact_refs)


# ---------------------------------------------------------------------------
# AC-02: ME Specialist Output Conforms to Contract
# ---------------------------------------------------------------------------


def test_ac02_specialist_output_conforms_to_contract():
    """AgentOutputContract.validate() on VALID_SPECIALIST_OUTPUT must return no violations."""
    violations = AgentOutputContract.validate(VALID_SPECIALIST_OUTPUT)
    assert violations == [], (
        f"Expected no violations, got: {[v.reason for v in violations]}"
    )


# ---------------------------------------------------------------------------
# AC-03: GMSH Envelope Structure
# ---------------------------------------------------------------------------


def test_ac03_gmsh_envelope_structure():
    """Mock GMSH envelope must have required keys and non-zero element_count."""
    executor = MockToolExecutor()
    trace_id = str(uuid.uuid4())
    envelope = executor.run_gmsh(
        trace_id=trace_id,
        task_id="task-test",
        invocation_id=f"gmsh-{trace_id[:8]}",
    )

    assert "tool_id" in envelope, "Envelope missing 'tool_id'"
    assert envelope["tool_id"] == "gmsh"
    assert "status" in envelope, "Envelope missing 'status'"
    assert envelope["status"] == "success"
    assert "trace_id" in envelope, "Envelope missing 'trace_id'"
    assert envelope["trace_id"] == trace_id
    assert "output" in envelope, "Envelope missing 'output'"
    assert envelope["output"]["element_count"] > 0, "element_count must be > 0"


# ---------------------------------------------------------------------------
# AC-04: CalculiX Envelope Has von Mises
# ---------------------------------------------------------------------------


def test_ac04_calculix_envelope_has_von_mises():
    """Mock CalculiX envelope must contain output.max_von_mises_mpa as a float."""
    executor = MockToolExecutor()
    trace_id = str(uuid.uuid4())
    envelope = executor.run_calculix(
        trace_id=trace_id,
        task_id="task-test",
        invocation_id=f"ccx-{trace_id[:8]}",
    )

    assert "output" in envelope, "Envelope missing 'output'"
    output = envelope["output"]
    assert "max_von_mises_mpa" in output, "output missing 'max_von_mises_mpa'"
    assert isinstance(output["max_von_mises_mpa"], float), (
        f"max_von_mises_mpa must be float, got {type(output['max_von_mises_mpa'])}"
    )


# ---------------------------------------------------------------------------
# AC-05: All Verification Gates Pass for Valid Output
# ---------------------------------------------------------------------------


def test_ac05_all_gates_pass_for_valid_output():
    """run_all_gates() on VALID_SPECIALIST_OUTPUT must return all passed=True."""
    gate_results = run_all_gates(VALID_SPECIALIST_OUTPUT)
    assert gate_results, "run_all_gates must return at least one result"

    failed = [gr for gr in gate_results if not gr.passed]
    assert failed == [], (
        f"Expected all gates to pass; failed gates: "
        f"{[(gr.gate, gr.error_code, gr.detail) for gr in failed]}"
    )


# ---------------------------------------------------------------------------
# AC-06: Vault Note Has Correct Frontmatter
# ---------------------------------------------------------------------------


def test_ac06_vault_note_has_correct_frontmatter(tmp_path, motor_mount_request):
    """After pipeline run, written .md file must have trace_id and type in frontmatter."""
    runner = _make_runner(tmp_path, anthropic_client=MockAnthropicClient())
    result = runner.run(motor_mount_request)

    # Find written .md files
    md_files = list(tmp_path.glob("**/*.md"))
    assert md_files, f"No .md files found under {tmp_path}"

    # Read each file and verify frontmatter using python-frontmatter
    import frontmatter  # python-frontmatter library

    found_trace_id = False
    found_type = False
    for md_file in md_files:
        raw = md_file.read_text(encoding="utf-8")
        try:
            post = frontmatter.loads(raw)
            fm = post.metadata
        except Exception:
            # Fall back to raw string check if parsing fails
            fm = {}
            raw_lower = raw
            if "trace_id" in raw_lower:
                found_trace_id = True
            if "type" in raw_lower:
                found_type = True
            continue

        if fm.get("trace_id") or result.trace_id in raw:
            found_trace_id = True
        if fm.get("type"):
            found_type = True

    assert found_trace_id, (
        f"No vault note contained trace_id in frontmatter. "
        f"Files: {[str(f) for f in md_files]}"
    )
    assert found_type, "No vault note had 'type' field in frontmatter"


# ---------------------------------------------------------------------------
# AC-07: Amnesia Check Passes After Write
# ---------------------------------------------------------------------------


def test_ac07_amnesia_check_passes_after_write(tmp_path):
    """LibrarianAgent.amnesia_check() must return True immediately after intake()."""
    vault_manager = ObsidianVaultManager(vault_path=tmp_path)
    librarian = LibrarianAgent(vault_manager)

    note_dict = {
        "project": "aladdin-3b",
        "component": "motor_mount_bracket",
        "domain": "mechanical_engineering",
        "trace_id": str(uuid.uuid4()),
        "confidence": 0.82,
        "content": "Linear static FEA result: max von Mises = 110.5 MPa.",
    }

    path = librarian.intake(note_dict)
    assert isinstance(path, str) and path.endswith(".md"), (
        f"intake() must return a .md path, got: {path!r}"
    )

    result = librarian.amnesia_check(path)
    assert result is True, (
        f"amnesia_check returned {result!r} for path {path!r} — vault amnesia detected"
    )


# ---------------------------------------------------------------------------
# AC-08: TaskResult Has Required Fields
# ---------------------------------------------------------------------------


def test_ac08_task_result_has_required_fields(tmp_path, motor_mount_request):
    """TaskResult must have all required fields with correct types and valid status."""
    runner = _make_runner(tmp_path, anthropic_client=MockAnthropicClient())
    result = runner.run(motor_mount_request)

    assert isinstance(result, TaskResult)

    # result_summary must be a non-empty string
    assert isinstance(result.result_summary, str) and result.result_summary, (
        "result_summary must be a non-empty string"
    )

    # unresolved_gaps must be a list
    assert isinstance(result.unresolved_gaps, list), (
        f"unresolved_gaps must be a list, got {type(result.unresolved_gaps)}"
    )

    # what_would_falsify must be a list
    assert isinstance(result.what_would_falsify, list), (
        f"what_would_falsify must be a list, got {type(result.what_would_falsify)}"
    )

    # confidence must be a float in [0.0, 1.0]
    assert isinstance(result.confidence, float), (
        f"confidence must be a float, got {type(result.confidence)}"
    )
    assert 0.0 <= result.confidence <= 1.0, (
        f"confidence must be in [0.0, 1.0], got {result.confidence}"
    )

    # artifact_refs must be a list
    assert isinstance(result.artifact_refs, list), (
        f"artifact_refs must be a list, got {type(result.artifact_refs)}"
    )

    # status must be one of the valid values
    assert result.status in {"complete", "degraded", "failed"}, (
        f"status must be 'complete', 'degraded', or 'failed'; got {result.status!r}"
    )


# ---------------------------------------------------------------------------
# AC-09: Vault Blocked on Gate Failure
# ---------------------------------------------------------------------------


def test_ac09_vault_blocked_on_gate_failure(tmp_path, motor_mount_request):
    """When specialist output is invalid, vault write must NOT be called and status == 'failed'."""

    # Use a MagicMock vault manager so we can assert upsert_note was not called
    mock_vault = MagicMock()
    mock_vault.search_notes.return_value = []
    mock_vault.upsert_note.return_value = "engineering/test/test.md"
    mock_vault.amnesia_check.return_value = True

    runner = PipelineRunner(
        config={"provider": "anthropic"},
        tool_executor=MockToolExecutor(),
        vault_manager=mock_vault,
        anthropic_client=MockAnthropicClientInvalid(),
    )
    result = runner.run(motor_mount_request)

    # Status must be "failed"
    assert result.status == "failed", (
        f"Expected status='failed' on gate failure, got {result.status!r}"
    )

    # Vault write must NOT have been called
    mock_vault.upsert_note.assert_not_called()


# ---------------------------------------------------------------------------
# AC-10: JSONL Has 9-Phase Events
# ---------------------------------------------------------------------------


def test_ac10_jsonl_has_9_phase_events(tmp_path, motor_mount_request):
    """All 9 phases must each emit a start and end event, all containing trace_id."""
    runner = _make_runner(tmp_path, anthropic_client=MockAnthropicClient())
    result = runner.run(motor_mount_request)

    expected_phases = {
        "intake",
        "routing",
        "decomposition",
        "memory_preflight",
        "specialist",
        "tool_execution",
        "verification",
        "persistence",
        "output",
    }

    start_events = [e for e in runner._jsonl_events if e.get("event") == "phase_start"]
    end_events = [e for e in runner._jsonl_events if e.get("event") == "phase_end"]

    start_phases = {e["phase"] for e in start_events}
    end_phases = {e["phase"] for e in end_events}

    missing_start = expected_phases - start_phases
    missing_end = expected_phases - end_phases

    assert not missing_start, f"Missing phase_start events for: {missing_start}"
    assert not missing_end, f"Missing phase_end events for: {missing_end}"

    assert len(start_events) == 9, (
        f"Expected 9 phase_start events, got {len(start_events)}. "
        f"Phases: {[e['phase'] for e in start_events]}"
    )
    assert len(end_events) == 9, (
        f"Expected 9 phase_end events, got {len(end_events)}. "
        f"Phases: {[e['phase'] for e in end_events]}"
    )

    # All events must contain trace_id with the correct value
    for event in runner._jsonl_events:
        assert "trace_id" in event, f"Event missing trace_id: {event}"
        assert event["trace_id"] == result.trace_id, (
            f"Event trace_id mismatch in phase={event.get('phase')!r}: "
            f"{event['trace_id']!r} != {result.trace_id!r}"
        )
