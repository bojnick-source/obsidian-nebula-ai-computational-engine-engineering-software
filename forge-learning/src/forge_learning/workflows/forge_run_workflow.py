"""Temporal durable workflow for a FORGE run.

Uses Temporal Python SDK:
  @workflow.defn  → ForgeRunWorkflow
  @activity.defn  → individual pipeline activities

Human-in-the-loop pause gates:
  - confidence < 0.7 after specialist phase
  - contradiction detected after antagonist phase
  - Tier 1/2 constitution violation
  - all providers down > 1h
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import activity, workflow
from temporalio.common import RetryPolicy


# ─────────────────────────────────────────────────────────────────────────────
# Activity definitions
# ─────────────────────────────────────────────────────────────────────────────

@activity.defn
async def run_intake(task_input: dict[str, Any]) -> dict[str, Any]:
    """Parse and validate incoming task request."""
    return {"status": "ok", "task": task_input}


@activity.defn
async def run_memory_preflight(task_context: dict[str, Any]) -> dict[str, Any]:
    """Query Supermemory for relevant prior episodes before specialist dispatch."""
    return {"relevant_episodes": [], "gaps_identified": []}


@activity.defn
async def run_specialist_phase(task_context: dict[str, Any]) -> dict[str, Any]:
    """Dispatch ME (or domain) specialist agent and collect output."""
    return {
        "findings": [],
        "assumptions": [],
        "confidence": 0.0,
        "what_would_falsify": "",
        "agent_id": "me_specialist",
    }


@activity.defn
async def run_antagonist_phase(specialist_output: dict[str, Any]) -> dict[str, Any]:
    """Dispatch antagonist agent and run adversarial debate."""
    return {
        "debate_outcome": "consensus",
        "critiques": [],
        "final_confidence": specialist_output.get("confidence", 0.0),
    }


@activity.defn
async def run_tool_execution(task_context: dict[str, Any]) -> dict[str, Any]:
    """Execute GMSH → CalculiX (or other tools) via MCP wrappers."""
    return {"tool_results": {}, "success": True}


@activity.defn
async def run_verification(
    specialist_output: dict[str, Any],
    tool_results: dict[str, Any],
) -> dict[str, Any]:
    """Run all verification gates (contract, unit, dimensional, provenance, constitution)."""
    return {"gates_passed": [], "gates_failed": [], "all_passed": True}


@activity.defn
async def run_vault_persistence(
    specialist_output: dict[str, Any],
    verification_result: dict[str, Any],
    run_id: str,
    trace_id: str,
) -> dict[str, Any]:
    """Write findings to Obsidian vault and Supermemory."""
    return {"notes_written": [], "vault_status": "ok"}


@activity.defn
async def capture_episode(
    run_id: str,
    trace_id: str,
    run_summary: dict[str, Any],
) -> dict[str, Any]:
    """Post-run: evaluate and store episode in episodic memory."""
    return {"episode_stored": True, "quality_score": 0.0}


# ─────────────────────────────────────────────────────────────────────────────
# Workflow definition
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ForgeRunInput:
    run_id: str
    trace_id: str
    project: str
    task_description: str
    task_input: dict[str, Any]


@workflow.defn
class ForgeRunWorkflow:
    """Durable FORGE run workflow with human-in-the-loop gates.

    Checkpointed at each phase — survives worker restarts.
    """

    _ACTIVITY_RETRY = RetryPolicy(
        initial_interval=timedelta(seconds=2),
        maximum_interval=timedelta(minutes=5),
        maximum_attempts=3,
    )

    @workflow.run
    async def run(self, inp: ForgeRunInput) -> dict[str, Any]:
        ctx = {"run_id": inp.run_id, "trace_id": inp.trace_id, "task": inp.task_input}

        # Phase 1: Intake
        await workflow.execute_activity(
            run_intake,
            args=[inp.task_input],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=self._ACTIVITY_RETRY,
        )

        # Phase 2: Memory preflight
        memory_result = await workflow.execute_activity(
            run_memory_preflight,
            args=[ctx],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=self._ACTIVITY_RETRY,
        )
        ctx["relevant_episodes"] = memory_result.get("relevant_episodes", [])

        # Phase 3: Specialist
        specialist_output = await workflow.execute_activity(
            run_specialist_phase,
            args=[ctx],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=self._ACTIVITY_RETRY,
        )

        # Human-in-the-loop gate: low confidence
        if specialist_output.get("confidence", 1.0) < 0.7:
            await workflow.wait_condition(
                lambda: self._human_approved,
                timeout=timedelta(hours=24),
            )

        # Phase 4: Antagonist / debate
        antagonist_output = await workflow.execute_activity(
            run_antagonist_phase,
            args=[specialist_output],
            start_to_close_timeout=timedelta(minutes=20),
            retry_policy=self._ACTIVITY_RETRY,
        )

        # Human-in-the-loop gate: contradiction detected
        if antagonist_output.get("debate_outcome") == "maintained_disagreement":
            await workflow.wait_condition(
                lambda: self._human_approved,
                timeout=timedelta(hours=24),
            )

        # Phase 5: Tool execution
        tool_results = await workflow.execute_activity(
            run_tool_execution,
            args=[ctx],
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=self._ACTIVITY_RETRY,
        )

        # Phase 6: Verification
        verification = await workflow.execute_activity(
            run_verification,
            args=[specialist_output, tool_results],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=self._ACTIVITY_RETRY,
        )

        # Human-in-the-loop gate: Tier 1/2 constitution violation
        if not verification.get("all_passed", True):
            failed = verification.get("gates_failed", [])
            tier_critical = [g for g in failed if g.get("tier", 3) <= 2]
            if tier_critical:
                await workflow.wait_condition(
                    lambda: self._human_approved,
                    timeout=timedelta(hours=24),
                )

        # Phase 7: Vault persistence
        vault_result = await workflow.execute_activity(
            run_vault_persistence,
            args=[specialist_output, verification, inp.run_id, inp.trace_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=self._ACTIVITY_RETRY,
        )

        # Phase 8: Episode capture (learning loop)
        run_summary = {
            "specialist_output": specialist_output,
            "tool_results": tool_results,
            "verification": verification,
            "vault_result": vault_result,
        }
        episode_result = await workflow.execute_activity(
            capture_episode,
            args=[inp.run_id, inp.trace_id, run_summary],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=self._ACTIVITY_RETRY,
        )

        return {
            "run_id": inp.run_id,
            "trace_id": inp.trace_id,
            "success": verification.get("all_passed", False),
            "specialist_output": specialist_output,
            "verification": verification,
            "episode_stored": episode_result.get("episode_stored", False),
        }

    # ------------------------------------------------------------------
    # Human-in-the-loop signal handler
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        self._human_approved = False

    @workflow.signal
    def approve(self) -> None:
        """Signal to resume a paused workflow."""
        self._human_approved = True

    @workflow.signal
    def reject(self) -> None:
        """Signal to abort a paused workflow."""
        raise RuntimeError("Run rejected by human reviewer")


# ─────────────────────────────────────────────────────────────────────────────
# Scheduled workflows
# ─────────────────────────────────────────────────────────────────────────────

@workflow.defn
class DailyKnowledgeDiscoveryWorkflow:
    """Scheduled daily: scan arXiv, ingest new knowledge units."""

    @workflow.run
    async def run(self, _: None = None) -> dict[str, Any]:
        # Placeholder — real implementation calls knowledge_discovery activities
        return {"status": "ok", "units_ingested": 0}


@workflow.defn
class NightlyConsolidationWorkflow:
    """Scheduled nightly: FSRS decay, consolidate episodes, prune stale notes."""

    @workflow.run
    async def run(self, _: None = None) -> dict[str, Any]:
        return {"status": "ok", "notes_pruned": 0, "episodes_consolidated": 0}
