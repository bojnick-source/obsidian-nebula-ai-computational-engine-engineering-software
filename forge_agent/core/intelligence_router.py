"""
IntelligenceRouter — pre-task dispatcher for the FORGE intelligence pipeline.

Decision tree (in order, non-exclusive):
  1. YouTube URL detected    → Gemini 2.5 Pro (video_analysis pre-task)
  2. Current-info trigger    → Perplexity Sonar Pro (current_intelligence pre-task)
  3. Hard math / proof       → OpenAI o3 (math_compute pre-task)
  4. Always                  → Claude Opus (orchestration — always last)

Returns a list of PreTask dicts that UnifiedAgent executes before the main loop.
Results are injected into the system prompt as context blocks.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from typing import Any


# ------------------------------------------------------------------ data types


@dataclass
class PreTask:
    provider: str
    task_type: str          # video_analysis | current_intelligence | math_compute | orchestration
    query: str = ""
    urls: list[str] = field(default_factory=list)
    model: str = ""
    domain_filter: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass
class PreTaskResult:
    task_type: str
    provider: str
    content: str            # formatted context block
    citations: list[str] = field(default_factory=list)
    error: str | None = None


# ------------------------------------------------------------------ trigger patterns

_CURRENT_INFO_TRIGGERS = frozenset({
    "current", "latest", "recent", "today", "now", "price",
    "availability", "new", "updated", "status", "spec sheet",
    "datasheet", "lead time", "stock", "release", "announced",
    "what is the", "has", "changed", "2024", "2025", "2026",
})

_MATH_TRIGGERS = frozenset({
    "derive", "proof", "prove", "optimize", "minimise", "maximize",
    "stability analysis", "convergence", "eigenvalue", "lagrangian",
    "kkt", "pde", "ode", "numerical stability", "formal proof",
    "lagrange multiplier", "hessian", "gradient descent", "convex",
})

_DOMAIN_MAP: dict[str, list[str]] = {
    "darpa":      ["darpa.mil"],
    "nasa":       ["nasa.gov"],
    "arxiv":      ["arxiv.org"],
    "patent":     ["patents.google.com", "patents.justia.com"],
    "faa":        ["faa.gov"],
    "easa":       ["easa.europa.eu"],
    "regulation": ["federalregister.gov"],
    "material":   ["matweb.com", "azom.com"],
    "component":  ["mouser.com", "digikey.com", "mcmaster.com"],
    "standard":   ["standards.ieee.org", "asme.org"],
    "mil":        ["quicksearch.dla.mil"],
}

_YT_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?[^\s]*v=|youtu\.be/)[^\s]+"
)


# ------------------------------------------------------------------ router


class IntelligenceRouter:
    """
    Determines which AI ecosystems to invoke before the core agent loop.

    Usage:
        router = IntelligenceRouter()
        pre_tasks = router.plan(user_message)
        results = await router.execute(pre_tasks)
        context = router.format_context(results)
    """

    def plan(self, user_message: str) -> list[PreTask]:
        """Return ordered list of pre-tasks to execute."""
        pre_tasks: list[PreTask] = []
        text_lower = user_message.lower()

        # 1. YouTube video analysis
        yt_urls = _YT_PATTERN.findall(user_message)
        if yt_urls:
            pre_tasks.append(PreTask(
                provider="gemini",
                task_type="video_analysis",
                query=user_message,
                urls=yt_urls,
                model="gemini-2.5-pro",
            ))

        # 2. Current intelligence
        if self._requires_current_info(text_lower):
            domains = self._infer_domains(text_lower)
            pre_tasks.append(PreTask(
                provider="perplexity",
                task_type="current_intelligence",
                query=user_message,
                model="sonar-pro",
                domain_filter=domains,
            ))

        # 3. Hard math — pre-compute with o3
        if self._requires_formal_math(text_lower):
            pre_tasks.append(PreTask(
                provider="openai",
                task_type="math_compute",
                query=user_message,
                model="o3",
            ))

        return pre_tasks

    async def execute(self, pre_tasks: list[PreTask]) -> list[PreTaskResult]:
        """Execute all pre-tasks concurrently; return results."""
        if not pre_tasks:
            return []
        coros = [self._run_task(t) for t in pre_tasks]
        return await asyncio.gather(*coros)

    def format_context(self, results: list[PreTaskResult]) -> str:
        """Format all pre-task results into a single context injection block."""
        if not results:
            return ""
        blocks = []
        for r in results:
            if r.error:
                blocks.append(f"[{r.task_type} — ERROR: {r.error}]")
            else:
                blocks.append(r.content)
        return "\n\n---\n\n".join(blocks)

    # ---------------------------------------------------------------- private

    async def _run_task(self, task: PreTask) -> PreTaskResult:
        try:
            if task.task_type == "video_analysis":
                return await self._run_gemini(task)
            elif task.task_type == "current_intelligence":
                return await self._run_perplexity(task)
            elif task.task_type == "math_compute":
                return await self._run_openai_math(task)
            else:
                return PreTaskResult(
                    task_type=task.task_type,
                    provider=task.provider,
                    content="",
                    error=f"Unknown task type: {task.task_type}",
                )
        except Exception as exc:
            return PreTaskResult(
                task_type=task.task_type,
                provider=task.provider,
                content="",
                error=str(exc),
            )

    async def _run_gemini(self, task: PreTask) -> PreTaskResult:
        from forge_agent.core.gemini_client import GeminiClient
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        client = GeminiClient(api_key)
        if len(task.urls) == 1:
            result = await client.analyze_video_async(task.urls[0], task.query, task.model)
        else:
            result = await client.compare_videos_async(task.urls, task.query, task.model)
        return PreTaskResult(
            task_type=task.task_type,
            provider="gemini",
            content=result.to_context_block(),
        )

    async def _run_perplexity(self, task: PreTask) -> PreTaskResult:
        from forge_agent.core.perplexity_client import PerplexityClient
        api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        if not api_key:
            raise RuntimeError("PERPLEXITY_API_KEY not set")
        client = PerplexityClient(api_key)
        result = await client.search_async(
            task.query,
            model=task.model or "sonar-pro",
            domain_filter=task.domain_filter or None,
        )
        return PreTaskResult(
            task_type=task.task_type,
            provider="perplexity",
            content=result.to_context_block(),
            citations=result.citations,
        )

    async def _run_openai_math(self, task: PreTask) -> PreTaskResult:
        import openai
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=task.model or "o3",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a mathematical computation engine. "
                        "Solve the problem rigorously with full derivation. "
                        "Show all steps. State all assumptions."
                    ),
                },
                {"role": "user", "content": task.query},
            ],
            max_completion_tokens=4096,
        )
        content = response.choices[0].message.content or ""
        return PreTaskResult(
            task_type=task.task_type,
            provider="openai",
            content=f"[OpenAI {task.model} Math Pre-Computation]\n{content}",
        )

    # ---------------------------------------------------------------- detection

    @staticmethod
    def _requires_current_info(text: str) -> bool:
        return any(trigger in text for trigger in _CURRENT_INFO_TRIGGERS)

    @staticmethod
    def _requires_formal_math(text: str) -> bool:
        return any(trigger in text for trigger in _MATH_TRIGGERS)

    @staticmethod
    def _infer_domains(text: str) -> list[str]:
        domains: list[str] = []
        for key, urls in _DOMAIN_MAP.items():
            if key in text:
                domains.extend(urls)
        return domains[:20]


# ─────────────────────────────────────────────────────────────────────────────
# FailoverRouter — Anthropic→OpenAI failover with CircuitBreaker
# ─────────────────────────────────────────────────────────────────────────────


class FailoverRouter:
    """Route LLM calls with automatic failover using per-provider CircuitBreakers.

    Primary provider: Anthropic (claude-opus-4-6 / claude-sonnet-4-6)
    Secondary provider: OpenAI (o3 / gpt-4o)

    Failover triggers when:
      - Primary CircuitBreaker.allow_call() returns False (OPEN or HALF_OPEN + probe in flight)
      - Primary call raises any exception

    Parameters
    ----------
    config:
        Router config dict (same structure as forge.yaml router section).
        Used to resolve model IDs via ProviderClients.resolve_model().
    providers:
        ProviderClients singleton (or injectable mock for testing).
    primary_cb:
        CircuitBreaker instance for the primary (Anthropic) provider.
        If None, a default CircuitBreaker() is created.
    secondary_cb:
        CircuitBreaker instance for the secondary (OpenAI) provider.
        If None, a default CircuitBreaker() is created.
    """

    def __init__(
        self,
        config: dict,
        providers: Any,
        primary_cb: Any = None,
        secondary_cb: Any = None,
    ) -> None:
        from forge_agent.core.retry import CircuitBreaker
        self._config = config               # used in route_call via resolve_model
        self._providers = providers         # used in route_call for API calls
        self._primary_cb = primary_cb if primary_cb is not None else CircuitBreaker()
        self._secondary_cb = secondary_cb if secondary_cb is not None else CircuitBreaker()

    async def route_call(
        self,
        role: str,
        messages: list,
        **kwargs: Any,
    ) -> dict:
        """Attempt primary provider; failover to secondary on circuit open or error.

        Parameters
        ----------
        role:
            Agent role string passed to ProviderClients.resolve_model() for model selection.
        messages:
            List of message dicts in provider-agnostic format
            [{"role": "user", "content": "..."}].
        **kwargs:
            Extra kwargs forwarded to provider SDK (max_tokens, temperature, system, etc.)

        Returns
        -------
        dict with keys: provider, model, content (str), raw_response (provider object)

        Raises
        ------
        RuntimeError(ERR_PROVIDER_UNAVAILABLE ...) if both providers fail.
        """
        # --- Try primary (Anthropic) ---
        if self._primary_cb.allow_call():
            try:
                result = await self._call_anthropic(role, messages, **kwargs)
                self._primary_cb.record_success()
                return result
            except Exception as primary_exc:
                self._primary_cb.record_failure()
                # Fall through to secondary
                primary_err = str(primary_exc)
        else:
            primary_err = f"Primary circuit breaker {self._primary_cb.state} — skipped"

        # --- Failover to secondary (OpenAI) ---
        if self._secondary_cb.allow_call():
            try:
                result = await self._call_openai(role, messages, **kwargs)
                self._secondary_cb.record_success()
                return result
            except Exception as secondary_exc:
                self._secondary_cb.record_failure()
                raise RuntimeError(
                    f"ERR_PROVIDER_UNAVAILABLE: both providers failed. "
                    f"Primary: {primary_err}. Secondary: {secondary_exc}"
                ) from secondary_exc

        raise RuntimeError(
            f"ERR_PROVIDER_UNAVAILABLE: both circuit breakers open. "
            f"Primary: {primary_err}"
        )

    def route_call_sync(
        self,
        role: str,
        messages: list,
        **kwargs: Any,
    ) -> dict:
        """Synchronous wrapper around route_call() for use in sync pipelines.

        Must NOT be called from within a running event loop.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            raise RuntimeError(
                "route_call_sync() called from within a running event loop. "
                "Use 'await route_call()' instead."
            )
        return asyncio.run(self.route_call(role, messages, **kwargs))

    async def _call_anthropic(self, role: str, messages: list, **kwargs: Any) -> dict:
        model, _ = self._providers.resolve_model(self._config, role)
        response = await self._providers.anthropic.messages.create(
            model=model,
            messages=messages,
            **kwargs,
        )
        return {
            "provider": "anthropic",
            "model": model,
            "content": response.content[0].text,
            "raw_response": response,
        }

    async def _call_openai(self, role: str, messages: list, **kwargs: Any) -> dict:
        # Strip Anthropic-specific kwargs not accepted by OpenAI
        oai_kwargs = {k: v for k, v in kwargs.items() if k not in {"system"}}
        # OpenAI uses system message as first message element
        system = kwargs.get("system")
        oai_messages = list(messages)
        if system:
            oai_messages = [{"role": "system", "content": system}] + oai_messages

        # Resolve OpenAI model from config (fallback to gpt-4o)
        model, _ = self._providers.resolve_model(
            self._config, role + "_openai_fallback"
        )
        if not model or "claude" in model:
            model = "gpt-4o"

        response = await self._providers.openai.chat.completions.create(
            model=model,
            messages=oai_messages,
            **oai_kwargs,
        )
        return {
            "provider": "openai",
            "model": model,
            "content": response.choices[0].message.content,
            "raw_response": response,
        }
