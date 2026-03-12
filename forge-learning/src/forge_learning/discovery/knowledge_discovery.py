"""Knowledge discovery agent — daily arXiv scan + weekly deep review.

Sources:
  Tier 1: Semantic Scholar (SPECTER2, 1 req/s free), arXiv RSS (no auth)
  Tier 2: OpenAlex (474M+ CC0), Materials Project API, OPTIMADE (10M+)
  Tier 3: Tavily, Scrapling (StealthyFetcher)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx


ARXIV_RSS_BASE = "https://rss.arxiv.org/rss/"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
OPENALEX_API = "https://api.openalex.org"

_RELEVANT_ARXIV_CATEGORIES = [
    "cs.CE",   # Computational Engineering
    "cs.NA",   # Numerical Analysis
    "cond-mat.mtrl-sci",  # Materials Science
    "physics.flu-dyn",    # Fluid Dynamics
    "physics.comp-ph",    # Computational Physics
]


@dataclass
class KnowledgeUnit:
    title: str
    abstract: str
    source: str
    url: str
    authors: list[str] = field(default_factory=list)
    published_date: str = ""
    relevance_score: float = 0.0
    domain_tags: list[str] = field(default_factory=list)
    contradicts_existing: bool = False
    contradiction_detail: str = ""


class KnowledgeDiscoveryAgent:
    """Discover and ingest new engineering knowledge from external sources."""

    def __init__(
        self,
        tavily_api_key: str | None = None,
        semantic_scholar_api_key: str | None = None,
    ) -> None:
        self._tavily_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
        self._ss_key = semantic_scholar_api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self._client = httpx.Client(timeout=30)

    def daily_arxiv_scan(
        self,
        categories: list[str] | None = None,
        max_per_category: int = 20,
    ) -> list[KnowledgeUnit]:
        """Fetch latest arXiv papers across relevant categories."""
        cats = categories or _RELEVANT_ARXIV_CATEGORIES
        units: list[KnowledgeUnit] = []
        for cat in cats:
            try:
                fetched = self._fetch_arxiv_rss(cat, max_per_category)
                units.extend(fetched)
                time.sleep(0.5)  # polite delay
            except Exception:
                pass
        return units

    def _fetch_arxiv_rss(self, category: str, limit: int) -> list[KnowledgeUnit]:
        url = f"{ARXIV_RSS_BASE}{category}"
        resp = self._client.get(url)
        resp.raise_for_status()
        return self._parse_arxiv_rss(resp.text, limit)

    def _parse_arxiv_rss(self, xml_text: str, limit: int) -> list[KnowledgeUnit]:
        import xml.etree.ElementTree as ET
        units: list[KnowledgeUnit] = []
        try:
            root = ET.fromstring(xml_text)
            items = root.findall(".//item")
            for item in items[:limit]:
                title_el = item.find("title")
                desc_el = item.find("description")
                link_el = item.find("link")
                units.append(KnowledgeUnit(
                    title=title_el.text.strip() if title_el is not None else "",
                    abstract=desc_el.text.strip() if desc_el is not None else "",
                    source="arxiv",
                    url=link_el.text.strip() if link_el is not None else "",
                    published_date=datetime.now(timezone.utc).date().isoformat(),
                ))
        except ET.ParseError:
            pass
        return units

    def semantic_scholar_search(
        self,
        query: str,
        limit: int = 10,
        fields: list[str] | None = None,
    ) -> list[KnowledgeUnit]:
        """Search Semantic Scholar (SPECTER2 embeddings, 1 req/s free tier)."""
        f = fields or ["title", "abstract", "authors", "year", "externalIds", "url"]
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "fields": ",".join(f),
        }
        headers = {}
        if self._ss_key:
            headers["x-api-key"] = self._ss_key

        try:
            resp = self._client.get(
                f"{SEMANTIC_SCHOLAR_API}/paper/search",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            units = []
            for paper in data.get("data", []):
                authors = [a.get("name", "") for a in paper.get("authors", [])]
                units.append(KnowledgeUnit(
                    title=paper.get("title", ""),
                    abstract=paper.get("abstract", ""),
                    source="semantic_scholar",
                    url=paper.get("url", ""),
                    authors=authors,
                    published_date=str(paper.get("year", "")),
                ))
            return units
        except Exception:
            return []

    def weekly_deep_review(
        self,
        domain_queries: list[str] | None = None,
    ) -> list[KnowledgeUnit]:
        """Deeper weekly review using Semantic Scholar + OpenAlex."""
        queries = domain_queries or [
            "topology optimization aerospace structures",
            "mesh convergence finite element analysis",
            "CFD turbulence model validation",
            "structural steel fatigue life prediction",
        ]
        all_units: list[KnowledgeUnit] = []
        for q in queries:
            units = self.semantic_scholar_search(q, limit=5)
            all_units.extend(units)
            time.sleep(1.1)  # 1 req/s rate limit
        return all_units

    def check_contradictions(
        self,
        new_unit: KnowledgeUnit,
        existing_facts: list[dict[str, Any]],
    ) -> KnowledgeUnit:
        """Flag if new_unit contradicts any existing vault fact."""
        for fact in existing_facts:
            # Simple keyword overlap check — production would use embeddings
            fact_text = (fact.get("title", "") + " " + fact.get("body", "")).lower()
            new_text = (new_unit.title + " " + new_unit.abstract).lower()
            shared_terms = set(fact_text.split()) & set(new_text.split()) - _STOP_WORDS
            if len(shared_terms) > 5:
                # Rough heuristic: significant topic overlap
                contradictory_phrases = ["contradicts", "disproves", "overturns", "challenges"]
                if any(p in new_text for p in contradictory_phrases):
                    new_unit.contradicts_existing = True
                    new_unit.contradiction_detail = f"Possible contradiction with: {fact.get('title', '')[:60]}"
        return new_unit

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "KnowledgeDiscoveryAgent":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


_STOP_WORDS = {
    "the", "a", "an", "in", "of", "for", "to", "and", "or", "is", "are",
    "was", "be", "this", "that", "with", "by", "at", "from", "as", "on",
}
