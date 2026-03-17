"""
forge_agent/core/swanlab_tracker.py

SwanLab experiment tracker for FORGE AI agents.

Tracks every model call, tool call, budget event, and phase transition as a
SwanLab metric, giving a live dashboard of token spend, latency, and tool
error rates across agent runs.

Usage
-----
Pass a SwanlabTracker to AgentLogger at construction time:

    from forge_agent.core.swanlab_tracker import SwanlabTracker
    from forge_agent.core.logger import AgentLogger

    tracker = SwanlabTracker.create(
        project="forge-aladdin-3b",
        run_name="motor-mount-v7",
        config={"model": "claude-opus-4-6", "component": "motor_mount_bracket"},
    )
    logger = AgentLogger("logs/run.jsonl", run_id=run_id, tracker=tracker)
    ...
    tracker.finish()

If swanlab is not installed the tracker silently no-ops — no import error,
no behaviour change. Install: pip install swanlab

SwanLab dashboard: https://swanlab.cn  (or self-hosted)

Metrics emitted
---------------
Per model call (step = iteration):
    tokens/input          — input token count
    tokens/output         — output token count
    tokens/total          — total tokens this call
    tokens/cumulative     — cumulative total tokens for the run
    latency_ms/model      — model call wall time
    cost/model_calls      — cumulative model call count

Per tool call (step = iteration):
    latency_ms/tool_<name> — tool wall time
    errors/tool            — 1 if errored, else 0
    cost/tool_calls        — cumulative tool call count

Per budget event (step = iteration):
    budget/estimated_tokens  — estimated tokens for this context window
    budget/remaining         — remaining budget
    budget/utilisation_pct   — % of total budget consumed

Per phase event:
    phase/<name>           — 1 = started, 2 = completed, 3 = failed
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import swanlab as _swanlab
    _SWANLAB_AVAILABLE = True
except ImportError:
    _swanlab = None  # type: ignore[assignment]
    _SWANLAB_AVAILABLE = False


_PHASE_STATUS = {"started": 1, "completed": 2, "failed": 3}


class SwanlabTracker:
    """
    Thin wrapper around swanlab.init / swanlab.log for FORGE agent runs.

    All methods are safe to call regardless of whether swanlab is installed;
    they silently no-op when the package is absent.
    """

    def __init__(self, *, _run: Any = None, total_budget: int = 180_000) -> None:
        self._run = _run
        self._total_budget = total_budget
        self._cumulative_tokens: int = 0
        self._model_calls: int = 0
        self._tool_calls: int = 0

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        project: str = "forge",
        run_name: str | None = None,
        config: dict | None = None,
        total_budget: int = 180_000,
        logdir: str = "swanlab-logs",
    ) -> "SwanlabTracker":
        """
        Initialise a SwanLab run and return a tracker.

        Parameters
        ----------
        project   : SwanLab project name (groups related runs).
        run_name  : Display name for this specific run (e.g. "motor-mount-v7").
        config    : Dict of hyperparameters / metadata to record (model, agent, etc.).
        total_budget : Total token budget for this run (used for utilisation %).
        logdir    : Local directory for offline SwanLab logs.
        """
        if not _SWANLAB_AVAILABLE:
            logger.warning(
                "swanlab not installed — tracking disabled. "
                "Install with: pip install swanlab"
            )
            return cls(total_budget=total_budget)

        try:
            run = _swanlab.init(
                project=project,
                experiment_name=run_name,
                config=config or {},
                logdir=logdir,
            )
            return cls(_run=run, total_budget=total_budget)
        except Exception as exc:
            logger.warning("SwanLab init failed (%s) — tracking disabled", exc)
            return cls(total_budget=total_budget)

    # ── Public log methods (mirror AgentLogger signatures) ────────────────────

    def log_model_call(
        self,
        *,
        iteration: int,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        agent_role: str = "",
        model: str = "",
        provider: str = "",
        error: str | None = None,
    ) -> None:
        if self._run is None:
            return

        self._model_calls += 1
        total = input_tokens + output_tokens
        self._cumulative_tokens += total

        metrics: dict[str, float | int] = {
            "tokens/input":      input_tokens,
            "tokens/output":     output_tokens,
            "tokens/total":      total,
            "tokens/cumulative": self._cumulative_tokens,
            "latency_ms/model":  latency_ms,
            "cost/model_calls":  self._model_calls,
        }
        if error:
            metrics["errors/model"] = 1

        self._log(metrics, step=iteration)

    def log_tool_call(
        self,
        *,
        iteration: int,
        tool_name: str,
        latency_ms: float,
        error: str | None = None,
    ) -> None:
        if self._run is None:
            return

        self._tool_calls += 1
        # Sanitise tool name for metric key (no spaces / slashes)
        safe_name = tool_name.replace(" ", "_").replace("/", "_")[:40]
        metrics: dict[str, float | int] = {
            f"latency_ms/tool_{safe_name}": latency_ms,
            "errors/tool":                  1 if error else 0,
            "cost/tool_calls":              self._tool_calls,
        }
        self._log(metrics, step=iteration)

    def log_budget(
        self,
        *,
        iteration: int,
        estimated_tokens: int,
        budget: int,
        action: str,
    ) -> None:
        if self._run is None:
            return

        used = budget - max(0, budget - estimated_tokens)
        utilisation = (used / budget * 100.0) if budget > 0 else 0.0

        metrics: dict[str, float | int] = {
            "budget/estimated_tokens": estimated_tokens,
            "budget/remaining":        max(0, budget - estimated_tokens),
            "budget/utilisation_pct":  round(utilisation, 2),
            "budget/action_exhausted": 1 if action == "exhausted" else 0,
        }
        self._log(metrics, step=iteration)

    def log_phase(self, *, phase: str, status: str) -> None:
        """Log a phase transition. status: 'started' | 'completed' | 'failed'."""
        if self._run is None:
            return

        code = _PHASE_STATUS.get(status, 0)
        if code:
            self._log({f"phase/{phase}": code})

    def finish(self) -> None:
        """Finalise the SwanLab run. Call once at the end of the agent loop."""
        if self._run is None:
            return
        try:
            _swanlab.finish()
        except Exception as exc:
            logger.warning("SwanLab finish failed: %s", exc)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _log(self, metrics: dict[str, float | int], step: int | None = None) -> None:
        try:
            if step is not None:
                _swanlab.log(metrics, step=step)
            else:
                _swanlab.log(metrics)
        except Exception as exc:
            logger.debug("SwanLab log failed: %s", exc)
