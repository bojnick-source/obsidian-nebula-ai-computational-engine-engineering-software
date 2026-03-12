"""Episodic memory: post-run episode capture, storage, and retrieval."""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from forge_learning.evaluators.quality_evaluator import QualityEvaluator

try:
    from supermemory import Supermemory
    _SUPERMEMORY_AVAILABLE = True
except ImportError:
    _SUPERMEMORY_AVAILABLE = False


_CONTAINER_TAG = "forge-episodes"


@dataclass
class Episode:
    run_id: str
    trace_id: str
    project: str
    task_description: str
    agents_involved: list[str]
    outcome: str  # "success" | "partial" | "failure"
    success_patterns: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(default_factory=list)
    reusable_strategies: list[str] = field(default_factory=list)
    tool_parameter_findings: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d = {
            "episode_id": self.episode_id,
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "project": self.project,
            "task_description": self.task_description,
            "agents_involved": self.agents_involved,
            "outcome": self.outcome,
            "success_patterns": self.success_patterns,
            "failure_patterns": self.failure_patterns,
            "reusable_strategies": self.reusable_strategies,
            "tool_parameter_findings": self.tool_parameter_findings,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat(),
        }
        return d


def _compute_utility(
    success_rate: float,
    days_since_last_access: float,
    total_retrievals: int,
) -> float:
    """FSRS-6-inspired utility score for memory prioritization."""
    recency_weight = math.exp(-0.1 * days_since_last_access)
    retrieval_freq = min(total_retrievals / 10.0, 1.0)
    return success_rate * recency_weight * retrieval_freq


class EpisodicMemoryStore:
    """Persist and retrieve episodes from JSONL + Supermemory."""

    def __init__(
        self,
        store_path: Path,
        evaluator: QualityEvaluator | None = None,
        supermemory_api_key: str | None = None,
    ) -> None:
        self._store_path = store_path
        store_path.parent.mkdir(parents=True, exist_ok=True)
        self._evaluator = evaluator or QualityEvaluator()
        self._sm: Any | None = None
        if _SUPERMEMORY_AVAILABLE and supermemory_api_key:
            self._sm = Supermemory(api_key=supermemory_api_key)

    def add(self, episode: Episode, skip_evaluation: bool = False) -> bool:
        """Evaluate and conditionally store an episode.

        Returns True if episode passed quality gate and was stored.
        """
        if not skip_evaluation:
            result = self._evaluator.evaluate(episode.to_dict())
            episode.quality_score = result.score
            if not result.passes:
                return False

        record = episode.to_dict()

        with self._store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        if self._sm is not None:
            try:
                content = yaml.dump(record, default_flow_style=False)
                self._sm.add(content, container_tag=_CONTAINER_TAG)
            except Exception:
                pass

        return True

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Hybrid semantic + keyword search via Supermemory, or file scan fallback."""
        if self._sm is not None:
            try:
                results = self._sm.search(query, container_tag=_CONTAINER_TAG, limit=limit)
                return [r.content if hasattr(r, "content") else r for r in results]
            except Exception:
                pass

        return self._file_search(query, limit)

    def _file_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Simple keyword scan for fallback when Supermemory unavailable."""
        if not self._store_path.exists():
            return []
        query_lower = query.lower()
        results: list[dict[str, Any]] = []
        with self._store_path.open(encoding="utf-8") as f:
            for line in f:
                if query_lower in line.lower():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
                    if len(results) >= limit:
                        break
        return results

    def load_all(self) -> list[dict[str, Any]]:
        if not self._store_path.exists():
            return []
        episodes = []
        with self._store_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    episodes.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return episodes
