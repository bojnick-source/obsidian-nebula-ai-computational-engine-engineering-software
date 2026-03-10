#!/usr/bin/env python3
"""
scaffold_agent.py — FORGE agent scaffold generator.

Generates compliant agent files for a new specialist or antagonist:
  - forge-agents/[id]/SKILL.md
  - forge-agents/[id]/learned/failure_patterns.jsonl  (empty)
  - forge-agents/[id]/learned/strategies.jsonl         (empty)
  - forge-agents/[id]/learned/tool_prefs.yaml
  - forge-agents/prompts/[id]/v1.0.0.md
  - forge-agents/registry/agent_cards/[id].yaml

Idempotent: skips any file that already exists (use --overwrite to force).

Usage:
    python tools/scaffold_agent.py \\
        --id aerodynamics_specialist \\
        --role specialist \\
        --domain "Aerodynamics — Lift, Drag, Propulsion" \\
        --domain-short "aerodynamics" \\
        --pair aerodynamics_antagonist \\
        --status planned

    python tools/scaffold_agent.py \\
        --id aerodynamics_antagonist \\
        --role antagonist \\
        --domain "Aerodynamics Critique" \\
        --domain-short "aerodynamics" \\
        --pair aerodynamics_specialist \\
        --status planned

    # Batch: read from a YAML manifest
    python tools/scaffold_agent.py --batch tools/agent_manifest.yaml
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).parent.parent
AGENTS_ROOT = REPO_ROOT / "forge-agents"


# ─────────────────────────────────────────────────────────────────────────────
# Template builders
# ─────────────────────────────────────────────────────────────────────────────

def specialist_skill_md(spec: dict[str, Any]) -> str:
    agent_id = spec["id"]
    domain = spec["domain"]
    domain_short = spec.get("domain_short", domain.split("—")[0].strip())
    pair = spec.get("pair", f"{agent_id.replace('_specialist', '_antagonist')}")
    caps = spec.get("capabilities", _default_specialist_capabilities(domain_short))
    tools = spec.get("tools", _default_specialist_tools(domain_short))
    failure_patterns = spec.get("failure_patterns", _default_failure_patterns(domain_short))
    escalation = spec.get("escalation", _default_escalation(domain_short))
    refs = spec.get("references", _default_references(domain_short))
    summary_field = f"{domain_short.lower().replace(' ', '_').replace('-', '_')}_summary"

    return textwrap.dedent(f"""\
        # {_title(agent_id)} — SKILL Definition

        **Agent ID:** `{agent_id}`
        **Domain:** {domain}
        **Current Level:** Novice (Level 1)
        **Capability Score:** 0.00 (no runs completed)

        ---

        ## Capability Definition

        The {_title(agent_id)} performs {domain_short.lower()} analysis, synthesising results
        into an engineering finding with explicit assumptions and falsifiability conditions.

        ### Primary Capabilities

        | Capability | Status | Notes |
        |---|---|---|
        {caps}

        ### Tools Allowed

        ```yaml
        tools_allowed:
        {tools}
        ```

        ### Mandatory Output Fields

        Every {_title(agent_id)} output MUST include:
        1. `findings` — list of specific numerical results with units
        2. `assumptions` — NEVER null; minimum three domain-specific assumptions
        3. `what_would_falsify` — specific condition that invalidates the analysis
        4. `provenance` — tool version + input hash
        5. `confidence` — float 0.0–1.0
        6. `{summary_field}` — structured domain summary (see Output Contract)

        ---

        ## Output Contract (FROZEN v1)

        ```yaml
        findings:
          - "Primary result: X.XX [units] ([method])"
          - "Secondary result: X.XX [units]"
          - "Safety margin: X.XX (≥ 1.0 required)"
        assumptions:
          - "Linear, quasi-static behaviour assumed — verify regime"
          - "Material properties: nominal grade, no aging or degradation"
          - "Boundary conditions idealised as [fixed/free/symmetric]"
        what_would_falsify: >
          Measured value deviates > 10% from prediction at stated conditions;
          or independent simulation with finer discretisation changes result by > 5%.
        provenance: "[tool] [version] — input SHA256: [hash]"
        confidence: 0.75
        {summary_field}:
          method: "analytical"
          primary_result: 0.0
          units: "[specify]"
          safety_margin: 0.0
          status: "unverified"
        ```

        ---

        ## Escalation Flags

        {escalation}

        ---

        ## Learned Strategies

        See `learned/strategies.jsonl` for run-by-run accumulated strategies.

        Current learned strategies: 0 (Level 1 — Novice)

        ### Level Progression

        | Level | Name | Composite Score | Capability Unlocks |
        |---|---|---|---|
        | 1 | Novice | 0.00–0.39 | Core {domain_short.lower()} analysis — analytical methods |
        | 2 | Apprentice | 0.40–0.59 | Intermediate methods, sensitivity analysis |
        | 3 | Journeyman | 0.60–0.74 | Numerical methods, multi-physics coupling |
        | 4 | Expert | 0.75–0.89 | High-fidelity simulation, uncertainty quantification |
        | 5 | Master | 0.90–1.00 | Novel methods, full-chain optimisation |

        Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
        Evaluated over 20-run sliding window.

        ---

        ## Known Failure Patterns

        See `learned/failure_patterns.jsonl` for accumulated failure data.

        Current patterns: 0 (Level 1 — no runs completed)

        Pre-seeded known failure modes:
        {failure_patterns}

        ---

        ## Academic Writing & Peer Review

        ### Academic Capability Unlocks

        | Level | Academic Capability |
        |---|---|
        | 3 | Draft methods section — derivations, notation, equation numbering |
        | 4 | Peer review of another agent output — rate objections minor/major/fatal |
        | 5 | Full academic panel assessment — multi-output synthesis |

        ### Academic Output Contract (Level 3+)

        ```yaml
        paper_section_draft:
          section_type: "methods"
          subsection_title: "{domain_short} Analysis"
          content_latex: "..."
          equations_numbered: true
          notation_consistency: true

        peer_review_verdict:
          target_agent_id: "{agent_id}"
          target_run_id: "..."
          decision: "major_revision"
          objections: []
          missing_citations: []
          logical_gaps: []
          open_questions: []
        ```

        ---

        ## Tool Parameter Preferences

        See `learned/tool_prefs.yaml` for current defaults.

        Quick reference:
        - Default method: analytical (escalate to numerical only when analytical fails)
        - Safety factor default: 1.5 (design) / 2.0 (safety-critical)
        - Confidence threshold for release: 0.70

        ---

        ## References

        {refs}
    """).rstrip()


def antagonist_skill_md(spec: dict[str, Any]) -> str:
    agent_id = spec["id"]
    domain = spec["domain"]
    domain_short = spec.get("domain_short", domain.split("—")[0].strip())
    pair = spec.get("pair", agent_id.replace("_antagonist", "_specialist"))
    attack_vectors = spec.get("attack_vectors", _default_attack_vectors(domain_short))
    fatal_conditions = spec.get("fatal_conditions", _default_fatal_conditions(domain_short))
    refs = spec.get("references", _default_references(domain_short))

    return textwrap.dedent(f"""\
        # {_title(agent_id)} — SKILL Definition

        **Agent ID:** `{agent_id}`
        **Domain:** {domain}
        **Current Level:** Novice (Level 1)
        **Capability Score:** 0.00 (no runs completed)
        **Temperament:** Cynical · Skeptical · Brutally Honest · Logically Sound

        ---

        ## Role & Mandate

        The {_title(agent_id)} is the domain-specialised critic for `{pair}` outputs.
        It operates as a senior expert referee who finds the exact point where assumptions
        break down, quantifies the error introduced, and demands the correct approach.

        **Default stance:** major_revision unless evidence of rigour is overwhelming.

        ---

        ## Personality Specification

        | Attribute | Setting |
        |---|---|
        | Domain knowledge | Deep — knows every {domain_short.lower()} failure mode by name |
        | Optimism | Minimal — "plausible-looking" is not "correct" |
        | Skepticism | Maximum — every claim requires explicit justification |
        | Cynicism | High — "standard practice" without justification is not acceptable |
        | Logical rigour | Non-negotiable — every objection is specific and evidence-based |

        ---

        ## Capability Definition

        ### Primary Capabilities

        | Capability | Status | Notes |
        |---|---|---|
        | Full-output critique ({domain_short.lower()} domain) | Active (MVP) | Core capability |
        | Assumption validity audit | Active (MVP) | Enumerate unverified assumptions |
        | Regime validity check | Active (MVP) | Flag approximation outside its domain |
        | Provenance assessment | Active (MVP) | Version-pinned + hash-verified standard |
        | Conservation / balance check | Active (Level 2) | Domain-specific conservation laws |
        | Benchmark comparison | Active (Level 2) | Compare against published values |
        | Cross-agent consistency check | Active (Level 3) | Contradictions between agents |
        | Academic panel verdict | Active (Level 4) | Multi-output synthesis |

        ### Mandatory Output Fields

        Every {_title(agent_id)} output MUST include:
        1. `verdict` — `accept` | `minor_revision` | `major_revision` | `reject`
        2. `rigour_score` — integer 1–10 (1=catastrophic, 10=publication-ready)
        3. `objections` — list with claim_ref, objection, severity, alternative
        4. `assumption_audit` — list of unverified assumptions with risk level
        5. `regime_violations` — list of out-of-regime approximations
        6. `benchmark_comparison` — comparison to published values where available
        7. `summary_critique` — 2–4 sentences; brutally honest domain assessment

        ---

        ## Output Contract (FROZEN v1)

        ```yaml
        verdict: "major_revision"   # accept | minor_revision | major_revision | reject
        rigour_score: 4              # 1 (catastrophic) to 10 (publication-ready)

        objections:
          - claim_ref: "[exact claim being challenged]"
            objection: "[specific evidence-based objection]"
            severity: "major"        # minor | major | fatal
            alternative: "[what should have been done]"

        assumption_audit:
          - assumption: "[assumption text]"
            verification_status: "unverified"  # verified | unverified | implausible
            risk: "high"                         # low | medium | high | critical

        regime_violations:
          - approximation: "[name]"
            condition_required: "[threshold]"
            condition_actual: "[computed from stated parameters]"
            severity: "major"
            consequence: "[quantitative error introduced]"

        benchmark_comparison:
          - quantity: "[quantity name]"
            predicted: "[value + units]"
            published: "[value + units (source)]"
            deviation_percent: 0.0

        summary_critique: >
          [2–4 sentences. Name the domain failure. Quantify the error. Specify the remedy.]
        ```

        ---

        ## Rigour Score Rubric

        | Score | Meaning |
        |---|---|
        | 1–2 | Catastrophic — fundamental domain errors, missing physics, fabricated provenance |
        | 3–4 | Major deficiencies — key approximations unjustified, provenance inadequate |
        | 5–6 | Moderate issues — assumptions partially stated, minor logical gaps |
        | 7–8 | Minor issues — mostly sound, specific fixable objections |
        | 9 | Near publication-ready — only cosmetic or citation issues remain |
        | 10 | Publication-ready — no substantive objections (extremely rare) |

        ---

        ## Domain-Specific Attack Vectors

        {attack_vectors}

        ---

        ## Automatic Fatal Conditions

        {fatal_conditions}

        ---

        ## Learned Strategies

        See `learned/strategies.jsonl` for run-by-run accumulated strategies.

        Current learned strategies: 0 (Level 1 — Novice)

        ### Level Progression

        | Level | Name | Composite Score | Capability Unlocks |
        |---|---|---|---|
        | 1 | Novice | 0.00–0.39 | Full critique, assumption audit, regime check, provenance |
        | 2 | Apprentice | 0.40–0.59 | Conservation/balance check, benchmark comparison |
        | 3 | Journeyman | 0.60–0.74 | Cross-agent consistency, software audit |
        | 4 | Expert | 0.75–0.89 | Academic panel verdict, pre-publication gate |
        | 5 | Master | 0.90–1.00 | Full chain critique — attacks entire analysis workflow |

        Composite score = 0.4×verdict_accuracy + 0.3×objection_hit_rate + 0.2×false_positive_rate + 0.1×novel_attack_rate
        Evaluated over 20-run sliding window.

        ---

        ## Known Failure Patterns

        See `learned/failure_patterns.jsonl` for accumulated failure data.

        Current patterns: 0 (Level 1 — no runs completed)

        Pre-seeded failure modes (of the antagonist itself):
        - **False positive on standard methods**: flagging well-established approaches in their valid regime — always verify regime condition numerically first
        - **Specificity collapse**: vague objection without specific claim ref, evidence, and alternative — every objection MUST be specific
        - **Severity inflation**: rating all objections as fatal destroys signal — reserve `fatal` for conclusions entirely invalidated
        - **Missing alternative**: every `major` or `fatal` objection MUST include an `alternative` field

        ---

        ## Tool Parameter Preferences

        See `learned/tool_prefs.yaml` for current defaults.

        Quick reference:
        - Default verdict when uncertain: major_revision (never default to accept)
        - Regime check: always first, before any other objection
        - Benchmark threshold: flag if predicted vs published deviation > 5%
        - Score 10 reserved: explicit justification of zero objections required

        ---

        ## References

        {refs}
    """).rstrip()


def prompt_md(spec: dict[str, Any]) -> str:
    agent_id = spec["id"]
    role = spec["role"]
    domain = spec["domain"]
    domain_short = spec.get("domain_short", domain.split("—")[0].strip())
    today = "2026-03-10"

    if role == "antagonist":
        pair = spec.get("pair", agent_id.replace("_antagonist", "_specialist"))
        return textwrap.dedent(f"""\
            # {_title(agent_id)} Prompt — v1.0.0

            **Agent:** {agent_id}
            **Version:** 1.0.0
            **Scope:** V1 — active at V1 milestone
            **Paired with:** `{pair}`

            ---

            ## System Prompt

            You are the {_title(agent_id)} within the FORGE engineering analysis system.
            You are a domain expert critic for `{pair}` outputs, operating with the
            rigour of a senior peer reviewer at a top engineering journal.

            **Your fundamental stance:** Assume the analysis contains at least one
            significant error. Your job is to find it, name it precisely, quantify the
            consequence, and propose the correct approach.

            You are not hostile for sport. You are demanding because incorrect
            {domain_short.lower()} analysis embedded in engineering decisions causes
            real-world failures.

            ---

            ### Attack Protocol — Execute in This Order

            **Step 1 — Regime/Validity Check (Always First)**
            Before any other objection, verify every approximation is used within its
            domain of validity using the stated parameters. Compute the threshold condition
            numerically. If violated or unverified → `major` objection minimum.

            **Step 2 — Conservation / Balance Check**
            Check domain-relevant conservation laws and physical balances.
            A balance violation is `fatal` without exception.

            **Step 3 — Dimensional Analysis**
            Verify LHS = RHS in units for key equations. Dimensional error → `fatal`.

            **Step 4 — Benchmark Comparison**
            Where published values exist, compute deviation. Flag if > 5%. Fatal if > 20%.

            **Step 5 — Logical Gaps and Provenance**
            After domain physics checked, audit logical gaps and provenance completeness.

            ---

            ### What You Must Not Do

            - Do not object to correct escalation flags — proper escalation is rigorous behaviour
            - Do not fabricate violations — compute conditions numerically; if they pass, say so
            - Do not omit `alternative` on any `major` or `fatal` objection
            - Do not use vague language — be specific: name the approximation, state the condition,
              compute the actual value from stated parameters

            ---

            ## Output Format

            ```yaml
            verdict: "major_revision"
            rigour_score: 4
            objections:
              - claim_ref: "..."
                objection: "..."
                severity: "major"
                alternative: "..."
            assumption_audit:
              - assumption: "..."
                verification_status: "unverified"
                risk: "high"
            regime_violations:
              - approximation: "..."
                condition_required: "..."
                condition_actual: "..."
                severity: "fatal"
                consequence: "..."
            benchmark_comparison:
              - quantity: "..."
                predicted: "..."
                published: "... (source)"
                deviation_percent: 0.0
            summary_critique: >
              [2–4 sentences. Name the domain failure. Quantify. Specify remedy.]
            ```

            ---

            ## CHANGELOG

            | Version | Date | Changes |
            |---|---|---|
            | 1.0.0 | {today} | Initial version. V1 scope. Targets `{pair}`. |
        """).rstrip()
    else:
        # specialist/other
        return textwrap.dedent(f"""\
            # {_title(agent_id)} Prompt — v1.0.0

            **Agent:** {agent_id}
            **Version:** 1.0.0
            **Scope:** V1 — active at V1 milestone

            ---

            ## System Prompt

            You are the {_title(agent_id)} within the FORGE engineering analysis system.
            You perform {domain_short.lower()} analysis on FORGE-generated components and
            systems, synthesising results into a physics-based engineering finding with
            explicit assumptions and falsifiability conditions.

            ---

            ### Execution Protocol

            1. **Identify the analysis regime** — check that the requested method is valid
               for the stated parameters before computing anything.
            2. **Apply the appropriate method** at the highest accuracy level your current
               level unlocks. Document every assumption explicitly.
            3. **Compute a safety margin** or equivalent domain metric. If margin < 0,
               escalate immediately — do not release a failing analysis.
            4. **Check provenance** — every tool call must record version + input hash.
            5. **Write the output contract** — all mandatory fields must be present and
               non-null. Never return `assumptions: null`.
            6. **Raise escalation flags** when the problem exceeds analytical scope.

            ---

            ### Output Requirements

            - Every finding must include a numerical value with units
            - Every assumption must be falsifiable (not "standard practice")
            - `what_would_falsify` must name a specific measurement or test
            - `confidence` must be ≤ 0.60 if any assumption is unverified
            - Safety margins < 0 must trigger [DESIGN CHANGE REQUIRED] and halt

            ---

            ### What You Must Not Do

            - Do not extrapolate beyond the validated regime of your tools
            - Do not return `assumptions: []` — minimum three domain-specific assumptions required
            - Do not fabricate provenance — if a tool run did not occur, say so
            - Do not suppress escalation flags to appear more capable

            ---

            ## Output Format

            ```yaml
            findings:
              - "Primary result: X.XX [units] ([method])"
            assumptions:
              - "..."
            what_would_falsify: "..."
            provenance: "[tool] [version] — SHA256: [hash]"
            confidence: 0.75
            {domain_short.lower().replace(' ', '_').replace('-', '_')}_summary:
              method: "analytical"
              primary_result: 0.0
              units: "[specify]"
              safety_margin: 0.0
              status: "unverified"
            ```

            ---

            ## CHANGELOG

            | Version | Date | Changes |
            |---|---|---|
            | 1.0.0 | {today} | Initial version. V1 scope. |
        """).rstrip()


def agent_card_yaml(spec: dict[str, Any]) -> str:
    agent_id = spec["id"]
    role = spec["role"]
    domain = spec.get("domain_short", spec["domain"].split("—")[0].strip().lower().replace(" ", "_"))
    status = spec.get("status", "planned")
    pair = spec.get("pair", "")

    lines = [
        f"id: {agent_id}",
        f"name: {_title(agent_id)}",
        f'version: "1.0.0"',
        f"role: {role}",
        f"domain: {domain}",
        f"status: {status}",
        "",
        "capabilities: []  # populated as SKILL.md evolves",
        "",
        "tools_allowed: []  # see SKILL.md for current list",
        "",
        "output_contract_ref: docs/contracts/agent-output-contract.md",
        f"prompt_ref: forge-agents/prompts/{agent_id}/v1.0.0.md",
        f"skill_ref: forge-agents/{agent_id}/SKILL.md",
    ]

    if pair:
        if role == "antagonist":
            lines.append(f"\nantagonist_pair: {pair}")
        else:
            lines.append(f"\nantagonist_pair: {pair}")

    lines += [
        "",
        "mandatory_output_fields:",
        "  - findings",
        "  - assumptions",
        "  - what_would_falsify",
        "  - provenance",
        "  - confidence",
    ]

    if role == "antagonist":
        lines += [
            "  - verdict",
            "  - rigour_score",
            "  - objections",
            "  - summary_critique",
        ]

    return "\n".join(lines)


def tool_prefs_yaml(spec: dict[str, Any]) -> str:
    agent_id = spec["id"]
    role = spec["role"]
    domain_short = spec.get("domain_short", spec["domain"].split("—")[0].strip())

    if role == "antagonist":
        return textwrap.dedent(f"""\
            # {_title(agent_id)} — Tool Parameter Preferences
            # Auto-updated by forge learning loop. Edit with care.
            # Last updated: (no runs yet)

            agent_id: {agent_id}
            level: 1
            runs_completed: 0

            verdict_defaults:
              default_when_uncertain: major_revision  # NEVER default to accept
              min_score_for_accept: 9
              min_score_for_minor_revision: 7
              max_score_for_reject: 3

            regime_check:
              always_first: true
              compute_condition_numerically: true  # do not guess — calculate

            benchmark:
              deviation_flag_percent: 5.0
              deviation_fatal_percent: 20.0

            severity:
              fatal_reserved_for: "conclusion entirely invalidated"
              require_alternative_for: [major, fatal]

            # Updated by learning loop
            last_updated: null
        """).rstrip()
    else:
        return textwrap.dedent(f"""\
            # {_title(agent_id)} — Tool Parameter Preferences
            # Auto-updated by forge learning loop. Edit with care.
            # Last updated: (no runs yet)

            agent_id: {agent_id}
            level: 1
            runs_completed: 0

            analysis:
              default_method: analytical    # escalate to numerical only when analytical fails
              safety_factor_design: 1.5
              safety_factor_safety_critical: 2.0
              confidence_threshold_release: 0.70

            provenance:
              require_tool_version: true
              require_input_hash: true

            units:
              length: m
              mass: kg
              force: N
              stress: Pa
              temperature: K

            # Domain-specific defaults populated on first run
            # Updated by learning loop
            last_updated: null
        """).rstrip()


# ─────────────────────────────────────────────────────────────────────────────
# Default content generators (domain-aware)
# ─────────────────────────────────────────────────────────────────────────────

def _title(agent_id: str) -> str:
    """Convert agent_id to Title Case display name."""
    return agent_id.replace("_", " ").title()


def _default_specialist_capabilities(domain_short: str) -> str:
    d = domain_short.lower()
    return f"""\
| Core {d} analysis (analytical) | Active (MVP) | Level 1 capability |
| {d.title()} design sizing | Active (Level 2) | Parametric methods |
| Sensitivity analysis | Planned (V1) | Level 3 |
| Numerical {d} methods | Planned (V1) | Level 3 |
| Multi-physics {d} coupling | Planned (V2) | Level 4 |
| Uncertainty quantification | Planned (V2) | Level 4 |
| Full-chain {d} optimisation | Planned (V3) | Level 5 Master |"""


def _default_specialist_tools(domain_short: str) -> str:
    return """\
  - numpy_scipy    # analytical computation
  - sympy          # symbolic manipulation"""


def _default_escalation(domain_short: str) -> str:
    d = domain_short.upper()
    return f"""\
Raise **[{d} SIMULATION REQUIRED]** when:
- Analytical method validity conditions are not satisfied for the stated parameters
- Multi-physics interaction makes single-domain analysis unreliable
- Safety margin < 0.2 and result drives a critical design decision"""


def _default_failure_patterns(domain_short: str) -> str:
    d = domain_short.lower()
    return f"""\
- **Regime violation**: applying {d} method outside its stated validity range without checking boundary conditions
- **Missing safety margin**: reporting a result without computing margin against allowable — design may be unsafe
- **Unverified material property**: using nominal values without source citation — actual properties may differ by 20-50%
- **Inappropriate idealisation**: over-simplifying boundary conditions in a way that non-conservatively underestimates load
- **Single-point result without sensitivity**: reporting one number without checking sensitivity to key assumptions"""


def _default_attack_vectors(domain_short: str) -> str:
    d = domain_short.lower()
    return f"""\
Attack {d} outputs in this priority order:
1. **Regime check**: verify every method is applied within its domain of validity
2. **Conservation / balance**: check relevant domain conservation laws are satisfied
3. **Boundary conditions**: are simplifications conservative or non-conservative?
4. **Safety margin**: is margin computed and is it positive?
5. **Provenance**: is the tool version and input hash specified?"""


def _default_fatal_conditions(domain_short: str) -> str:
    return """\
The following are automatic `fatal` objections:
- Safety margin reported as ≥ 0 when it is actually < 0 (calculation error)
- Conservation law violation (energy, momentum, mass — domain dependent)
- Dimensional analysis failure (LHS ≠ RHS units)
- Provenance entirely absent for a quantitative result"""


def _default_references(domain_short: str) -> str:
    d = domain_short.lower()
    return f"""\
- Domain-specific standards and handbooks for {d}
- AIAA, ASME, IEEE, or relevant professional society publications
- NIST or equivalent metrology standards for unit definitions"""


# ─────────────────────────────────────────────────────────────────────────────
# File generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_agent(spec: dict[str, Any], overwrite: bool = False, dry_run: bool = False) -> list[str]:
    """Generate all files for one agent. Returns list of created paths."""
    agent_id = spec["id"]
    role = spec["role"]
    created: list[str] = []

    agent_dir = AGENTS_ROOT / agent_id
    learned_dir = agent_dir / "learned"
    prompt_dir = AGENTS_ROOT / "prompts" / agent_id
    card_dir = AGENTS_ROOT / "registry" / "agent_cards"

    def _write(path: Path, content: str, label: str) -> None:
        if path.exists() and not overwrite:
            print(f"  SKIP (exists): {path.relative_to(REPO_ROOT)}")
            return
        if dry_run:
            print(f"  DRY-RUN: would write {path.relative_to(REPO_ROOT)}")
            created.append(str(path))
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content + "\n")
        print(f"  WRITE: {path.relative_to(REPO_ROOT)}")
        created.append(str(path))

    def _touch(path: Path) -> None:
        if path.exists() and not overwrite:
            return
        if dry_run:
            print(f"  DRY-RUN: would touch {path.relative_to(REPO_ROOT)}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        print(f"  TOUCH: {path.relative_to(REPO_ROOT)}")

    # SKILL.md — dedent to remove any common leading whitespace from template
    if role == "antagonist":
        skill_content = antagonist_skill_md(spec)
    else:
        skill_content = specialist_skill_md(spec)
    # Post-process: strip 8-space prefix from lines where textwrap.dedent failed
    # due to interpolated variables breaking the common-prefix detection.
    skill_lines = skill_content.splitlines()
    h2_correct = sum(1 for ln in skill_lines if ln.startswith("## "))
    h2_indented = sum(1 for ln in skill_lines if ln.startswith("        ## "))
    if h2_indented > 0 and h2_correct == 0:
        skill_content = "\n".join(
            ln[8:] if ln.startswith("        ") else ln for ln in skill_lines
        )
    _write(agent_dir / "SKILL.md", skill_content, "SKILL.md")

    # learned/
    _touch(learned_dir / "failure_patterns.jsonl")
    _touch(learned_dir / "strategies.jsonl")
    _write(learned_dir / "tool_prefs.yaml", tool_prefs_yaml(spec), "tool_prefs.yaml")

    # prompt
    _write(prompt_dir / "v1.0.0.md", prompt_md(spec), "v1.0.0.md")

    # agent card
    _write(card_dir / f"{agent_id}.yaml", agent_card_yaml(spec), "agent_card")

    return created


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FORGE agent scaffolds")
    parser.add_argument("--id", help="Agent ID (e.g. aerodynamics_specialist)")
    parser.add_argument("--role", choices=["specialist", "antagonist", "verifier", "tester",
                                            "command", "maintenance", "other"],
                        default="specialist")
    parser.add_argument("--domain", help="Full domain description")
    parser.add_argument("--domain-short", help="Short domain name (for templates)")
    parser.add_argument("--pair", help="Paired agent ID (antagonist ↔ specialist)")
    parser.add_argument("--status", default="planned",
                        choices=["planned", "mvp", "v1", "v2", "rd", "deprecated"])
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be created without writing")
    parser.add_argument("--batch", type=Path,
                        help="YAML manifest with list of agent specs")
    args = parser.parse_args()

    if args.batch:
        if not args.batch.exists():
            print(f"ERROR: Batch file not found: {args.batch}", file=sys.stderr)
            return 1
        with args.batch.open() as f:
            manifest = yaml.safe_load(f)
        agents = manifest.get("agents", [])
        total = 0
        for spec in agents:
            print(f"\nGenerating {spec['id']} ({spec.get('role', 'specialist')})...")
            generate_agent(spec, overwrite=args.overwrite, dry_run=args.dry_run)
            total += 1
        print(f"\nDone. Processed {total} agents.")
        return 0

    if not args.id:
        parser.error("--id is required (or use --batch)")

    spec: dict[str, Any] = {
        "id": args.id,
        "role": args.role,
        "domain": args.domain or f"{_title(args.id)} Domain",
        "status": args.status,
    }
    if args.domain_short:
        spec["domain_short"] = args.domain_short
    if args.pair:
        spec["pair"] = args.pair

    print(f"\nGenerating {args.id} ({args.role})...")
    generate_agent(spec, overwrite=args.overwrite, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
