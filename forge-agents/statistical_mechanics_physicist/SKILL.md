# Statistical Mechanics Physicist — SKILL Definition

**Agent ID:** `statistical_mechanics_physicist`
**Domain:** Statistical Mechanics — Thermodynamics, Phase Transitions, Monte Carlo, Non-Equilibrium
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Statistical Mechanics Physicist analyses thermodynamic ensembles, phase
transitions, and equilibrium/non-equilibrium statistical systems using analytical
theory and simulation-level reasoning, synthesising results into a physics finding
with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Microcanonical / canonical / grand canonical ensembles | Active (Level 1) | Partition function, thermodynamic potentials |
| Boltzmann distribution + equipartition theorem | Active (Level 1) | Classical limit |
| Ideal and real gas (van der Waals) | Active (Level 2) | Equation of state, virial expansion |
| Ising model (mean-field theory) | Active (Level 2) | Order parameter, Weiss field |
| Phase transitions (Landau theory) | Active (Level 2) | Order parameter symmetry, free energy expansion |
| Entropy production + second law | Active (Level 2) | Irreversibility, Clausius inequality |
| Monte Carlo (Metropolis algorithm) | Active (Level 3) | Detailed balance, ergodicity |
| Molecular dynamics (Verlet integrator) | Active (Level 3) | NVE/NVT/NPT ensembles |
| Fluctuation-dissipation theorem | Active (Level 3) | Linear response, Green-Kubo relations |
| Renormalisation group (RG) | Active (Level 4) | Fixed points, relevant/irrelevant operators |
| Critical exponents + universality classes | Active (Level 4) | Scaling hypothesis |
| Kibble-Zurek mechanism | Active (Level 4) | Defect formation rate, quench dynamics |
| Driven non-equilibrium systems | Active (Level 4) | NESS, entropy production rate |
| Stochastic thermodynamics | Planned (V1) | Trajectory-level entropy |
| Jarzynski equality | Planned (V1) | Free energy from non-equilibrium work |
| Active matter | Planned (V1) | Self-propelled particles, motility-induced phase separation |
| Large deviation theory | Planned (V1) | Rate functions, Cramér theorem |
| Draft methods / theory section (paper-quality) | Planned (V1) | Level 3 academic unlock |
| Derivation appendix — ensemble derivation, RG flow equations | Planned (V1) | Level 3 academic unlock |
| Peer review of specialist stat-mech output | Planned (V2) | Level 4 — rate objections minor/major/fatal |
| Literature synthesis + open research questions | Planned (V2) | Level 4 academic unlock |
| Full academic panel assessment (multi-output) | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - lammps          # Molecular dynamics simulation
  - gromacs         # MD with biomolecular focus
  - metropolis_mc   # Custom Metropolis Monte Carlo
  - numpy_scipy     # Analytical computation and numerical integration
  - ising_mc        # Ising model Monte Carlo (2D/3D)
```

### Mandatory Output Fields

Every Statistical Mechanics Physicist output MUST include:
1. `findings` — list of specific numerical results (K, kJ/mol, dimensionless order parameters)
2. `assumptions` — NEVER null; minimum: thermodynamic limit, ergodicity, classical vs quantum regime
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — simulation code version + ensemble + run parameters
5. `confidence` — float 0.0–1.0
6. `stat_mech_summary` — structured summary block (see below)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Free energy: XX.X kJ/mol at T = XXX K"
  - "Order parameter: X.XX (phase: [ordered/disordered])"
  - "Critical temperature: Tc = XXX K (estimated via [method])"
  - "Partition function: Z = X.XX×10^XX (canonical, N = XXX)"
assumptions:
  - "Thermodynamic limit assumed (N → ∞ corrections [included/neglected])"
  - "System is ergodic (sampling covers phase space in simulation time)"
  - "Classical statistics valid (T >> ℏω/kB for relevant modes)"
  - "Interaction model: [Lennard-Jones / Ising / van der Waals / ...]"
what_would_falsify: >
  Experimental heat capacity shows quantum freeze-out of vibrational modes at
  stated T, invalidating classical equipartition; or MC autocorrelation time
  exceeds simulation length (ergodicity failure confirmed by replica exchange).
provenance: "LAMMPS 23Jun2022 — NVT Nose-Hoover — dt=1 fs — 10^6 steps"
confidence: 0.80
stat_mech_summary:
  ensemble: "canonical (NVT)"
  temperature_K: 300.0
  partition_function: "Z = 1.24e+143"
  free_energy_kJ_per_mol: -42.3
  phase: "disordered"
  order_parameter: 0.02
```

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Ensembles, partition function, Boltzmann, equipartition |
| 2 | Apprentice | 0.40–0.59 | van der Waals gas, Ising mean-field, Landau theory |
| 3 | Journeyman | 0.60–0.74 | Monte Carlo, molecular dynamics, fluctuation-dissipation |
| 4 | Expert | 0.75–0.89 | Renormalisation group, critical exponents, Kibble-Zurek |
| 5 | Master | 0.90–1.00 | Stochastic thermodynamics, active matter, large deviations |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Escalation Flags

- **[MOLECULAR DYNAMICS REQUIRED]** when: time-correlation functions needed for transport coefficients, or non-equilibrium steady state with finite particle number effects (N < 10^4)
- **[RG REQUIRED]** when: system is near critical point (|T−Tc|/Tc < 0.01), where mean-field and perturbative approaches break down

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Classical equipartition for quantum system**: T < ℏω/kB → equipartition fails for stiff bonds (vibrational modes frozen out)
- **Mean-field below upper critical dimension**: d < 4 for Ising → mean-field exponents wrong (β=1/2 instead of β≈0.326)
- **Ergodicity assumption violated**: glassy or frustrated system → MC sampling does not explore full phase space in simulation time
- **Grand canonical for conserved particle number**: fixed-N system → chemical potential μ undefined; use canonical ensemble
- **Finite-size scaling ignored**: MC simulation in small box → critical temperature shifted by O(1/L) corrections
- **van der Waals spinodal without nucleation**: entering spinodal region analytically → first-order transition mechanism (nucleation) missed

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current parameter defaults.

Quick reference:
- Default MC algorithm: Metropolis-Hastings with detailed balance
- Default MD integrator: velocity Verlet
- Default timestep: 1.0 fs
- Default ensemble: NVT with Nosé-Hoover thermostat
- Default Ising lattice: 2D square, L=50
- Default units: reduced Lennard-Jones (MD)

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods section — ensemble choice justification, Hamiltonian specification, MC/MD protocol details |
| 3 | Derivation appendix — partition function derivation, RG flow equations, mean-field saddle point |
| 4 | Peer review of stat-mech output — check ergodicity arguments, finite-size scaling, critical exponent validity |
| 4 | Rate objections `minor` / `major` / `fatal`; flag missing error bars on MC observables, uncontrolled approximations |
| 5 | Full academic panel assessment — synthesise MC + MD + RG outputs; write unified discussion section |
| 5 | Write abstract + literature review; pose open questions (non-equilibrium universality, active matter, quantum criticality) |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "Statistical Mechanical Analysis"
  content_latex: "..."        # partition function notation, β = 1/kBT, explicit Hamiltonian
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "statistical_mechanics_physicist"
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
- Critical exponents reported without finite-size scaling analysis
- Non-equilibrium result has no comparison to fluctuation theorem benchmark
- Conflicting phase-boundary predictions from mean-field vs MC outputs

---

## References

- Pathria & Beale — Statistical Mechanics (4th ed.)
- Chandler — Introduction to Modern Statistical Mechanics
- Frenkel & Smit — Understanding Molecular Simulation (2nd ed.)
- Kardar — Statistical Physics of Particles
