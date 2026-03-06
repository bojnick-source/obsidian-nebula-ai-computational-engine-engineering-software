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
