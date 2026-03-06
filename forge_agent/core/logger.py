"""
AgentLogger — structured JSONL logging for every tool call, model call,
token count, and latency measurement inside the FORGE agent loop.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ records


@dataclass
class ToolCallRecord:
    event: str = "tool_call"
    ts: float = field(default_factory=time.time)
    run_id: str = ""
    iteration: int = 0
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    result_summary: str = ""      # first 200 chars of result
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class ModelCallRecord:
    event: str = "model_call"
    ts: float = field(default_factory=time.time)
    run_id: str = ""
    iteration: int = 0
    agent_role: str = ""
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    stop_reason: str = ""
    error: str | None = None


@dataclass
class PhaseRecord:
    event: str = "phase"
    ts: float = field(default_factory=time.time)
    run_id: str = ""
    phase: str = ""
    status: str = ""          # started | completed | failed
    details: dict = field(default_factory=dict)


@dataclass
class BudgetRecord:
    event: str = "budget"
    ts: float = field(default_factory=time.time)
    run_id: str = ""
    iteration: int = 0
    estimated_tokens: int = 0
    budget: int = 0
    action: str = ""          # none | compress | strip_skills | drop_tools | exhausted


# ------------------------------------------------------------------ logger


class AgentLogger:
    """Writes structured JSONL to a log file; also keeps in-memory summary stats."""

    def __init__(self, log_path: str | Path, run_id: str = "") -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self._fh = self.log_path.open("a", encoding="utf-8")

        # summary stats
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_tool_calls: int = 0
        self.total_model_calls: int = 0

    # ---------------------------------------------------------------- public

    def log_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
        result: Any,
        latency_ms: float,
        iteration: int = 0,
        error: str | None = None,
    ) -> None:
        result_summary = _summarise(result)
        rec = ToolCallRecord(
            run_id=self.run_id,
            iteration=iteration,
            tool_name=tool_name,
            tool_args=tool_args,
            result_summary=result_summary,
            latency_ms=latency_ms,
            error=error,
        )
        self._write(rec)
        self.total_tool_calls += 1

    def log_model_call(
        self,
        agent_role: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        stop_reason: str = "",
        iteration: int = 0,
        error: str | None = None,
    ) -> None:
        rec = ModelCallRecord(
            run_id=self.run_id,
            iteration=iteration,
            agent_role=agent_role,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            stop_reason=stop_reason,
            error=error,
        )
        self._write(rec)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_model_calls += 1

    def log_phase(self, phase: str, status: str, details: dict | None = None) -> None:
        rec = PhaseRecord(
            run_id=self.run_id,
            phase=phase,
            status=status,
            details=details or {},
        )
        self._write(rec)

    def log_budget(self, iteration: int, estimated_tokens: int, budget: int, action: str) -> None:
        rec = BudgetRecord(
            run_id=self.run_id,
            iteration=iteration,
            estimated_tokens=estimated_tokens,
            budget=budget,
            action=action,
        )
        self._write(rec)

    @contextmanager
    def time_tool_call(self, tool_name: str, tool_args: dict, iteration: int = 0):
        """Context manager that times a tool call and logs the result."""
        t0 = time.perf_counter()
        result = None
        error = None
        try:
            yield lambda r: setattr(self, "_ctx_result", r)
            result = getattr(self, "_ctx_result", None)
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            self.log_tool_call(tool_name, tool_args, result, latency_ms, iteration, error)

    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_tool_calls": self.total_tool_calls,
            "total_model_calls": self.total_model_calls,
        }

    def close(self) -> None:
        self._fh.flush()
        self._fh.close()

    def __enter__(self) -> "AgentLogger":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ---------------------------------------------------------------- private

    def _write(self, record) -> None:
        line = json.dumps(asdict(record), default=str)
        self._fh.write(line + "\n")
        self._fh.flush()


# ------------------------------------------------------------------ helpers


def _summarise(result: Any) -> str:
    """First 200 chars of string representation."""
    try:
        text = json.dumps(result, default=str) if not isinstance(result, str) else result
    except Exception:
        text = repr(result)
    return text[:200]
