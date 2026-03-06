"""
Verifier agent — enforces the Agent Output Contract.

The verifier reviews specialist output and either:
  - stamps "validated"   → blackboard.verification_stamp.status = "validated"
  - stamps "disputed"    → populates blackboard.disagreements[]

Agent Output Contract (all fields required):
  model_choice        str   — rationale for chosen approach
  equations           list  — LaTeX equations used
  units               str   — all SI
  sanity_checks       list  — ≥1 of: limiting_case | conservation | dimensional
  calculation_path    str   — step-by-step narrative
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


VERIFIER_SYSTEM_PROMPT = """\
You are the FORGE Verifier — the final quality gate for all engineering analysis.

Your job is to review specialist agent output against the **Agent Output Contract**:

REQUIRED fields:
1. model_choice       — explicit rationale for the chosen engineering model / approach
2. equations          — all governing equations in LaTeX notation
3. units              — confirm all values carry SI units
4. sanity_checks      — at least ONE of:
   a) limiting_case   — does the answer reduce to a known limit?
   b) conservation    — does it satisfy conservation of energy/mass/momentum?
   c) dimensional     — is dimensional analysis consistent?
5. calculation_path   — reproducible step-by-step derivation

SCORING (return JSON):
{
  "contract_satisfied": true | false,
  "missing_fields": [],
  "equation_errors": [],
  "unit_errors": [],
  "sanity_check_verdict": "pass" | "fail" | "partial",
  "overall_verdict": "validated" | "disputed",
  "notes": "...",
  "corrected_answer": null | "..."
}

Be rigorous. Reject vague provenance, fabricated citations, or missing assumptions.
If units are wrong or dimensions are inconsistent, mark it disputed.
"""


@dataclass
class ContractViolation:
    field: str
    reason: str


@dataclass
class VerificationResult:
    contract_satisfied: bool
    overall_verdict: str          # "validated" | "disputed"
    missing_fields: list[str] = field(default_factory=list)
    equation_errors: list[str] = field(default_factory=list)
    unit_errors: list[str] = field(default_factory=list)
    sanity_check_verdict: str = "pass"
    notes: str = ""
    corrected_answer: str | None = None


class AgentOutputContract:
    """Static validator — checks output dict for required fields before LLM review."""

    REQUIRED_FIELDS = [
        "model_choice",
        "equations",
        "units",
        "sanity_checks",
        "calculation_path",
    ]

    @classmethod
    def validate(cls, output: dict) -> list[ContractViolation]:
        """Returns list of violations; empty = contract satisfied."""
        violations: list[ContractViolation] = []

        for f in cls.REQUIRED_FIELDS:
            if f not in output or not output[f]:
                violations.append(ContractViolation(field=f, reason=f"Field '{f}' is missing or empty"))

        # equations must be a non-empty list
        if "equations" in output:
            if not isinstance(output["equations"], list) or len(output["equations"]) == 0:
                violations.append(ContractViolation(
                    field="equations",
                    reason="'equations' must be a non-empty list of LaTeX strings"
                ))

        # sanity_checks must have ≥1 entry
        if "sanity_checks" in output:
            checks = output["sanity_checks"]
            if not isinstance(checks, list) or len(checks) == 0:
                violations.append(ContractViolation(
                    field="sanity_checks",
                    reason="'sanity_checks' must contain at least one check"
                ))

        return violations


class VerifierAgent:
    """LLM-backed verifier that reviews specialist output."""

    MODEL = "claude-opus-4-6"

    def __init__(self, client: Any) -> None:
        self._client = client

    async def verify(
        self,
        specialist_output: str,
        blackboard: dict,
        agent_role: str = "specialist",
    ) -> VerificationResult:
        """
        1. Quick static contract check (no LLM)
        2. Full LLM review
        3. Update blackboard with stamp
        """
        # Parse output if JSON-like
        parsed = _try_parse_json(specialist_output)
        if parsed:
            violations = AgentOutputContract.validate(parsed)
            if violations:
                # Fast-fail on structural violations
                return VerificationResult(
                    contract_satisfied=False,
                    overall_verdict="disputed",
                    missing_fields=[v.field for v in violations],
                    notes="; ".join(v.reason for v in violations),
                )

        # LLM review
        prompt = (
            f"Review this output from the '{agent_role}' specialist:\n\n"
            f"```\n{specialist_output[:6000]}\n```\n\n"
            f"Current blackboard context:\n"
            f"```json\n{json.dumps(blackboard, indent=2, default=str)[:2000]}\n```\n\n"
            "Return your assessment as JSON matching the schema above."
        )

        msg = await self._client.messages.create(
            model=self.MODEL,
            max_tokens=1024,
            temperature=0.0,
            system=VERIFIER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        result_text = msg.content[0].text
        result_data = _try_parse_json(result_text) or {}

        verdict = result_data.get("overall_verdict", "disputed")
        result = VerificationResult(
            contract_satisfied=result_data.get("contract_satisfied", False),
            overall_verdict=verdict,
            missing_fields=result_data.get("missing_fields", []),
            equation_errors=result_data.get("equation_errors", []),
            unit_errors=result_data.get("unit_errors", []),
            sanity_check_verdict=result_data.get("sanity_check_verdict", "fail"),
            notes=result_data.get("notes", ""),
            corrected_answer=result_data.get("corrected_answer"),
        )

        # Stamp blackboard
        stamp = {
            "status": verdict,
            "verifier_notes": result.notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        blackboard["verification_stamp"] = stamp

        if verdict == "disputed" and result.notes:
            blackboard.setdefault("disagreements", []).append({
                "agent": f"verifier→{agent_role}",
                "claim": "contract violation",
                "basis": result.notes,
            })

        return result


# ------------------------------------------------------------------ helpers


def _try_parse_json(text: str) -> dict | None:
    """Try to extract and parse JSON from text."""
    import re
    # Try to find JSON block
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
