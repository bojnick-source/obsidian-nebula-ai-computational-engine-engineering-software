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

Moved from forge_agent/agents/verifier.py — VerifierAgent is infrastructure
(quality gate), not a domain specialist. It belongs alongside governance.py,
mcp_manager.py, token_budget.py, etc. in core/.
"""

from __future__ import annotations

import json
import re
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


# ─────────────────────────────────────────────────────────────────────────────
# Static verification gates (no LLM required)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class GateResult:
    gate: str
    passed: bool
    error_code: str | None = None
    detail: str = ""


class UnitGate:
    """AC-05: Every finding must carry non-empty units; no mixed unit systems."""

    # Mixed-unit pairs that indicate inconsistency within a single output
    _SI_STRESS = frozenset({"pa", "kpa", "mpa", "gpa", "n/m2", "n/mm2"})
    _IMPERIAL_STRESS = frozenset({"psi", "ksi"})

    @classmethod
    def check(cls, output: dict) -> GateResult:
        findings = output.get("findings", [])
        if not isinstance(findings, list):
            findings = []

        has_si = False
        has_imperial = False

        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            units_raw = str(finding.get("units", "")).strip()
            if not units_raw:
                return GateResult(
                    gate="UnitGate",
                    passed=False,
                    error_code="ERR_UNIT_MISSING",
                    detail=f"Finding[{i}] has no units",
                )
            units_lower = units_raw.lower()
            if any(u in units_lower for u in cls._SI_STRESS):
                has_si = True
            if any(u in units_lower for u in cls._IMPERIAL_STRESS):
                has_imperial = True

        if has_si and has_imperial:
            return GateResult(
                gate="UnitGate",
                passed=False,
                error_code="ERR_UNIT_INCONSISTENT",
                detail="Mixed SI and imperial stress units detected in findings",
            )

        return GateResult(gate="UnitGate", passed=True)


class DimensionalGate:
    """AC-05: Units must be dimensionally compatible with the declared quantity."""

    # Heuristic: quantity keyword → accepted unit substrings
    _QUANTITY_UNITS: dict[str, frozenset[str]] = {
        "stress": frozenset({"pa", "kpa", "mpa", "gpa", "psi", "ksi", "n/m2", "n/mm2"}),
        "force": frozenset({"n", "kn", "mn", "lbf", "kip"}),
        "displacement": frozenset({"m", "mm", "cm", "km", "in", "ft"}),
        "pressure": frozenset({"pa", "kpa", "mpa", "gpa", "bar", "atm", "psi"}),
        "temperature": frozenset({"k", "°c", "°f", "degc", "degf"}),
        "mass": frozenset({"kg", "g", "mg", "lb", "oz", "t"}),
    }

    @classmethod
    def check(cls, output: dict) -> GateResult:
        findings = output.get("findings", [])
        if not isinstance(findings, list):
            return GateResult(gate="DimensionalGate", passed=True)

        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            quantity = str(finding.get("quantity", "")).lower().strip()
            units = str(finding.get("units", "")).lower().strip()
            if not quantity or not units:
                continue

            for keyword, accepted in cls._QUANTITY_UNITS.items():
                if keyword in quantity:
                    if not any(u in units for u in accepted):
                        return GateResult(
                            gate="DimensionalGate",
                            passed=False,
                            error_code="ERR_DIMENSIONAL_MISMATCH",
                            detail=(
                                f"Finding[{i}] quantity '{quantity}' "
                                f"has incompatible units '{units}'"
                            ),
                        )
                    break

        return GateResult(gate="DimensionalGate", passed=True)


class ProvenanceGate:
    """AC-05: Every finding must cite a specific, traceable source."""

    _GENERIC_SOURCES = frozenset({
        "unknown", "textbook", "literature", "reference", "general",
        "standard", "various", "multiple", "see above", "n/a", "na",
        "none", "", "tbd",
    })

    # Patterns that suggest a real citation: DOI, ISBN, ASM, ASTM, ISO, MIL-SPEC
    # Precompiled for efficiency — patterns are static across all calls.
    _CITATION_PATTERNS: tuple[re.Pattern, ...] = tuple(re.compile(p) for p in (
        r"10\.\d{4,}/",          # DOI
        r"isbn",                  # ISBN
        r"astm\s+[a-z]\d+",      # ASTM A1234
        r"iso\s+\d+",            # ISO 9001
        r"mil-",                  # MIL-SPEC
        r"asm\s+handbook",       # ASM Handbook
        r"matweb",               # MatWeb
        r"\d{4}",                # at least a 4-digit year (rough publication marker)
    ))

    @classmethod
    def check(cls, output: dict) -> GateResult:
        findings = output.get("findings", [])
        if not isinstance(findings, list):
            return GateResult(gate="ProvenanceGate", passed=True)

        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            prov = finding.get("provenance", {})
            if not isinstance(prov, dict):
                prov = {}

            source = str(prov.get("source", "")).strip().lower()
            if not source or source in cls._GENERIC_SOURCES:
                return GateResult(
                    gate="ProvenanceGate",
                    passed=False,
                    error_code="ERR_PROVENANCE_MISSING",
                    detail=f"Finding[{i}] provenance.source is missing or too generic: '{source}'",
                )

            specificity = str(prov.get("specificity", "")).strip().lower()
            if specificity == "low":
                return GateResult(
                    gate="ProvenanceGate",
                    passed=False,
                    error_code="ERR_PROVENANCE_UNSPECIFIC",
                    detail=f"Finding[{i}] provenance.specificity is 'low'",
                )

            citation = str(prov.get("citation", "")).strip()
            if citation:
                citation_lower = citation.lower()
                has_real_citation = any(
                    pat.search(citation_lower)
                    for pat in cls._CITATION_PATTERNS
                )
                if not has_real_citation:
                    return GateResult(
                        gate="ProvenanceGate",
                        passed=False,
                        error_code="ERR_PROVENANCE_UNSPECIFIC",
                        detail=(
                            f"Finding[{i}] citation lacks a traceable reference "
                            f"(DOI, ASTM, ISO, ASM, year, etc.): '{citation[:80]}'"
                        ),
                    )

        return GateResult(gate="ProvenanceGate", passed=True)


def run_all_gates(output: dict) -> list[GateResult]:
    """Run all four verification gates against an agent output dict.

    Gates run in order: ContractGate → UnitGate → DimensionalGate → ProvenanceGate.
    Call this before any vault write. Block the write if any gate returns passed=False.

    Returns:
        List of GateResult (one per gate). Check all — don't short-circuit on first fail
        so callers get the full picture.
    """
    results: list[GateResult] = []

    # Contract gate (existing static validator)
    violations = AgentOutputContract.validate(output)
    if violations:
        results.append(GateResult(
            gate="ContractGate",
            passed=False,
            error_code="ERR_CONTRACT_VIOLATION",
            detail="; ".join(v.reason for v in violations),
        ))
    else:
        results.append(GateResult(gate="ContractGate", passed=True))

    results.append(UnitGate.check(output))
    results.append(DimensionalGate.check(output))
    results.append(ProvenanceGate.check(output))

    return results


# ------------------------------------------------------------------ helpers


def _try_parse_json(text: str) -> dict | None:
    """Try to extract and parse JSON from text."""
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
