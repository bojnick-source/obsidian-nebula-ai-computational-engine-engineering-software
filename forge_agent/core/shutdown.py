"""
GracefulShutdown — drains pending vault writes before process exit.

Usage:
    shutdown = GracefulShutdown(drain_timeout_s=10.0)
    shutdown.install_signal_handlers()   # SIGINT + SIGTERM
    shutdown.register_drain_task(vault_manager.flush)

    # In main loop:
    if shutdown.requested:
        await shutdown.drain_and_stop(container_state)
"""

from __future__ import annotations

import asyncio
import signal
import time
from typing import Awaitable, Callable

from forge_agent.core.container_state import ContainerState


class GracefulShutdown:
    def __init__(self, drain_timeout_s: float = 10.0) -> None:
        self.drain_timeout_s = drain_timeout_s
        self._requested = False
        self._request_time: float | None = None
        self._drain_tasks: list[Callable[[], Awaitable[None]]] = []

    # ---------------------------------------------------------------- public

    @property
    def requested(self) -> bool:
        return self._requested

    def request(self) -> None:
        """Mark shutdown as requested (idempotent)."""
        if not self._requested:
            self._requested = True
            self._request_time = time.monotonic()

    def register_drain_task(self, fn: Callable[[], Awaitable[None]]) -> None:
        """Register an async coroutine function to run during drain phase."""
        self._drain_tasks.append(fn)

    def install_signal_handlers(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """Install SIGINT and SIGTERM handlers that trigger graceful shutdown."""
        _loop = loop or asyncio.get_event_loop()

        def _handler(sig_num: int, _frame) -> None:
            sig_name = signal.Signals(sig_num).name
            print(f"\n[forge_agent] Received {sig_name} — initiating graceful shutdown.")
            _loop.call_soon_threadsafe(self.request)

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    async def drain_and_stop(self, container: ContainerState) -> None:
        """
        1. Transition container → DRAINING
        2. Run all registered drain tasks concurrently (with timeout)
        3. Transition container → STOPPED
        """
        await container.begin_drain()
        print(f"[forge_agent] Draining {len(self._drain_tasks)} task(s) "
              f"(timeout={self.drain_timeout_s}s)…")

        if self._drain_tasks:
            coros = [task() for task in self._drain_tasks]
            try:
                await asyncio.wait_for(
                    asyncio.gather(*coros, return_exceptions=True),
                    timeout=self.drain_timeout_s,
                )
            except asyncio.TimeoutError:
                print(
                    f"[forge_agent] WARNING: drain tasks did not complete within "
                    f"{self.drain_timeout_s}s — forcing stop."
                )

        await container.mark_stopped()
        print("[forge_agent] Shutdown complete.")

    def time_since_request(self) -> float | None:
        if self._request_time is None:
            return None
        return time.monotonic() - self._request_time
