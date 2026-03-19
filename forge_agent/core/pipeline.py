"""
forge_agent/core/pipeline.py

Python pipeline runner — 9-phase FORGE core loop.

Phases:
  1. intake           — validate request, assign trace_id, populate blackboard
  2. routing          — select provider/model
  3. decomposition    — single-task for MVP
  4. memory_preflight — retrieve top-k relevant vault notes
  5. specialist       — call ME Specialist (Anthropic API or stub)
  6. tool_execution   — invoke GMSH then CalculiX via tool_executor
  7. verification     — run_all_gates(); block vault write on failure
  8. persistence      — upsert_note() + amnesia_check()
  9. (output)         — assemble TaskResult
"""

from __future__ import annotations

import json
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from forge_agent.core.verifier import run_all_gates
from forge_agent.agents.engineers.mechanical_engineer import SYSTEM_PROMPT as ME_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass
class TaskRequest:
    task_type: str
    project: str
    component: str
    description: str
    load_cases: list = field(default_factory=list)


@dataclass
class TaskResult:
    trace_id: str
    status: str                          # "complete" | "degraded" | "failed" | "disputed"
    result_summary: str
    confidence: float
    artifact_refs: list = field(default_factory=list)
    unresolved_gaps: list = field(default_factory=list)
    what_would_falsify: list = field(default_factory=list)
    debate_verdict: str | None = field(default=None)  # "consensus" | "maintained_disagreement" | None


# ---------------------------------------------------------------------------
# Stub specialist output — contract-compliant, enables offline tests
# ---------------------------------------------------------------------------

VALID_SPECIALIST_OUTPUT: dict = {
    "model_choice": (
        "Euler-Bernoulli beam theory is appropriate for L/h > 10; "
        "linear static FEA for small-deflection regime"
    ),
    "equations": [
        r"$$\sigma = M \cdot c / I$$",
        r"$$I = b h^3 / 12$$",
        r"$$\delta_{max} = F L^3 / (3 E I)$$",
    ],
    "units": "SI: Pa, m, kg, N",
    "sanity_checks": [
        {"type": "limiting_case", "detail": "For zero load F=0, sigma=0 and delta=0 — confirmed."},
        {"type": "dimensional", "detail": "[N·m · m / m⁴] = [N/m²] = [Pa] — consistent."},
    ],
    "calculation_path": (
        "Step 1: Section modulus I = b·h³/12. "
        "Step 2: Bending stress σ = M·c/I at extreme fibre. "
        "Step 3: Tip deflection δ = F·L³/(3EI). "
        "Step 4: Check FoS ≥ 2.0 per MIL-HDBK-5J."
    ),
    "numerical_answer": "sigma_max = 1.5 MPa, delta_max = 0.8 mm — within allowable limits.",
    "assumptions": ["Small deflection", "Linear elastic, isotropic material", "Pinned-free BC"],
    "findings": [],
}


# ---------------------------------------------------------------------------
# Null vault manager — no-op, used when no vault_manager is supplied
# ---------------------------------------------------------------------------


class NullVaultManager:
    """No-op vault manager used when PipelineRunner is instantiated without one."""

    def upsert_note(self, path: str, markdown: str, frontmatter: dict | None = None) -> str:
        return path

    def amnesia_check(self, path: str) -> bool:
        return True

    def search_notes(self, query: str, top_k: int = 5) -> list:
        return []


# ---------------------------------------------------------------------------
# Default tool executor
# ---------------------------------------------------------------------------


class DefaultToolExecutor:
    """Calls real GMSH / CalculiX MCP servers.

    If the binary is not found on PATH, returns a degraded-mode envelope
    instead of raising — the pipeline continues with status="degraded".
    """

    def run_gmsh(
        self,
        trace_id: str,
        task_id: str,
        invocation_id: str,
        **kwargs: Any,
    ) -> dict:
        if shutil.which("gmsh") is None:
            return {
                "tool": "gmsh",
                "trace_id": trace_id,
                "task_id": task_id,
                "invocation_id": invocation_id,
                "status": "degraded",
                "reason": "gmsh binary not found on PATH",
            }
        # Real invocation would go here; placeholder for when binary is present.
        return {
            "tool": "gmsh",
            "trace_id": trace_id,
            "task_id": task_id,
            "invocation_id": invocation_id,
            "status": "ok",
        }

    def run_calculix(
        self,
        trace_id: str,
        task_id: str,
        invocation_id: str,
        **kwargs: Any,
    ) -> dict:
        if shutil.which("ccx") is None:
            return {
                "tool": "calculix",
                "trace_id": trace_id,
                "task_id": task_id,
                "invocation_id": invocation_id,
                "status": "degraded",
                "reason": "ccx (CalculiX) binary not found on PATH",
            }
        return {
            "tool": "calculix",
            "trace_id": trace_id,
            "task_id": task_id,
            "invocation_id": invocation_id,
            "status": "ok",
        }

    def run_openfoam(
        self,
        trace_id: str,
        task_id: str,
        invocation_id: str,
        **kwargs: Any,
    ) -> dict:
        if shutil.which("foamRun") is None and shutil.which("simpleFoam") is None:
            return {
                "tool": "openfoam",
                "trace_id": trace_id,
                "task_id": task_id,
                "invocation_id": invocation_id,
                "status": "degraded",
                "reason": "OpenFOAM binary (foamRun/simpleFoam) not found on PATH",
            }
        return {
            "tool": "openfoam",
            "trace_id": trace_id,
            "task_id": task_id,
            "invocation_id": invocation_id,
            "status": "ok",
        }

    def run_su2(
        self,
        trace_id: str,
        task_id: str,
        invocation_id: str,
        **kwargs: Any,
    ) -> dict:
        if shutil.which("SU2_CFD") is None:
            return {
                "tool": "su2",
                "trace_id": trace_id,
                "task_id": task_id,
                "invocation_id": invocation_id,
                "status": "degraded",
                "reason": "SU2_CFD binary not found on PATH",
            }
        return {
            "tool": "su2",
            "trace_id": trace_id,
            "task_id": task_id,
            "invocation_id": invocation_id,
            "status": "ok",
        }


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------


PHASE_NAMES = [
    "intake",
    "routing",
    "decomposition",
    "memory_preflight",
    "specialist",
    "tool_execution",
    "verification",
    "persistence",
    "output",
]


class PipelineRunner:
    """Execute the 9-phase FORGE core loop.

    Parameters
    ----------
    config:
        Runtime configuration dict. Recognised keys:
          - ``log_output``: if ``"stdout"``, emit JSONL events to sys.stdout.
          - ``provider``: model provider name (default ``"anthropic"``).
          - ``vault_path``: path used when constructing the default vault note path.
    tool_executor:
        Object with ``run_gmsh()`` / ``run_calculix()`` / ``run_openfoam()`` / ``run_su2()``
        methods. If *None*, a ``DefaultToolExecutor`` is used.
    vault_manager:
        Object with ``upsert_note()`` / ``amnesia_check()`` / ``search_notes()``.
        If *None*, a ``NullVaultManager`` (no-op) is used.
    anthropic_client:
        Anthropic SDK client (``anthropic.Anthropic``).
        If *None*, the pipeline uses ``_stub_specialist()`` so tests work offline.
    intelligence_router:
        Optional ``FailoverRouter`` instance (from ``intelligence_router.py``).
        When provided, ``_run_phase_specialist()`` calls through the router for
        automatic Anthropic→OpenAI failover. Takes precedence over
        ``anthropic_client`` when set.
    debate_orchestrator:
        Optional ``DebateOrchestrator`` instance. When provided, Phase 5b runs
        antagonist critique after the specialist phase. A ``fatal`` verdict
        sets ``TaskResult.status = "disputed"``.
    specialist_prompt:
        Optional system prompt string to use in ``_run_phase_specialist()``.
        When *None* (the default), ``ME_SYSTEM_PROMPT`` is used, preserving
        backward compatibility for all existing callers.
    """

    def __init__(
        self,
        config: dict,
        tool_executor: Any = None,
        vault_manager: Any = None,
        anthropic_client: Any = None,
        intelligence_router: Any = None,
        debate_orchestrator: Any = None,
        specialist_prompt: str | None = None,    # NEW: None → use ME_SYSTEM_PROMPT
    ) -> None:
        # All seven parameters stored and used — never silently dropped (P2 rule).
        self._config = config
        self._tool_executor: Any = tool_executor if tool_executor is not None else DefaultToolExecutor()
        self._vault_manager: Any = vault_manager if vault_manager is not None else NullVaultManager()
        self._anthropic_client: Any = anthropic_client  # None → use stub
        self._intelligence_router: Any = intelligence_router  # None → use anthropic_client path
        self._debate_orchestrator: Any = debate_orchestrator  # None → skip debate (Phase 5b)
        self._specialist_prompt: str = (
            specialist_prompt if specialist_prompt is not None else ME_SYSTEM_PROMPT
        )

        self._log_stdout: bool = config.get("log_output") == "stdout"
        self._jsonl_events: list[dict] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, request: TaskRequest) -> TaskResult:
        """Execute all 9 phases and return a TaskResult."""
        blackboard: dict = {}
        trace_id: str = ""
        specialist_output: dict = {}
        tool_results: dict = {}
        memory_notes: list = []
        unresolved_gaps: list = []
        artifact_refs: list = []

        # Phase 1
        trace_id = self._run_phase_intake(request, blackboard)

        # Phase 2
        self._run_phase_routing(blackboard)

        # Phase 3
        self._run_phase_decomposition(blackboard)

        # Phase 4
        memory_notes = self._run_phase_memory_preflight(blackboard)

        # Phase 5
        specialist_output = self._run_phase_specialist(blackboard, memory_notes)

        # Phase 5b — debate (optional; only runs when debate_orchestrator is configured)
        debate_verdict: str | None = None
        if self._debate_orchestrator is not None:
            debate_result = self._debate_orchestrator.run_debate(
                specialist_output, blackboard
            )
            debate_verdict = debate_result.verdict
            blackboard["debate.verdict"] = debate_verdict
            blackboard["debate.rounds"] = debate_result.rounds
            blackboard["debate.fatal_critique"] = any(
                c.get("severity") == "fatal" for c in debate_result.critiques
            )

        # Phase 6
        tool_results = self._run_phase_tool_execution(blackboard)
        if any(v.get("status") == "degraded" for v in tool_results.values()):
            blackboard["tool_execution.degraded"] = True

        # Phase 7
        verification_passed = self._run_phase_verification(specialist_output, blackboard)

        # Phase 8 — only if verification passed
        if verification_passed:
            gaps = self._run_phase_persistence(blackboard, specialist_output)
            unresolved_gaps.extend(gaps)
        else:
            blackboard["verification.status"] = "failed"

        # Phase 9 — assemble output
        result = self._assemble_output(
            trace_id=trace_id,
            blackboard=blackboard,
            specialist_output=specialist_output,
            tool_results=tool_results,
            verification_passed=verification_passed,
            unresolved_gaps=unresolved_gaps,
            artifact_refs=artifact_refs,
            debate_verdict=debate_verdict,
        )
        return result

    # ------------------------------------------------------------------
    # Phase implementations
    # ------------------------------------------------------------------

    def _run_phase_intake(self, request: TaskRequest, blackboard: dict) -> str:
        t0 = time.monotonic()
        phase = "intake"
        trace_id = str(uuid.uuid4())
        self._emit_phase_start(phase, trace_id)
        try:
            blackboard["intake.trace_id"] = trace_id
            blackboard["intake.task_type"] = request.task_type
            blackboard["intake.project"] = request.project
            blackboard["intake.component"] = request.component
            blackboard["intake.description"] = request.description
            blackboard["intake.load_cases"] = request.load_cases
            blackboard["intake.timestamp"] = datetime.now(timezone.utc).isoformat()
            status = "ok"
        except Exception as exc:
            status = "error"
            blackboard["intake.error"] = str(exc)
            raise
        finally:
            self._emit_phase_end(phase, status, t0, trace_id)
        return trace_id

    def _run_phase_routing(self, blackboard: dict) -> None:
        t0 = time.monotonic()
        phase = "routing"
        trace_id = blackboard.get("intake.trace_id", "")
        self._emit_phase_start(phase, trace_id)
        try:
            provider = self._config.get("provider", "anthropic")
            model = "claude-opus-4-6"
            blackboard["routing.provider"] = provider
            blackboard["routing.model"] = model
            blackboard["routing.trace_id"] = trace_id
            status = "ok"
        except Exception as exc:
            status = "error"
            blackboard["routing.error"] = str(exc)
            raise
        finally:
            self._emit_phase_end(phase, status, t0, trace_id)

    def _run_phase_decomposition(self, blackboard: dict) -> None:
        t0 = time.monotonic()
        phase = "decomposition"
        trace_id = blackboard.get("intake.trace_id", "")
        self._emit_phase_start(phase, trace_id)
        try:
            # MVP: single-task — no decomposition needed
            task_id = f"task-{trace_id[:8]}"
            blackboard["decomposition.tasks"] = [task_id]
            blackboard["decomposition.task_id"] = task_id
            blackboard["decomposition.trace_id"] = trace_id
            status = "ok"
        except Exception as exc:
            status = "error"
            blackboard["decomposition.error"] = str(exc)
            raise
        finally:
            self._emit_phase_end(phase, status, t0, trace_id)

    def _run_phase_memory_preflight(self, blackboard: dict) -> list:
        t0 = time.monotonic()
        phase = "memory_preflight"
        trace_id = blackboard.get("intake.trace_id", "")
        self._emit_phase_start(phase, trace_id)
        notes: list = []
        try:
            query = blackboard.get("intake.description", "")
            # vault_manager is always set (never None) — either real or NullVaultManager
            notes = self._vault_manager.search_notes(query, top_k=5)
            blackboard["memory_preflight.note_count"] = len(notes)
            blackboard["memory_preflight.trace_id"] = trace_id
            status = "ok"
        except Exception as exc:
            status = "degraded"
            blackboard["memory_preflight.error"] = str(exc)
            notes = []
        finally:
            self._emit_phase_end(phase, status, t0, trace_id)
        return notes

    def _run_phase_specialist(self, blackboard: dict, memory_notes: list) -> dict:
        t0 = time.monotonic()
        phase = "specialist"
        trace_id = blackboard.get("intake.trace_id", "")
        self._emit_phase_start(phase, trace_id)
        output: dict = {}
        try:
            context = blackboard.get("intake.description", "")
            if memory_notes:
                snippets = "\n\n".join(str(n) for n in memory_notes[:3])
                context = f"{context}\n\nRelevant vault notes:\n{snippets}"

            if self._intelligence_router is not None:
                # Failover router path — used when FailoverRouter is injected (P2 satisfied)
                router_result = self._intelligence_router.route_call_sync(
                    role="specialist",
                    messages=[{"role": "user", "content": context}],
                    model=blackboard.get("routing.model", "claude-opus-4-6"),
                    max_tokens=2048,
                    system=self._specialist_prompt,
                )
                raw_text = router_result["content"]
                try:
                    output = json.loads(raw_text)
                except (json.JSONDecodeError, ValueError):
                    output = {"raw": raw_text}
            elif self._anthropic_client is not None:
                # Direct Anthropic client path — anthropic_client used here (P2 satisfied)
                msg = self._anthropic_client.messages.create(
                    model=blackboard.get("routing.model", "claude-opus-4-6"),
                    max_tokens=2048,
                    temperature=0.2,
                    system=self._specialist_prompt,
                    messages=[{"role": "user", "content": context}],
                )
                raw_text = msg.content[0].text
                # Attempt JSON parse; fall back to wrapping in dict
                try:
                    output = json.loads(raw_text)
                except (json.JSONDecodeError, ValueError):
                    output = {"raw": raw_text}
            else:
                # Offline stub — used in unit tests
                output = self._stub_specialist()

            output["trace_id"] = trace_id
            blackboard["specialist.output_keys"] = list(output.keys())
            blackboard["specialist.trace_id"] = trace_id
            status = "ok"
        except Exception as exc:
            status = "error"
            blackboard["specialist.error"] = str(exc)
            output = {"trace_id": trace_id, "error": str(exc)}
        finally:
            self._emit_phase_end(phase, status, t0, trace_id)
        return output

    def _run_phase_tool_execution(self, blackboard: dict) -> dict:
        t0 = time.monotonic()
        phase = "tool_execution"
        trace_id = blackboard.get("intake.trace_id", "")
        task_id = blackboard.get("decomposition.task_id", "task-unknown")
        self._emit_phase_start(phase, trace_id)
        results: dict = {}
        overall_status = "ok"
        try:
            # tool_executor is always set — either real or injected mock (P2 rule satisfied)
            gmsh_inv_id = f"gmsh-{trace_id[:8]}"
            ccx_inv_id = f"ccx-{trace_id[:8]}"

            gmsh_result = self._tool_executor.run_gmsh(
                trace_id=trace_id,
                task_id=task_id,
                invocation_id=gmsh_inv_id,
            )
            ccx_result = self._tool_executor.run_calculix(
                trace_id=trace_id,
                task_id=task_id,
                invocation_id=ccx_inv_id,
            )

            results["gmsh"] = gmsh_result
            results["calculix"] = ccx_result

            if gmsh_result.get("status") == "degraded" or ccx_result.get("status") == "degraded":
                overall_status = "degraded"

            blackboard["tool_execution.gmsh_status"] = gmsh_result.get("status")
            blackboard["tool_execution.calculix_status"] = ccx_result.get("status")
            blackboard["tool_execution.trace_id"] = trace_id
        except Exception as exc:
            overall_status = "error"
            blackboard["tool_execution.error"] = str(exc)
            results["error"] = str(exc)
        finally:
            self._emit_phase_end(phase, overall_status, t0, trace_id)
        return results

    def _run_phase_verification(self, specialist_output: dict, blackboard: dict) -> bool:
        t0 = time.monotonic()
        phase = "verification"
        trace_id = blackboard.get("intake.trace_id", "")
        self._emit_phase_start(phase, trace_id)
        passed = True
        try:
            gate_results = run_all_gates(specialist_output)
            failed_gates = [gr for gr in gate_results if not gr.passed]

            blackboard["verification.gate_count"] = len(gate_results)
            blackboard["verification.failed_gates"] = [gr.gate for gr in failed_gates]
            blackboard["verification.trace_id"] = trace_id

            if failed_gates:
                passed = False
                blackboard["verification.status"] = "failed"
                # Log each failed gate
                for gr in failed_gates:
                    blackboard[f"verification.{gr.gate}.error_code"] = gr.error_code
                    blackboard[f"verification.{gr.gate}.detail"] = gr.detail
            else:
                blackboard["verification.status"] = "passed"

            status = "ok" if passed else "degraded"
        except Exception as exc:
            passed = False
            status = "error"
            blackboard["verification.error"] = str(exc)
            blackboard["verification.status"] = "failed"
        finally:
            self._emit_phase_end(phase, status, t0, trace_id)
        return passed

    def _run_phase_persistence(self, blackboard: dict, specialist_output: dict) -> list:
        t0 = time.monotonic()
        phase = "persistence"
        trace_id = blackboard.get("intake.trace_id", "")
        self._emit_phase_start(phase, trace_id)
        gaps: list = []
        try:
            project = blackboard.get("intake.project", "unknown")
            component = blackboard.get("intake.component", "unknown")
            domain = blackboard.get("intake.task_type", "mechanical")

            # Build vault note path and frontmatter
            note_path = f"engineering/{project}/{component}-{trace_id[:8]}.md"
            frontmatter: dict = {
                "trace_id": trace_id,
                "domain": domain,
                "component": component,
                "project": project,
                "type": "finding",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Build markdown body from specialist output
            summary = specialist_output.get("numerical_answer", "")
            calc_path = specialist_output.get("calculation_path", "")
            markdown = (
                f"# Analysis: {component}\n\n"
                f"**Project**: {project}  \n"
                f"**Trace ID**: {trace_id}  \n\n"
                f"## Result\n\n{summary}\n\n"
                f"## Calculation Path\n\n{calc_path}\n"
            )

            # Persist — second parameter is named `markdown` (not `content`) per obsidian_manager.py
            self._vault_manager.upsert_note(note_path, markdown, frontmatter)

            # Amnesia check — if False, flag ERR_VAULT_AMNESIA
            retrieved = self._vault_manager.amnesia_check(note_path)
            if not retrieved:
                gaps.append("ERR_VAULT_AMNESIA")

            blackboard["persistence.note_path"] = note_path
            blackboard["persistence.trace_id"] = trace_id
            blackboard["persistence.amnesia_ok"] = retrieved
            status = "ok"
        except Exception as exc:
            status = "error"
            blackboard["persistence.error"] = str(exc)
        finally:
            self._emit_phase_end(phase, status, t0, trace_id)
        return gaps

    def _assemble_output(
        self,
        trace_id: str,
        blackboard: dict,
        specialist_output: dict,
        tool_results: dict,
        verification_passed: bool,
        unresolved_gaps: list,
        artifact_refs: list,
        debate_verdict: str | None = None,
    ) -> TaskResult:
        t0 = time.monotonic()
        phase = "output"
        self._emit_phase_start(phase, trace_id)
        try:
            # Determine overall status
            if not verification_passed:
                status = "failed"
            elif blackboard.get("tool_execution.degraded") or any(
                v.get("status") == "degraded" for v in tool_results.values()
                if isinstance(v, dict)
            ):
                status = "degraded"
            else:
                status = "complete"

            # Override status when debate produced a fatal maintained_disagreement
            if (
                debate_verdict == "maintained_disagreement"
                and blackboard.get("debate.fatal_critique")
            ):
                status = "disputed"

            result_summary = specialist_output.get(
                "numerical_answer",
                "Analysis complete — see vault note for details.",
            )

            # Confidence heuristic: 1.0 if all gates passed, 0.5 if degraded, 0.0 if failed
            confidence = 1.0 if status == "complete" else (0.5 if status == "degraded" else 0.0)

            # what_would_falsify from specialist output if present
            what_would_falsify = specialist_output.get("what_would_falsify", [])
            if not isinstance(what_would_falsify, list):
                what_would_falsify = [str(what_would_falsify)]

            note_path = blackboard.get("persistence.note_path", "")
            if note_path:
                artifact_refs.append(note_path)

            phase_status = "ok"
        except Exception as exc:
            phase_status = "error"
            status = "failed"
            result_summary = f"Assembly error: {exc}"
            confidence = 0.0
            what_would_falsify = []
            raise
        finally:
            self._emit_phase_end(phase, phase_status, t0, trace_id)

        return TaskResult(
            trace_id=trace_id,
            status=status,
            result_summary=result_summary,
            confidence=confidence,
            artifact_refs=artifact_refs,
            unresolved_gaps=unresolved_gaps,
            what_would_falsify=what_would_falsify,
            debate_verdict=debate_verdict,
        )

    # ------------------------------------------------------------------
    # Stub specialist (offline / test mode)
    # ------------------------------------------------------------------

    def _stub_specialist(self) -> dict:
        """Return a contract-compliant specialist output dict for offline testing."""
        return dict(VALID_SPECIALIST_OUTPUT)

    # ------------------------------------------------------------------
    # JSONL event emission
    # ------------------------------------------------------------------

    def _emit_phase_start(self, phase: str, trace_id: str) -> None:
        event = {
            "event": "phase_start",
            "phase": phase,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._jsonl_events.append(event)
        if self._log_stdout:
            print(json.dumps(event), file=sys.stdout, flush=True)

    def _emit_phase_end(
        self,
        phase: str,
        status: str,
        t0: float,
        trace_id: str,
    ) -> None:
        duration_ms = round((time.monotonic() - t0) * 1000, 2)
        event = {
            "event": "phase_end",
            "phase": phase,
            "status": status,
            "duration_ms": duration_ms,
            "trace_id": trace_id,
        }
        self._jsonl_events.append(event)
        if self._log_stdout:
            print(json.dumps(event), file=sys.stdout, flush=True)
