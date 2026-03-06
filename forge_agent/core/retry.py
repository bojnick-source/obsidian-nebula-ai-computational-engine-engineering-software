"""Retry / backoff / circuit breaker for API and MCP calls."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, TypeVar

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Exponential backoff with jitter, hard max attempts."""
    max_attempts: int = 4
    base_delay_s: float = 1.0     # 1 → 2 → 4 → 8
    jitter_s: float = 0.5
    retryable_status_codes: frozenset[int] = frozenset({429, 500, 502, 503, 504})

    def delay(self, attempt: int) -> float:
        """Return sleep duration for the N-th retry (0-indexed)."""
        backoff = self.base_delay_s * (2 ** attempt)
        jitter = random.uniform(-self.jitter_s, self.jitter_s)
        return max(0.0, backoff + jitter)


async def retry_api_call(
    fn: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> Any:
    """Run an async callable with retry / backoff.

    Raises the last exception if all attempts are exhausted.
    """
    cfg = config or RetryConfig()
    last_exc: Exception | None = None

    for attempt in range(cfg.max_attempts):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt == cfg.max_attempts - 1:
                break
            delay = cfg.delay(attempt)
            await asyncio.sleep(delay)

    raise RuntimeError(
        f"All {cfg.max_attempts} retry attempts exhausted"
    ) from last_exc


# ─────────────────────────────────────────────────────────────────────────────
# Circuit breaker
# ─────────────────────────────────────────────────────────────────────────────

class CircuitState(StrEnum):
    CLOSED = "closed"       # normal — calls pass through
    OPEN = "open"           # failing — calls rejected immediately
    HALF_OPEN = "half_open" # recovery — one probe call allowed


@dataclass
class CircuitBreaker:
    """Per-server circuit breaker.

    Opens after N consecutive failures; half-opens after reset_timeout_s;
    closes again on first successful call in half-open state.
    """
    failure_threshold: int = 3
    reset_timeout_s: float = 60.0

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.reset_timeout_s:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()

    def allow_call(self) -> bool:
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True  # allow probe
        return False  # OPEN — reject

    async def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if not self.allow_call():
            raise RuntimeError(
                f"Circuit breaker OPEN — server unavailable "
                f"(resets after {self.reset_timeout_s}s)"
            )
        try:
            result = await fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure()
            raise exc
