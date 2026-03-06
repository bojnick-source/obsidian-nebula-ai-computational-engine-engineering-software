"""
PerplexityClient — real-time grounded search with citations.

Uses the Perplexity REST API (OpenAI-compatible endpoint).
No temperature parameter — search-grounded, not purely generative.

Models (as of 2026-02):
  sonar       — fast, cheap, everyday queries
  sonar-pro   — complex queries, 2× citations, multi-step reasoning
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class SearchResult:
    answer: str
    citations: list[str] = field(default_factory=list)
    search_results: list[dict] = field(default_factory=list)

    def to_context_block(self) -> str:
        """Format as injected context for downstream agents."""
        lines = [f"[Perplexity Search Result]\n{self.answer}"]
        if self.citations:
            lines.append("\nSources:")
            for i, url in enumerate(self.citations, 1):
                lines.append(f"  [{i}] {url}")
        return "\n".join(lines)


class PerplexityClient:
    """Sync and async wrappers for Perplexity Sonar API."""

    BASE_URL = "https://api.perplexity.ai"
    DEFAULT_MODEL = "sonar-pro"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def search(
        self,
        query: str,
        model: str = DEFAULT_MODEL,
        domain_filter: list[str] | None = None,  # max 20 entries
    ) -> SearchResult:
        """Synchronous search — use in non-async contexts."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": query}],
        }
        if domain_filter:
            payload["search_domain_filter"] = domain_filter[:20]

        resp = requests.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self._headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        return SearchResult(
            answer=data["choices"][0]["message"]["content"],
            citations=data.get("citations", []),
            search_results=data.get("search_results", []),
        )

    async def search_async(
        self,
        query: str,
        model: str = DEFAULT_MODEL,
        domain_filter: list[str] | None = None,
    ) -> SearchResult:
        """Async wrapper — runs sync call in executor to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.search(query, model, domain_filter),
        )

    def search_with_domain_hints(
        self,
        query: str,
        context_keywords: list[str],
        model: str = DEFAULT_MODEL,
    ) -> SearchResult:
        """Auto-select domain filters from context keywords."""
        domains = _infer_domains(context_keywords)
        return self.search(query, model, domain_filter=domains or None)


# ------------------------------------------------------------------ helpers


_DOMAIN_MAP: dict[str, list[str]] = {
    "darpa":       ["darpa.mil"],
    "nasa":        ["nasa.gov"],
    "arxiv":       ["arxiv.org"],
    "patent":      ["patents.google.com", "patents.justia.com"],
    "faa":         ["faa.gov"],
    "easa":        ["easa.europa.eu"],
    "regulation":  ["federalregister.gov"],
    "material":    ["matweb.com", "azom.com"],
    "component":   ["mouser.com", "digikey.com", "mcmaster.com"],
    "standard":    ["standards.ieee.org", "asme.org"],
    "mil-spec":    ["quicksearch.dla.mil"],
}


def _infer_domains(keywords: list[str]) -> list[str]:
    domains: list[str] = []
    kw_lower = [k.lower() for k in keywords]
    for key, urls in _DOMAIN_MAP.items():
        if any(key in kw for kw in kw_lower):
            domains.extend(urls)
    return domains[:20]
