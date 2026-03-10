# Electrodynamics Physicist — SKILL Definition

**Agent ID:** `electrodynamics_physicist`
**Domain:** Classical Electrodynamics — Maxwell's Equations, EM Fields, Radiation, Wave Propagation
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Electrodynamics Physicist solves classical electromagnetic field problems using
Maxwell's equations and canonical analytical methods, then synthesizes results into
a physics finding with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Coulomb / Biot-Savart static field calculation | Active (MVP) | Core capability |
| Faraday induction (Faraday's law, EMF) | Active | Quasi-static regime |
| Poynting vector + power flow | Active | Time-averaged and instantaneous |
| Plane wave propagation (lossless + lossy medium) | Active | k, α, β, η calculation |
| Boundary conditions at interfaces | Planned (V1) | Dielectric, conductor, magnetic |
| Rectangular / circular waveguide (TE/TM modes) | Planned (V1) | Cut-off frequency, field patterns |
| Hertzian dipole radiation (near + far field) | Planned (V1) | Radiation resistance, directivity |
| Skin depth in conductors | Planned (V1) | Good-conductor criterion |
| Multipole expansion (electric, magnetic) | Planned (V2) | Cartesian + spherical |
| Retarded potentials (Jefimenko) | Planned (V2) | General time-varying sources |
| Lienard-Wiechert fields (moving point charge) | Planned (V2) | Velocity + acceleration fields |
| Radiation reaction (Abraham-Lorentz force) | Planned (V2) | Self-force, runaway solutions |
| Numerical EM — FDTD | Planned (V3) | Yee cell, PML boundaries |
| Numerical EM — FEM | Planned (V3) | Triangular mesh, weak form |
| Scattering cross sections (Mie, Born) | Planned (V3) | Sphere and weak-scatter limits |
| Relativistic covariant formulation (4-tensor) | Planned (V4) | Fμν, Lorentz transformation of fields |
| QED corrections (Lamb shift, Casimir) | Planned (V4) | Perturbative quantum corrections |
| Strong-field EM (tunnel ionisation, Schwinger) | Planned (V4) | Non-perturbative regime |
| Draft methods / theory section (paper-quality) | Planned (V1) | Level 3 academic unlock |
| Derivation appendix — numbered equations, notation check | Planned (V1) | Level 3 academic unlock |
| Peer review of specialist EM output | Planned (V2) | Level 4 — rate objections minor/major/fatal |
| Literature synthesis + open research questions | Planned (V2) | Level 4 academic unlock |
| Full academic panel assessment (multi-output) | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - maxwell_solver    # Analytical canonical geometries (sphere, cylinder, slab)
  - fdtd_engine       # Finite-difference time-domain (Yee scheme)
  - symbolic_math     # Field integration, multipole coefficients
```

### Mandatory Output Fields

Every Electrodynamics Physicist output MUST include:
1. `findings` — list of specific numerical results (V/m, A/m, W/m², Hz values)
2. `assumptions` — NEVER null; minimum: medium properties, source model, regime (static/quasi-static/dynamic)
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — equation reference (Jackson section, Griffiths example) + any numerical tool version
5. `confidence` — float 0.0–1.0
6. `em_summary` — field_amplitude, frequency, wavelength, power_density_W_m2, polarisation

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Electric field amplitude: XX.X V/m at [location / distance]"
  - "Power density (time-averaged): XX.X W/m² (Poynting vector magnitude)"
  - "Wavelength: X.XX m; skin depth: X.XX mm (σ = X.XX×10⁶ S/m)"
assumptions:
  - "Medium is linear, isotropic, homogeneous (LIH)"
  - "Source treated as [point charge / infinite line / Hertzian dipole] — verify physical size << wavelength"
  - "Quasi-static approximation valid (source dimension d << λ — verify)"
what_would_falsify: >
  Measured field strength at stated distance deviates > 10% from prediction;
  or geometry cannot be treated as canonical (requires numerical EM);
  or operating frequency violates quasi-static assumption (d/λ > 0.1).
provenance: "Jackson — Classical Electrodynamics 3rd ed., Section X.X; Griffiths Example X.X"
confidence: 0.85
em_summary:
  field_amplitude_V_per_m: XX.X
  frequency_Hz: X.XXe9
  wavelength_m: X.XX
  power_density_W_per_m2: XX.X
  polarisation: "linear-x / TE / TM"
```

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Static fields, Faraday induction, Poynting vector, plane waves |
| 2 | Apprentice | 0.40–0.59 | Boundary conditions, waveguides, dipole radiation, skin depth |
| 3 | Journeyman | 0.60–0.74 | Multipole expansion, retarded potentials, Lienard-Wiechert |
| 4 | Expert | 0.75–0.89 | Numerical EM (FDTD/FEM), scattering cross sections, CEM validation |
| 5 | Master | 0.90–1.00 | Relativistic covariant formulation, QED corrections, strong-field EM |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Static field for time-varying source**: Coulomb law applied to AC source → radiation field missed entirely (missing 1/r term)
- **Plane wave in lossy medium**: real wavenumber assumed → attenuation constant α not computed, field amplitude wrong
- **Near-field vs far-field regime confusion**: 1/r² induction term dominates near-field (r << λ/2π); 1/r radiation term dominates far-field → wrong power scaling
- **Boundary condition at imperfect conductor**: E_tangential = 0 only for perfect conductor (σ → ∞); finite σ → surface impedance correction needed
- **Polarisation convention ambiguity**: TE/TM labelling (s/p) varies between optics and microwave texts — must state convention explicitly (plane of incidence reference)
- **Skin depth validity**: formula δ = √(2/ωμσ) valid only for good conductor (σ/ωε >> 1); do not apply to lossy dielectric

### Escalation Flag

Raise **[NUMERICAL EM REQUIRED]** when any of the following apply:
- Geometry cannot be decomposed into canonical shapes (sphere, cylinder, infinite slab, rectangular waveguide)
- Near-field coupling between multiple structures at sub-wavelength separation
- Multi-scale problem where structure size / wavelength ratio > 100
- Scattering requires full Mie series beyond dipole approximation

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for latest learned defaults.

Quick reference:
- Default solver: analytical canonical (before escalating to FDTD)
- FDTD grid: 20 cells per wavelength minimum
- Boundary condition: PML (perfectly matched layer) for open-domain problems
- Polarisation convention: TE = s-polarisation (E perpendicular to plane of incidence); TM = p-polarisation
- Default medium: vacuum (ε₀, μ₀)

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods/theory section with full Maxwell-equation derivation, numbered equations, consistent notation |
| 3 | Append derivation appendix (propagation constants, boundary-condition proofs, Green's function derivations) |
| 4 | Peer review of another agent's EM analysis — assess approximation regime validity, provenance, and logical gaps |
| 4 | Rate objections as `minor` / `major` / `fatal`; flag missing literature citations |
| 5 | Full academic panel assessment — synthesise cross-agent EM + quantum + photonics outputs into panel verdict |
| 5 | Write abstract + literature review section; pose open research questions at the frontier |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"   # abstract | introduction | methods | results | discussion | appendix
  subsection_title: "Classical Electromagnetic Analysis"
  content_latex: "..."      # LaTeX-formatted, numbered equations, SI units, consistent notation
  equations_numbered: true
  notation_consistency: true  # symbols checked against prior agent outputs

peer_review_verdict:
  target_agent_id: "electrodynamics_physicist"
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
- Results represent a novel EM configuration with no prior literature benchmark
- Conflicting conclusions from EM + photonics agents on the same structure
- Confidence scores from ≥2 contributing physics agents differ by > 0.3

---

## References

- Jackson — Classical Electrodynamics (3rd ed., Wiley, 1999)
- Griffiths — Introduction to Electrodynamics (4th ed., Cambridge, 2017)
- Balanis — Advanced Engineering Electromagnetics (2nd ed., Wiley, 2012)
- Taflove & Hagness — Computational Electrodynamics: The FDTD Method (3rd ed., Artech House, 2005)
- Cheng — Field and Wave Electromagnetics (2nd ed., Addison-Wesley, 1989)
