"""Quality Evaluator — LLM-as-judge gating episodic memory admission.

THE critical learning component. Episodes below threshold=0.8 are discarded.
Research finding: selective add (quality ≥ 0.8) yields self-improvement;
add-all yields degradation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import anthropic


QUALITY_THRESHOLD = 0.8

_CLIENT = None


def _get_client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _CLIENT


@dataclass
class EvaluationResult:
    score: float
    passes: bool
    rationale: str
    improvement_suggestions: list[str]


class QualityEvaluator:
    """Evaluate an episode for memory admission using LLM-as-judge."""

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        threshold: float = QUALITY_THRESHOLD,
    ) -> None:
        self._model = model
        self._threshold = threshold

    def evaluate(self, episode: dict[str, Any]) -> EvaluationResult:
        """Score an episode 0.0–1.0. Returns EvaluationResult."""
        prompt = self._build_evaluation_prompt(episode)
        client = _get_client()

        response = client.messages.create(
            model=self._model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        return self._parse_response(raw)

    def _build_evaluation_prompt(self, episode: dict[str, Any]) -> str:
        episode_json = json.dumps(episode, indent=2, default=str)
        return f"""You are evaluating the quality of an engineering analysis episode for
long-term memory admission. Score it 0.0–1.0 strictly.

EPISODE:
{episode_json}

Evaluate on these dimensions:
1. Technical accuracy (0–0.3): Are findings physically plausible? Units correct?
2. Learning value (0–0.3): Does it contain reusable strategies or failure patterns?
3. Provenance quality (0–0.2): Are sources specific and verifiable?
4. Assumption explicitness (0–0.2): Are all assumptions listed? No null assumptions?

STRICT RULES:
- Score < 0.8 if any calculation appears dimensionally incorrect
- Score < 0.8 if provenance is "standard engineering practice" or similar vague phrase
- Score < 0.8 if assumptions list is empty or null
- Score = 0.0 if the episode contains fabricated tool outputs (no real run_id/trace_id)

Respond in JSON only:
{{
  "score": <float 0.0-1.0>,
  "rationale": "<one sentence>",
  "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>"]
}}"""

    def _parse_response(self, raw: str) -> EvaluationResult:
        try:
            # Strip markdown code fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            data = json.loads(clean.strip())
            score = float(data.get("score", 0.0))
            return EvaluationResult(
                score=score,
                passes=score >= self._threshold,
                rationale=data.get("rationale", ""),
                improvement_suggestions=data.get("improvement_suggestions", []),
            )
        except Exception:
            return EvaluationResult(
                score=0.0,
                passes=False,
                rationale="Failed to parse evaluator response",
                improvement_suggestions=["Ensure episode has valid structure"],
            )
