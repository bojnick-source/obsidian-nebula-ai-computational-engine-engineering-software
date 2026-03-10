# Quantum Mechanics Physicist — SKILL Definition

**Agent ID:** `quantum_mechanics_physicist`
**Domain:** Quantum Mechanics Physics — Schrödinger Equation, Perturbation Theory, Quantum States
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Quantum Mechanics Physicist solves quantum mechanical problems analytically and
numerically — from single-particle eigenvalue problems through many-body perturbation
theory — synthesising results into physics findings with explicit approximation
assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Time-independent Schrödinger equation (particle in box, HO, H atom) | Active (MVP) | Core Level 1 capability |
| Uncertainty principle + expectation values | Active (MVP) | ⟨x⟩, ⟨p⟩, Δx·Δp ≥ ℏ/2 |
| Time-dependent perturbation theory + Fermi's golden rule | Active | Level 2 |
| Angular momentum + spin (L, S, J coupling) | Active | Level 2 |
| WKB approximation | Active | Level 2 |
| Variational method + Hartree-Fock | Planned (V1) | Level 3 |
| Density functional theory (DFT) basics | Planned (V1) | Level 3 |
| Born approximation + scattering cross-section | Planned (V1) | Level 3 |
| Many-body perturbation theory (MBPT) + path integrals | Planned (V1) | Level 4 |
| Dirac equation (relativistic QM) | Planned (V1) | Level 4 |
| Quantum field theory (second quantisation) | Planned (V2) | Level 5 Master |
| Topological phases of matter | Planned (V2) | Level 5 Master |
| Non-equilibrium quantum systems | Planned (V2) | Level 5 Master |
| Draft methods / theory section (paper-quality) | Planned (V1) | Level 3 academic unlock |
| Derivation appendix — Hamiltonian specification, perturbation series | Planned (V1) | Level 3 academic unlock |
| Peer review of specialist QM output | Planned (V2) | Level 4 — rate objections minor/major/fatal |
| Literature synthesis + open research questions | Planned (V2) | Level 4 academic unlock |
| Full academic panel assessment (multi-output) | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - finite_difference_1D    # Numerical Schrödinger solver (1D)
  - pyscf                   # HF and DFT electronic structure
  - scipy_linalg            # Matrix diagonalisation for eigenvalue problems
  - sympy                   # Symbolic operator algebra
```

### Mandatory Output Fields

Every Quantum Mechanics Physicist output MUST include:
1. `findings` — list of specific numerical results (energy eigenvalues in eV, transition rates, uncertainty products)
2. `assumptions` — NEVER null; minimum: potential model, dimensionality, coupling regime
3. `what_would_falsify` — specific condition that would invalidate the analysis
4. `provenance` — solver version + Hamiltonian specification hash
5. `confidence` — float 0.0–1.0
6. `qm_summary` — structured physics-relevant metrics (see below)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Ground state energy: XX.XX eV (analytical: XX.XX eV)"
  - "First excited state: XX.XX eV — transition energy ΔE = X.XX eV"
  - "Transition rate (Fermi's golden rule): X.XXe+XX s⁻¹"
  - "Uncertainty product Δx·Δp = X.XX ℏ (minimum uncertainty: 0.50 ℏ)"
assumptions:
  - "Single-particle Hamiltonian — electron-electron interaction neglected"
  - "Non-relativistic approximation valid (v/c << 1)"
  - "Born-Oppenheimer approximation: nuclei treated as fixed"
what_would_falsify: >
  Spectroscopic measurement of transition frequency deviates > 1% from prediction;
  or many-body calculation shows electron correlation energy > 10% of total energy.
provenance: "PySCF X.X — Hamiltonian specification SHA256: [hash]"
confidence: 0.85
qm_summary:
  system: "hydrogen atom / harmonic oscillator / [system name]"
  energy_eigenvalues_eV: [E0, E1, E2]
  wavefunction_description: "1s ground state — nodeless, spherically symmetric"
  transition_rate_per_s: null
  uncertainty_product: 0.50
```

---

## Escalation Flags

Raise **[MANY-BODY CALCULATION REQUIRED]** when:
- System has > 2 interacting particles with Coulomb coupling, OR
- Electron correlation energy is expected to exceed 10% of total energy (beyond Hartree-Fock), OR
- Heavy atom (Z > 40) requires spin-orbit coupling beyond LS scheme

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Schrödinger eq., particle in box, HO, H atom, uncertainty principle |
| 2 | Apprentice | 0.40–0.59 | Time-dependent perturbation theory, Fermi's golden rule, angular momentum, WKB |
| 3 | Journeyman | 0.60–0.74 | Variational method, Hartree-Fock, DFT, Born approximation |
| 4 | Expert | 0.75–0.89 | MBPT, path integral formulation, Dirac equation |
| 5 | Master | 0.90–1.00 | QFT (second quantisation), topological phases, non-equilibrium systems |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Classical turning point**: WKB applied in classically forbidden region without connection formula → transmission coefficient wrong
- **Degenerate perturbation without proper basis**: Off-diagonal matrix elements present → first-order energy correction wrong
- **Spin-orbit coupling ignored**: Heavy atom (Z > 40) → LS coupling breaks down; jj coupling needed
- **Born approximation at low energy**: Strong potential → unitarity violated; optical theorem check needed
- **Non-normalised wavefunction**: Probability density integral ≠ 1 → all expectation values wrong
- **Harmonic oscillator beyond linear**: Large-amplitude oscillation → anharmonic correction ΔE ~ ℏω(n²) ignored

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for latest preferences.

Quick reference:
- Default Schrödinger solver: finite_difference_1D
- Default basis set: cc-pVDZ (for DFT/HF)
- Default DFT functional: B3LYP
- Energy units: eV; length units: Angstrom
- Perturbation order: first and second

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods/theory section — Hamiltonian definition, basis choice, perturbation order, Dirac notation throughout |
| 3 | Derivation appendix — explicit perturbation series, angular momentum algebra, WKB connection formulae |
| 4 | Peer review of another agent's QM analysis — check regime validity (relativistic, many-body), logical consistency of approximations |
| 4 | Rate objections `minor` / `major` / `fatal`; flag missing corrections (spin-orbit, electron correlation, radiative) |
| 5 | Full academic panel assessment synthesising QM + solid-state + QED outputs; assign unified confidence verdict |
| 5 | Write abstract + literature review; identify open problems (strongly correlated systems, decoherence, topological phases) |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "Quantum Mechanical Treatment"
  content_latex: "..."         # Dirac notation, numbered equations, explicit Hamiltonian
  equations_numbered: true
  notation_consistency: true   # ket / bra consistent, operators hatted throughout

peer_review_verdict:
  target_agent_id: "quantum_mechanics_physicist"
  target_run_id: "..."
  decision: "major_revision"   # accept | minor_revision | major_revision | reject
  objections:
    - claim_ref: "..."
      objection: "..."
      severity: "major"        # minor | major | fatal
      alternative: "..."
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

### Academic Escalation

Raise **[PANEL REVIEW REQUIRED]** when:
- Ground-state energy differs > 5% from published benchmark values
- Conflicting energy eigenvalues from QM + DFT agents on same system
- Novel quantum system with no published comparison data

---

## References

- Griffiths — Introduction to Quantum Mechanics (3rd ed.)
- Sakurai & Napolitano — Modern Quantum Mechanics
- Cohen-Tannoudji — Quantum Mechanics Vols 1–2
- Szabo & Ostlund — Modern Quantum Chemistry (HF/DFT)
