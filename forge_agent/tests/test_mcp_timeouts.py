"""Tests for MCP circuit breaker and timeout behaviour."""
import asyncio
import pytest

from forge_agent.core.retry import CircuitBreaker, CircuitState, RetryConfig, retry_api_call


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_failure_threshold_opens_circuit(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()  # back to 1 failure, not 3
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_open_circuit_raises(self):
        cb = CircuitBreaker(failure_threshold=1, reset_timeout_s=9999)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        async def dummy():
            return "ok"

        with pytest.raises(RuntimeError, match="Circuit breaker OPEN"):
            await cb.call(dummy)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, reset_timeout_s=0.05)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        await asyncio.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker(failure_threshold=1, reset_timeout_s=0.05)
        cb.record_failure()
        await asyncio.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

        async def succeed():
            return "ok"

        result = await cb.call(succeed)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED


class TestRetryApiCall:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self):
        calls = []

        async def fn(x):
            calls.append(x)
            return x * 2

        result = await retry_api_call(fn, 5, config=RetryConfig(max_attempts=4, base_delay_s=0.0))
        assert result == 10
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        attempts = []

        async def flaky():
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("transient")
            return "success"

        result = await retry_api_call(flaky, config=RetryConfig(max_attempts=4, base_delay_s=0.0, jitter_s=0.0))
        assert result == "success"
        assert len(attempts) == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        async def always_fail():
            raise ValueError("permanent")

        with pytest.raises(RuntimeError, match="permanent"):
            await retry_api_call(
                always_fail,
                config=RetryConfig(max_attempts=3, base_delay_s=0.0, jitter_s=0.0),
            )
