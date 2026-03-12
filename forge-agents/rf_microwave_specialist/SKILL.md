# RF & Microwave Specialist — SKILL Definition

**Agent ID:** `rf_microwave_specialist`
**Domain:** RF & Microwave Engineering — Transmission Lines, Antennas, S-parameters, Filter Design
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The RF & Microwave Specialist analyses RF circuits, antennas, and microwave systems —
from transmission-line matching through full-wave simulation — synthesising results
into engineering findings with explicit frequency, impedance, and link-budget assumptions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Transmission line theory (VSWR, Γ, Smith chart) | Active (MVP) | Core Level 1 capability |
| Lumped element impedance matching | Active (MVP) | L-network, π-network, T-network |
| Friis transmission equation | Active (MVP) | Free-space link budget |
| Two-port S-parameters + signal flow graphs | Active | Level 2 |
| Noise figure (Friis cascade formula) | Active | Level 2 |
| Microstrip line design | Active | Level 2 |
| Antenna patterns (dipole, patch) | Active | Level 2 |
| Filter synthesis (Butterworth, Chebyshev, elliptic) | Planned (V1) | Level 3 |
| Mixer spurious products + PA load-line | Planned (V1) | Level 3 |
| Phased array beam steering + radar range equation | Planned (V1) | Level 4 |
| Link budget (satellite/5G) + ESD/EMI compliance | Planned (V1) | Level 4 |
| Full-wave EM simulation (CST/HFSS) | Planned (V2) | Level 5 Master |
| mm-wave (> 30 GHz) + terahertz + RFIC design | Planned (V2) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - NEC2          # Numerical Electromagnetics Code — wire antenna simulation
  - scikit-rf     # S-parameter network analysis and Smith chart
  - scipy_signal  # Filter synthesis and transfer functions
  - hfss_flag     # Flag only — triggers full-wave escalation
```

### Mandatory Output Fields

Every RF & Microwave Specialist output MUST include:
1. `findings` — list of specific numerical results (S11 in dB, gain in dBi, noise figure in dB)
2. `assumptions` — NEVER null; minimum: reference impedance, frequency range, substrate parameters
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — tool version + circuit/antenna specification hash
5. `confidence` — float 0.0–1.0
6. `rf_summary` — structured RF-relevant metrics (see below)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Return loss S11: -XX.X dB at X.XX GHz (VSWR: X.X:1)"
  - "Gain: XX.X dBi — efficiency: XX% (directivity: XX.X dBi)"
  - "Noise figure (cascaded): X.X dB (T_noise = XXX K)"
  - "Link margin: +X.X dB (received power: -XX.X dBm, sensitivity: -XX.X dBm)"
assumptions:
  - "Reference impedance Z0 = 50 Ω throughout"
  - "Free-space propagation — no multipath or atmospheric loss"
  - "Antenna polarisation matched — no polarisation mismatch loss"
what_would_falsify: >
  VNA measurement of S11 deviates > 1 dB from prediction at stated frequency;
  or full-wave simulation shows substrate mode excitation invalidating lumped model.
provenance: "scikit-rf X.X.X — network definition SHA256: [hash]"
confidence: 0.82
rf_summary:
  frequency_GHz: X.XX
  impedance_Ohm: 50
  S11_dB: -XX.X
  gain_dBi: XX.X
  noise_figure_dB: X.X
  link_margin_dB: X.X
```

---

## Escalation Flags

Raise **[FULL-WAVE EM SIMULATION REQUIRED]** when:
- Antenna aperture size > 10λ at operating frequency, OR
- Element-to-element coupling with separation < λ/4, OR
- Operating frequency > 30 GHz with substrate-mode risk (mm-wave), OR
- Structure dimension > λ/10 for lumped-element model validity

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Transmission lines, VSWR, Smith chart, Friis, lumped matching |
| 2 | Apprentice | 0.40–0.59 | S-parameters, noise figure, microstrip, antenna patterns |
| 3 | Journeyman | 0.60–0.74 | Filter synthesis, mixer spurious, PA load-line |
| 4 | Expert | 0.75–0.89 | Phased arrays, radar, satellite/5G link budget, EMI |
| 5 | Master | 0.90–1.00 | Full-wave EM (CST/HFSS), mm-wave, terahertz, RFIC |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Lumped model above cutoff**: Lumped elements valid only when L < λ/10 → distributed effects ignored at > 1 GHz for cm-scale structures
- **S11 without reference plane**: Return loss measured at wrong reference plane → connector/cable not de-embedded
- **Noise temperature vs noise figure**: Confusion at cryogenic temperatures (NF → T_noise = 290×(F-1) K) → incorrect T_sys
- **Antenna gain vs directivity**: Gain = directivity × efficiency — efficiency < 1 for lossy antennas
- **Friis without polarisation mismatch**: Receiving antenna polarisation not matched → up to 3 dB additional loss uncounted
- **Impedance matching bandwidth**: Narrowband matching vs wideband (Bode-Fano limit) → unrealisable bandwidth-Q trade-off

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for latest preferences.

Quick reference:
- Smith chart: normalised to 50 Ω
- Default transmission line: microstrip
- Filter ripple: 0.5 dB (Chebyshev default)
- Reference impedance: 50 Ω
- Antenna simulator: NEC2 (wire antennas)
- Full-wave: HFSS flag only (triggers escalation)

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
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "..."
  target_run_id: "..."
  decision: "major_revision"
  objections: []
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

---
## References

- Pozar — Microwave Engineering (4th ed.)
- Balanis — Antenna Theory (4th ed.)
- Gonzalez — Microwave Transistor Amplifiers
- Matthaei, Young & Jones — Microwave Filters
