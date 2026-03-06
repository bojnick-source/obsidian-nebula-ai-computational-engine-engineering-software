"""
AgentLoopGuard — iteration limit + divergence detection.

Divergence: same (tool_name, canonical_args) called ≥ 3 times → LoopDivergenceError.
Limit:       iteration count ≥ max_iterations → LoopLimitError.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field


class LoopLimitError(RuntimeError):
    """Raised when the agent exceeds max_iterations."""


class LoopDivergenceError(RuntimeError):
    """Raised when the agent calls the same tool with identical args ≥ divergence_threshold times."""


@dataclass
class AgentLoopGuard:
    max_iterations: int = 25
    divergence_threshold: int = 3

    _iteration: int = field(default=0, init=False, repr=False)
    # Maps canonical (tool_name, args_key) → call count
    _tool_call_counts: dict[tuple[str, str], int] = field(
        default_factory=lambda: defaultdict(int), init=False, repr=False
    )

    # ------------------------------------------------------------------ public

    def tick(self) -> int:
        """Increment iteration counter; raise LoopLimitError if limit reached."""
        self._iteration += 1
        if self._iteration > self.max_iterations:
            raise LoopLimitError(
                f"Agent exceeded max_iterations={self.max_iterations}. "
                "Aborting to prevent infinite loop."
            )
        return self._iteration

    def record_tool_call(self, tool_name: str, tool_args: dict) -> None:
        """Record a tool invocation; raise LoopDivergenceError on repeated identical calls."""
        key = (tool_name, _canonical_args(tool_args))
        self._tool_call_counts[key] += 1
        count = self._tool_call_counts[key]
        if count >= self.divergence_threshold:
            raise LoopDivergenceError(
                f"Divergence detected: tool '{tool_name}' called {count} times "
                f"with identical arguments: {tool_args!r}. "
                "Agent appears stuck — escalating."
            )

    def reset(self) -> None:
        """Reset state for a fresh run."""
        self._iteration = 0
        self._tool_call_counts.clear()

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def remaining(self) -> int:
        return max(0, self.max_iterations - self._iteration)


# ------------------------------------------------------------------ helpers


def _canonical_args(args: dict) -> str:
    """Stable JSON serialisation for use as a dict key."""
    try:
        return json.dumps(args, sort_keys=True, default=str)
    except Exception:
        return repr(args)
