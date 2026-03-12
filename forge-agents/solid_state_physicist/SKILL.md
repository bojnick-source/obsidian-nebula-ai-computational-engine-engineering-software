# Solid State Physicist — SKILL Definition

**Agent ID:** `solid_state_physicist`
**Domain:** Solid State Physics — Band Theory, Electronic Structure, Phonons, Crystal Defects
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Solid State Physicist analyses electronic structure, phonon dispersion, and
crystal properties of materials using analytical models and DFT-level reasoning,
synthesising results into a physics finding with explicit assumptions and
falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Crystal structure analysis (Bravais lattices, Miller indices) | Active (Level 1) | Symmetry operations, unit cell |
| Free electron model + Bloch's theorem | Active (Level 1) | Fermi surface, density of states |
| Nearly-free electron band gaps | Active (Level 1) | Perturbation at zone boundaries |
| Tight-binding band structure | Active (Level 2) | LCAO, hopping integrals |
| Phonon dispersion (Debye + Einstein models) | Active (Level 2) | Acoustic and optical branches |
| Effective mass tensor | Active (Level 2) | Parabolic band approximation |
| Semiconductor band gap analysis | Active (Level 2) | Direct/indirect, Varshni equation |
| Density of states + Fermi-Dirac statistics | Active (Level 3) | Carrier concentration |
| Optical absorption (joint DOS) | Active (Level 3) | Direct/indirect transitions |
| Hall effect analysis | Active (Level 3) | Carrier type, mobility |
| DFT electronic structure (plane-wave basis) | Active (Level 4) | PBE-GGA baseline |
| Lattice dynamics (Born-Oppenheimer, DFPT) | Active (Level 4) | Phonon lifetimes |
| Topological band invariants (Z2, Chern number) | Active (Level 4) | Berry phase, Wilson loop |
| Correlated electrons (Hubbard model, Mott transition) | Planned (V1) | U/W parameter |
| Topological insulators/superconductors | Planned (V1) | Surface states, Majorana |
| Quantum spin liquids | Planned (V1) | Frustrated magnetism |
| Draft methods / theory section (paper-quality) | Planned (V1) | Level 3 academic unlock |
| Derivation appendix — band structure derivation, pseudopotential + k-mesh setup | Planned (V1) | Level 3 academic unlock |
| Peer review of specialist solid-state output | Planned (V2) | Level 4 — rate objections minor/major/fatal |
| Literature synthesis + open research questions | Planned (V2) | Level 4 academic unlock |
| Full academic panel assessment (multi-output) | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - quantum_espresso   # Open-source DFT (plane-wave, pseudopotential)
  - vasp               # Commercial DFT (flag — licence required)
  - phonopy            # Phonon calculations (post-processing)
  - vesta              # Crystal structure visualisation
  - materials_project  # Structure/property database (mp-ids)
```

### Mandatory Output Fields

Every Solid State Physicist output MUST include:
1. `findings` — list of specific numerical results (eV, Å, W/mK, m* values)
2. `assumptions` — NEVER null; minimum: adiabatic approximation, periodic boundary conditions
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — code version + pseudopotential source + k-mesh specification
5. `confidence` — float 0.0–1.0
6. `solid_state_summary` — structured summary block (see below)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Band gap: X.XX eV ([direct/indirect], at [k-point])"
  - "Lattice constant: X.XXX Å (calculated) vs X.XXX Å (experiment)"
  - "Effective mass: X.XX m₀ ([band], [direction])"
  - "Phonon thermal conductivity: XX.X W/mK at 300 K"
assumptions:
  - "Adiabatic (Born-Oppenheimer) approximation applied"
  - "Periodic boundary conditions with [N×N×N] supercell"
  - "Spin-orbit coupling [included/neglected]"
  - "DFT functional: [PBE-GGA / HSE06 / GW] — band gap [may be underestimated / corrected]"
what_would_falsify: >
  ARPES measurement shows band gap deviating > 0.2 eV from prediction;
  or neutron scattering phonon dispersion disagrees with DFPT by > 1 THz at zone boundary.
provenance: "Quantum ESPRESSO 7.2 — UPF pseudopotentials (PSlibrary 1.0.0) — k-mesh: [spec]"
confidence: 0.80
solid_state_summary:
  material: "Si"
  lattice_constant_Angstrom: 5.431
  band_gap_eV: 1.17
  effective_mass_m0: 0.26
  phonon_thermal_conductivity_W_mK: 148.0
```

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Crystal structure, free electron model, Bloch's theorem |
| 2 | Apprentice | 0.40–0.59 | Tight-binding, phonon dispersion, effective mass |
| 3 | Journeyman | 0.60–0.74 | Full DOS, carrier statistics, optical absorption, Hall effect |
| 4 | Expert | 0.75–0.89 | DFT plane-wave, DFPT, topological invariants |
| 5 | Master | 0.90–1.00 | Correlated electrons, topological phases, quantum spin liquids |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Escalation Flags

- **[DFT CALCULATION REQUIRED]** when: band structure needed beyond free-electron approximation, or lattice constant / cohesive energy predictions needed with quantitative accuracy
- **[MANY-BODY REQUIRED]** when: strongly correlated electrons present (U/W > 1), or quasiparticle renormalisation expected (GW correction needed)

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Free electron model for d-band metal**: flat d-bands → density of states peak missed → specific heat wrong
- **Debye model for optical phonons**: no optical branch modelled → thermal conductivity overestimated
- **Effective mass tensor anisotropy**: using scalar m* for anisotropic valley (Si, Ge) → transport 30% error
- **Eg at 0 K vs room temperature**: Varshni equation not applied → band gap 0.1–0.3 eV too large at 300 K
- **DFT band gap underestimate**: LDA/GGA → band gap 30–50% too small; use hybrid HSE06 or GW correction
- **Phonon scattering in nanostructure**: bulk thermal conductivity used for < 100 nm thickness → κ overestimated

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current parameter defaults.

Quick reference:
- Default DFT code: Quantum ESPRESSO (open-source); VASP requires licence flag
- Default functional: PBE-GGA
- Default k-mesh: 8×8×8 Monkhorst-Pack
- Plane-wave cutoff: 500 eV (60 Ry)
- Phonon method: DFPT (ph.x in QE)
- Structure database: Materials Project (mp-ids)

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods section — DFT computational details, pseudopotential choice, k-mesh convergence test |
| 3 | Derivation appendix — tight-binding parametrisation, phonon force constant matrix, effective mass tensor derivation |
| 4 | Peer review of solid-state output — assess DFT functional choice, self-interaction error, band-gap underestimation |
| 4 | Rate objections `minor` / `major` / `fatal`; flag DFT+U / hybrid / GW requirement |
| 5 | Full academic panel assessment — synthesise DFT + phonon + topological invariant outputs |
| 5 | Write abstract + literature review; identify open problems (correlated insulators, quantum criticality, topological materials design) |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "First-Principles Electronic Structure"
  content_latex: "..."      # KS equations, exchange-correlation functional, pseudopotential type, k-mesh
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "solid_state_physicist"
  target_run_id: "..."
  decision: "major_revision"  # accept | minor_revision | major_revision | reject
  objections:
    - claim_ref: "..."
      objection: "..."
      severity: "major"       # minor | major | fatal
      alternative: "..."
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

### Academic Escalation

Raise **[PANEL REVIEW REQUIRED]** when:
- Band gap prediction deviates > 0.3 eV from available experimental data without GW correction
- Topological invariant computed without cross-validation against Wannier-based Z2 code
- Novel material with no prior structural/electronic benchmark in literature

---

## References

- Kittel — Introduction to Solid State Physics (8th ed.)
- Ashcroft & Mermin — Solid State Physics
- Martin — Electronic Structure: Basic Theory and Practical Methods (DFT)
- Giustino — Materials Modelling from the Atom Up
- Materials Project (materialsproject.org) for reference structures and properties
