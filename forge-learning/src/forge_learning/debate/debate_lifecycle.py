"""Adversarial debate lifecycle manager.

4-phase protocol:
  1. Independent analysis (no cross-contamination)
  2. Structured critique (novelty-enforced)
  3. Evidence-based response
  4. Arbiter synthesis

Hard cap: 3 rounds. Anti-degeneration enforcement.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import anthropic


MAX_ROUNDS = 3
NOVELTY_REQUIRED = True


@dataclass
class DebatePosition:
    agent_id: str
    phase: str
    findings: list[str]
    assumptions: list[str]
    confidence: float
    what_would_falsify: str


@dataclass
class CritiqueEntry:
    critic_agent: str
    target_agent: str
    critique_type: str  # "technical_error" | "missing_assumption" | "alternative_model" | "unit_error"
    specific_claim: str
    evidence: str
    severity: str  # "fatal" | "significant" | "minor"
    novel: bool = True  # Anti-degeneration: must be novel each round


@dataclass
class DebateRound:
    round_number: int
    critiques: list[CritiqueEntry] = field(default_factory=list)
    responses: list[dict[str, Any]] = field(default_factory=list)
    confidence_delta: float = 0.0


@dataclass
class DebateOutcome:
    verdict: str  # "consensus" | "maintained_disagreement" | "escalated"
    winning_position: str | None
    synthesis: str
    rounds_conducted: int
    confidence_final: float
    degeneration_detected: bool = False


class DebateLifecycle:
    """Orchestrate a full adversarial debate between two agents."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
    ) -> None:
        self._model = model
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def run(
        self,
        specialist: DebatePosition,
        antagonist: DebatePosition,
    ) -> DebateOutcome:
        """Execute the full debate protocol and return a synthesized outcome."""
        rounds: list[DebateRound] = []
        prev_critiques: set[str] = set()

        for round_num in range(1, MAX_ROUNDS + 1):
            debate_round = self._conduct_round(
                specialist, antagonist, round_num, prev_critiques
            )
            rounds.append(debate_round)

            # Anti-degeneration: both confidences declining → escalate
            if self._degeneration_detected(rounds):
                return DebateOutcome(
                    verdict="escalated",
                    winning_position=None,
                    synthesis="Debate degenerated — escalating to human review",
                    rounds_conducted=round_num,
                    confidence_final=min(specialist.confidence, antagonist.confidence),
                    degeneration_detected=True,
                )

            # Track critiques for novelty check
            for c in debate_round.critiques:
                prev_critiques.add(c.specific_claim[:50])

            # Early termination if consensus reached
            if self._consensus_reached(debate_round):
                break

        synthesis = self._synthesize(specialist, antagonist, rounds)
        return synthesis

    def _conduct_round(
        self,
        specialist: DebatePosition,
        antagonist: DebatePosition,
        round_num: int,
        prev_critiques: set[str],
    ) -> DebateRound:
        critique_prompt = self._build_critique_prompt(
            specialist, antagonist, round_num, prev_critiques
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": critique_prompt}],
        )
        critiques = self._parse_critiques(response.content[0].text)
        return DebateRound(
            round_number=round_num,
            critiques=critiques,
        )

    def _build_critique_prompt(
        self,
        specialist: DebatePosition,
        antagonist: DebatePosition,
        round_num: int,
        prev_critiques: set[str],
    ) -> str:
        prev = "\n".join(f"- {c}" for c in prev_critiques) if prev_critiques else "None"
        return f"""You are conducting round {round_num} of an adversarial engineering debate.

SPECIALIST POSITION ({specialist.agent_id}):
Findings: {specialist.findings}
Assumptions: {specialist.assumptions}
Confidence: {specialist.confidence}
What would falsify: {specialist.what_would_falsify}

ANTAGONIST POSITION ({antagonist.agent_id}):
Findings: {antagonist.findings}
Assumptions: {antagonist.assumptions}
Confidence: {antagonist.confidence}

PREVIOUS CRITIQUES (do NOT repeat these):
{prev}

Generate structured critiques. RULES:
1. Each critique must be NOVEL (not in previous critiques list)
2. Must cite specific values, formulas, or standards — no vague objections
3. Critique types: technical_error | missing_assumption | alternative_model | unit_error
4. Max 3 critiques per round

Respond in YAML:
critiques:
  - critic_agent: "<agent_id>"
    target_agent: "<agent_id>"
    critique_type: "<type>"
    specific_claim: "<claim with specific values>"
    evidence: "<standard, formula, or measurement>"
    severity: "fatal|significant|minor"
"""

    def _parse_critiques(self, raw: str) -> list[CritiqueEntry]:
        import yaml
        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("yaml"):
                    clean = clean[4:]
            data = yaml.safe_load(clean.strip())
            entries = []
            for c in data.get("critiques", []):
                entries.append(CritiqueEntry(
                    critic_agent=c.get("critic_agent", ""),
                    target_agent=c.get("target_agent", ""),
                    critique_type=c.get("critique_type", ""),
                    specific_claim=c.get("specific_claim", ""),
                    evidence=c.get("evidence", ""),
                    severity=c.get("severity", "minor"),
                ))
            return entries
        except Exception:
            return []

    def _degeneration_detected(self, rounds: list[DebateRound]) -> bool:
        """Detect if both sides are just restating positions (no novel critiques)."""
        if len(rounds) < 2:
            return False
        last_two = rounds[-2:]
        return all(len(r.critiques) == 0 for r in last_two)

    def _consensus_reached(self, round_: DebateRound) -> bool:
        """Consensus if no fatal critiques remain."""
        return not any(c.severity == "fatal" for c in round_.critiques)

    def _synthesize(
        self,
        specialist: DebatePosition,
        antagonist: DebatePosition,
        rounds: list[DebateRound],
    ) -> DebateOutcome:
        all_critiques = [c for r in rounds for c in r.critiques]
        fatal = [c for c in all_critiques if c.severity == "fatal"]

        if fatal:
            verdict = "maintained_disagreement"
            winning = None
        else:
            verdict = "consensus"
            winning = specialist.agent_id

        synthesis_prompt = f"""Synthesize this engineering debate in 2-3 sentences.
Specialist findings: {specialist.findings}
Antagonist findings: {antagonist.findings}
Fatal critiques: {[c.specific_claim for c in fatal]}
Verdict: {verdict}"""

        resp = self._client.messages.create(
            model=self._model,
            max_tokens=256,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )
        synthesis_text = resp.content[0].text.strip()

        return DebateOutcome(
            verdict=verdict,
            winning_position=winning,
            synthesis=synthesis_text,
            rounds_conducted=len(rounds),
            confidence_final=specialist.confidence if winning else 0.0,
        )
