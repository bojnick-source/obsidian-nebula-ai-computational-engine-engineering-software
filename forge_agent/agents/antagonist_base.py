"""Abstract base class for all FORGE antagonist agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

VALID_CRITIQUE_TYPES = frozenset({"factual", "dimensional", "provenance", "methodology"})
VALID_SEVERITIES = frozenset({"fatal", "warning", "info"})


@dataclass
class CritiqueResult:
    error_code: str | None          # from docs/contracts/error-codes.md or None
    critique_type: str              # factual | dimensional | provenance | methodology
    severity: str                   # fatal | warning | info
    detail: str                     # >=50 chars, human-readable explanation
    evidence: str                   # supporting standard, equation, or measurement
    confidence_delta: float         # float <= 0.0; how much critique reduces confidence


class AntagonistAgent(ABC):
    """Abstract base for all FORGE antagonist agents.

    Subclasses implement `_generate_critique()` to produce domain-specific
    challenges. The public `critique()` method validates the output contract
    before returning — never trust subclass output blindly (P2 rule).
    """

    def __init__(self, agent_id: str, domain: str) -> None:
        self.agent_id = agent_id        # used — not silently dropped (P2)
        self.domain = domain            # used — not silently dropped (P2)

    def critique(
        self,
        specialist_output: dict,
        context: dict,
    ) -> dict:
        """Run critique and return a validated structured dict.

        Parameters
        ----------
        specialist_output:
            Full output dict from the specialist agent (must conform to
            AGENT_OUTPUT_CONTRACT in _base_specialist.py).
        context:
            Ambient context: task description, load cases, trace_id, etc.

        Returns
        -------
        dict with keys: error_code, critique_type, severity, detail,
                        evidence, confidence_delta
        """
        # Both parameters are consumed — not silently dropped (P2 guard)
        raw: dict = self._generate_critique(specialist_output, context)
        return self._validate(raw)

    @abstractmethod
    def _generate_critique(
        self,
        specialist_output: dict,
        context: dict,
    ) -> dict:
        """Produce raw critique dict. Called by `critique()`.

        Must return a dict with keys matching CritiqueResult fields.
        """
        ...

    # ---------------------------------------------------------------- private

    def _validate(self, raw: dict) -> dict:
        """Validate structure contract; raises ValueError on violation."""
        required = {
            "error_code",
            "critique_type",
            "severity",
            "detail",
            "evidence",
            "confidence_delta",
        }
        missing = required - raw.keys()
        if missing:
            raise ValueError(
                f"AntagonistAgent({self.agent_id}): _generate_critique() "
                f"is missing required keys: {missing}"
            )

        ctype = raw["critique_type"]
        if ctype not in VALID_CRITIQUE_TYPES:
            raise ValueError(
                f"AntagonistAgent({self.agent_id}): critique_type={ctype!r} "
                f"is not in {VALID_CRITIQUE_TYPES}"
            )

        severity = raw["severity"]
        if severity not in VALID_SEVERITIES:
            raise ValueError(
                f"AntagonistAgent({self.agent_id}): severity={severity!r} "
                f"is not in {VALID_SEVERITIES}"
            )

        detail = raw["detail"]
        if not isinstance(detail, str) or len(detail) < 50:
            raise ValueError(
                f"AntagonistAgent({self.agent_id}): detail must be str >=50 chars, "
                f"got {len(detail) if isinstance(detail, str) else type(detail).__name__}"
            )

        delta = raw["confidence_delta"]
        if not isinstance(delta, (int, float)) or float(delta) > 0.0:
            raise ValueError(
                f"AntagonistAgent({self.agent_id}): confidence_delta must be float <= 0, "
                f"got {delta!r}"
            )

        # Normalise to plain dict — do not return dataclass (avoids import coupling)
        return {
            "error_code": raw["error_code"],
            "critique_type": ctype,
            "severity": severity,
            "detail": detail,
            "evidence": str(raw["evidence"]),
            "confidence_delta": float(delta),
        }
