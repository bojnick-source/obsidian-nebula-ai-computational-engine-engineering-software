"""DebateOrchestrator — drives specialist→antagonist debate rounds within forge_agent.

Does NOT import from forge-learning. Self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DebateResult:
    verdict: str          # "consensus" | "maintained_disagreement"
    final_output: dict    # specialist_output (possibly updated after debate)
    rounds: int           # always >= 1
    critiques: list = field(default_factory=list)  # raw critique dicts from antagonist


class DebateOrchestrator:
    """Drives one or more rounds of specialist→antagonist debate.

    Does NOT import from forge-learning. Self-contained within forge_agent.

    Parameters
    ----------
    specialist:
        Object with a callable interface compatible with AntagonistAgent.
        Stored for future multi-round specialist-response rounds; not called
        in the current single-round implementation (P2: stored, not discarded).
    antagonist:
        AntagonistAgent subclass — must expose
        ``critique(specialist_output, context) -> dict`` returning keys:
        error_code, critique_type, severity, detail, evidence, confidence_delta.
    """

    MAX_ROUNDS: int = 3

    def __init__(
        self,
        specialist: Any,
        antagonist: Any,
    ) -> None:
        self._specialist = specialist   # stored for future multi-round use (P2)
        self._antagonist = antagonist   # called in run_debate (P2)

    def run_debate(
        self,
        specialist_output: dict,
        context: dict,
    ) -> DebateResult:
        """Run up to MAX_ROUNDS rounds of antagonist critique.

        Round protocol:
          1. Antagonist critiques specialist_output.
          2. If severity=="fatal" → maintained_disagreement; stop.
          3. Otherwise → consensus after first clean round.

        Both parameters are consumed — specialist_output passed to antagonist,
        context passed to antagonist (P2 rule satisfied).

        Parameters
        ----------
        specialist_output:
            Full specialist output dict.
        context:
            Ambient context (task description, blackboard keys, trace_id, etc.).

        Returns
        -------
        DebateResult with verdict, final_output, rounds, critiques.
        """
        critiques_all: list[dict] = []
        maintained = False
        round_num = 0

        for round_num in range(1, self.MAX_ROUNDS + 1):
            critique = self._antagonist.critique(specialist_output, context)
            critiques_all.append(critique)

            if critique.get("severity") == "fatal":
                maintained = True
                break   # fatal critique ends debate immediately

            # No fatal critique → consensus; stop after first clean round
            break

        # Ensure round_num is at least 1 even if MAX_ROUNDS == 0 (defensive)
        if round_num == 0:
            round_num = 1

        verdict = "maintained_disagreement" if maintained else "consensus"
        return DebateResult(
            verdict=verdict,
            final_output=specialist_output,
            rounds=round_num,
            critiques=critiques_all,
        )
