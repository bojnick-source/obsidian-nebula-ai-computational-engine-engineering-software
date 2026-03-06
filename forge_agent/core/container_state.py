"""
ContainerState — lifecycle management for the FORGE agent process.

States:
  INIT → READY → RUNNING → DRAINING → STOPPED
                         ↘ ERROR    → STOPPED
"""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Callable, Awaitable


class LifecycleState(str, Enum):
    INIT = "init"
    READY = "ready"
    RUNNING = "running"
    DRAINING = "draining"
    STOPPED = "stopped"
    ERROR = "error"


class InvalidTransitionError(RuntimeError):
    pass


# Valid state transitions
_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.INIT: {LifecycleState.READY, LifecycleState.ERROR},
    LifecycleState.READY: {LifecycleState.RUNNING, LifecycleState.STOPPED, LifecycleState.ERROR},
    LifecycleState.RUNNING: {LifecycleState.DRAINING, LifecycleState.ERROR},
    LifecycleState.DRAINING: {LifecycleState.STOPPED, LifecycleState.ERROR},
    LifecycleState.ERROR: {LifecycleState.STOPPED},
    LifecycleState.STOPPED: set(),
}


class ContainerState:
    """Tracks agent container lifecycle; fires registered callbacks on transition."""

    def __init__(self) -> None:
        self._state = LifecycleState.INIT
        self._entered_at: dict[LifecycleState, float] = {LifecycleState.INIT: time.monotonic()}
        self._callbacks: list[Callable[[LifecycleState, LifecycleState], Awaitable[None] | None]] = []
        self._lock = asyncio.Lock()

    # ---------------------------------------------------------------- public

    @property
    def state(self) -> LifecycleState:
        return self._state

    def is_running(self) -> bool:
        return self._state == LifecycleState.RUNNING

    def is_accepting_work(self) -> bool:
        return self._state in (LifecycleState.READY, LifecycleState.RUNNING)

    def is_terminal(self) -> bool:
        return self._state == LifecycleState.STOPPED

    async def transition(self, new_state: LifecycleState) -> None:
        async with self._lock:
            allowed = _TRANSITIONS.get(self._state, set())
            if new_state not in allowed:
                raise InvalidTransitionError(
                    f"Cannot transition from {self._state.value!r} to {new_state.value!r}. "
                    f"Allowed: {[s.value for s in allowed]}"
                )
            old_state = self._state
            self._state = new_state
            self._entered_at[new_state] = time.monotonic()

        # Fire callbacks outside the lock
        for cb in self._callbacks:
            result = cb(old_state, new_state)
            if asyncio.iscoroutine(result):
                await result

    def on_transition(
        self,
        callback: Callable[[LifecycleState, LifecycleState], Awaitable[None] | None],
    ) -> None:
        """Register a callback invoked on every state transition."""
        self._callbacks.append(callback)

    def time_in_state(self, state: LifecycleState | None = None) -> float:
        """Seconds spent in *state* (defaults to current state)."""
        target = state or self._state
        entered = self._entered_at.get(target)
        if entered is None:
            return 0.0
        return time.monotonic() - entered

    def snapshot(self) -> dict:
        return {
            "state": self._state.value,
            "time_in_state_s": round(self.time_in_state(), 3),
        }

    # ---------------------------------------------------------------- convenience

    async def mark_ready(self) -> None:
        await self.transition(LifecycleState.READY)

    async def mark_running(self) -> None:
        await self.transition(LifecycleState.RUNNING)

    async def begin_drain(self) -> None:
        await self.transition(LifecycleState.DRAINING)

    async def mark_stopped(self) -> None:
        if self._state not in (LifecycleState.DRAINING, LifecycleState.ERROR):
            # Force path via DRAINING if we're still RUNNING
            if self._state == LifecycleState.RUNNING:
                await self.transition(LifecycleState.DRAINING)
        await self.transition(LifecycleState.STOPPED)

    async def mark_error(self, exc: BaseException | None = None) -> None:
        await self.transition(LifecycleState.ERROR)
