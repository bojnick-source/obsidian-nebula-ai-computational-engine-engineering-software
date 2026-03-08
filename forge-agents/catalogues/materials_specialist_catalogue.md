# Materials Specialist — Catalogue

## 5 Canonical Examples

### Example 1: Aerospace Bracket Material Selection Using Ashby Charts
**Input:** Structural bracket for UAV airframe, mass-critical, fatigue loading, 3g sustained + 12g peak, operating temperature −40 °C to +85 °C, unit cost target < $50/part.
**Agent behaviour:** Constructed performance indices for strength-limited design (σ_f^(2/3)/ρ for plate bending), plotted candidate materials on strength–density Ashby chart, applied cost overlay, screened against fatigue endurance ratio (σ_e/σ_UTS > 0.4), flagged CFRP as dominant but noted tooling cost cliff, recommended Al 7075-T651 for volumes < 500 units with CFRP re-evaluation at scale.
**Output:** 7075-T651 selected; σ_UTS = 572 MPa, ρ = 2.81 g/cm³, M = σ^(2/3)/ρ = 2.89 (GPa^(2/3))/(g/cm³); estimated 34% mass saving vs 304 SS baseline.
**Why exemplary:** Index formulation preceded chart lookup; cost envelope was quantified not qualitative; MMPDS provenance cited for allowables (A-basis, 95%/99% confidence).

### Example 2: Thermal Interface Material Optimisation for Power Electronics
**Input:** GaN half-bridge module, 35 W dissipation, junction-to-case thermal resistance must be ≤ 0.8 K/W, bond-line thickness 50–200 µm, rework required.
**Agent behaviour:** Ranked TIMs by thermal conductivity k vs compliance (Young's modulus E), applied Fourier conduction R = BLT/(k·A), screened for pump-out risk at 125 °C using creep data, flagged phase-change materials (PCMs) for rework compliance, computed sensitivity ∂R/∂BLT to quantify assembly tolerance impact.
**Output:** Bergquist GP3000 phase-change pad selected; k = 3.0 W/(m·K), BLT = 75 µm target, R_TIM = 0.06 K/W. Total junction-to-ambient margin 0.14 K/W positive.
**Why exemplary:** BLT sensitivity analysis surfaced assembly process risk; rework requirement drove material class choice before thermal optimisation.

### Example 3: Corrosion-Compatible Fastener Selection for Marine Environment
**Input:** Aluminium 6061-T6 structure with 316 SS fasteners in salt-fog environment (ASTM B117), service life 10 years, no painting budget.
**Agent behaviour:** Identified galvanic series incompatibility (316 SS noble vs Al 6061 active, ΔV ≈ 0.8 V), computed galvanic current density using mixed-potential theory, evaluated titanium Grade 5 (ΔV ≈ 0.1 V vs Al), Monel, and anodised Al alternatives, recommended Ti-6Al-4V fasteners with Alodine-1200 contact surface treatment.
**Output:** Ti-6Al-4V A286 equivalents selected; galvanic couple ΔV < 0.15 V; annual corrosion allowance 12 µm/year vs 340 µm/year for original 316 SS pairing.
**Why exemplary:** Mixed-potential theory applied quantitatively; galvanic current estimated from area ratio (cathode/anode = 15:1 worst case), not just table lookup.

### Example 4: CALPHAD Phase Diagram Consultation for Weld Filler Selection
**Input:** Dissimilar weld between Inconel 718 and 304L SS, service at 650 °C, sigma-phase embrittlement concern.
**Agent behaviour:** Queried Thermo-Calc TCNI9 database for Fe-Ni-Cr-Nb-Mo system, computed equilibrium phase fractions at 600–750 °C, identified sigma phase stability window (30–55% Cr equivalent), evaluated ERNiCrMo-3 vs ERNiCrFe-7 fillers, recommended post-weld heat treatment 720 °C/8 h + 620 °C/8 h to dissolve Laves phase.
**Output:** ERNiCrMo-3 filler selected; sigma phase suppressed by dilution to Cr_eq < 28%; PWHT protocol reduces Laves from 4.2 vol% to < 0.3 vol%.
**Why exemplary:** Phase fraction vs temperature computed from thermodynamic database, not estimated; PWHT rationale tied to kinetic TTT data.

### Example 5: High-Temperature Polymer Bearing Selection
**Input:** Bushing in UAV servo mechanism, 180 °C continuous, 220 °C excursion, dry-running, PV limit < 0.35 MPa·m/s, dimensional tolerance ±25 µm.
**Agent behaviour:** Applied PV limit screening across PTFE, PEEK, PAI (Torlon), and PBI grades, cross-referenced continuous use temperature vs creep modulus at 180 °C, eliminated PTFE (creep), PEEK-unfilled (PV marginal), selected Torlon 4301 (PAI + PTFE/graphite), verified thermal expansion mismatch with aluminium housing (ΔαΔT = 14 ppm/K × 60 K = 0.84 µm/mm).
**Output:** Torlon 4301 selected; PV_limit = 0.52 MPa·m/s (margin 49%); dimensional change at 220 °C = 21 µm (within ±25 µm tolerance).
**Why exemplary:** Thermal expansion mismatch computed against tolerance band; creep modulus at temperature (not room temperature) used for PV limit.

## Thinking Parameters

### Primary Questions (ask before every task)
1. What is the dominant failure mode for this application — fracture, fatigue, corrosion, creep, or wear — and does it govern material selection ahead of stiffness or strength?
2. What is the manufacturing route, and does it constrain material forms (wrought, cast, additive) or processing temperatures?
3. What is the operating environment (temperature range, chemical exposure, radiation), and how does it degrade material properties over service life?
4. What are the relevant performance indices (Ashby M), and can I derive them from first principles for this loading mode?
5. Is there a traceable, auditable data source for the allowables (MMPDS, MIL-HDBK-5, manufacturer data sheet with lot traceability), and what statistical basis applies (A-basis, B-basis, S-basis)?

### Domain Priors
- Property data scatter is 10–30% for metals, 20–50% for composites; always identify the statistical basis (A/B/S) before comparing to requirements.
- Corrosion is rarely a material property problem alone — it is a system/environment problem; surface treatment, sealing, and galvanic compatibility must be evaluated together.
- CALPHAD databases are semi-empirical; predictions outside assessed composition ranges should be treated as indicative, not definitive — validate against experimental literature.
- High-temperature polymers lose 30–50% of room-temperature modulus by their rated continuous use temperature; use elevated-temperature data.
- Ashby charts rank materials; they do not select them. Constraints (cost, availability, regulatory approval) eliminate candidates before index optimisation.
- Fatigue endurance ratios (σ_e/σ_UTS) vary by material class: steels ~0.5, aluminium ~0.35, titanium ~0.45, composites load-direction-dependent.

### Metacognitive Flags
| Signal | Trigger condition | Action |
|---|---|---|
| Data provenance ambiguity | Property value cited without source or statistical basis | Request MMPDS/MIL-HDBK section number or manufacturer cert; note as unverified |
| Environmental degradation gap | Temperature or chemical environment not addressed in property screening | Flag explicitly; request environmental test data or apply knock-down factor |
| Manufacturing process conflict | Selected material incompatible with required joining or finishing process | Re-screen from manufacturing-constraint-first perspective |
| Galvanic couple risk | Two dissimilar metals in wet/salt environment without > 0.3 V EMF check | Run galvanic series check; compute area ratio and estimate corrosion current |
| CALPHAD extrapolation | Composition near edge of assessed database range | Flag uncertainty; recommend experimental validation (DSC, XRD) |
| Single-source allowable | All property data from one supplier datasheet | Recommend cross-check against independent database (CES Granta, ASM) |

## Dead Feedback — Common Failure Modes

| Failure Mode | Symptom | Root Cause | Correction |
|---|---|---|---|
| Index reversal | Heavier material selected despite mass-criticality | Performance index computed for wrong loading mode (tension vs bending) | Re-derive index from first principles for actual loading geometry |
| Room-temperature creep neglect | Polymer bearing fails after 200 hours at rated temperature | Creep modulus at operating temperature not checked | Use isochronous stress-strain curves at T_operating, not room-temperature E |
| Galvanic neglect | Aluminium structure corrodes at fastener holes within 18 months | Galvanic couple not evaluated; ΔV not checked | Apply galvanic series; compute area ratio; mandate surface treatment |
| A-basis/B-basis confusion | Structural margin appears positive but fails statistically | B-basis used where A-basis required by spec | Confirm statistical basis required by standard; re-margin with correct value |
| CALPHAD blindspot | Weld HAZ cracks despite correct filler selection | Phase stability checked at equilibrium; kinetic TTT not consulted | Check CCT/TTT diagrams; specify cooling rate control in weld procedure |

## Skill Refinements (v1.0 → next)
- What works well: Ashby index derivation from first principles, galvanic couple analysis, CALPHAD phase fraction interpretation, MMPDS provenance tracking.
- What needs improvement: Composite CLT integration (fibre angle optimisation currently outsourced to structural specialist), additive manufacturing microstructure prediction, tribological wear modelling (Archard equation application).
- Proposed v1.1 additions: Integrate Materials Project API queries for novel intermetallic screening; add Weibull modulus estimation for ceramics and brittle composites; link to CALPHAD TTT diagram generation workflow.

## Theoretical Physics Foundations

**Crystal Field Theory and Electronic Structure.** The mechanical and optical properties of materials arise fundamentally from electronic structure. In transition metal compounds, crystal field splitting Δ_o (octahedral) or Δ_t (tetrahedral) determines whether d-electrons occupy bonding or antibonding states. For corrosion resistance in stainless steels, the passivation layer forms when Cr content exceeds ~12 wt%, producing a Cr₂O₃ film whose thermodynamic stability is described by the Ellingham diagram: ΔG°_f(Cr₂O₃) = −1128 kJ/mol at 298 K, more negative than ΔG°_f(Fe₂O₃) = −824 kJ/mol, driving selective Cr oxidation.

**Dislocation Mechanics and Plastic Deformation.** Plastic deformation is mediated by dislocation motion. The Taylor hardening relation gives the yield stress increment from dislocation density ρ_d: Δσ = αGbρ_d^(1/2), where G is shear modulus, b is the Burgers vector magnitude (~2.5 Å for FCC metals), and α ≈ 0.3–0.5 is a geometrical constant. Strengthening mechanisms (solid solution, precipitation, grain boundary Hall-Petch: σ_y = σ_0 + k_y·d^(−1/2)) all act by impeding dislocation glide. The Orowan bypass stress for precipitate hardening is τ = Gb/(L − 2r), where L is inter-precipitate spacing and r is precipitate radius. This governs the peak-aging condition in Al 2xxx and 7xxx alloys and Ni superalloys.

**Bonding Types and Property Correlations.** The nature of interatomic bonding determines the property envelope of a material class. Metallic bonding (non-directional, electron-gas mediated) gives ductility and electrical conductivity. Covalent bonding (directional, high bond energy ~350–700 kJ/mol) gives high hardness and high melting point (diamond: E = 1050 GPa). Ionic bonding produces brittle, electrically insulating ceramics with high compressive strength but low K_IC (~1–3 MPa·m^(1/2) vs steel ~50–100 MPa·m^(1/2)). Mixed bonding in intermetallics (e.g., Ni₃Al γ′ phase) gives anomalous yield stress increase with temperature — a key feature of superalloy design.

**Fracture Mechanics.** Linear elastic fracture mechanics (LEFM) governs crack propagation when the plastic zone r_p = (1/2π)(K_I/σ_y)² is small relative to crack size. The stress intensity factor K_I = Yσ√(πa) determines crack driving force; fracture occurs when K_I = K_IC. Fatigue crack growth follows Paris's law: da/dN = C(ΔK)^m, where m ≈ 2–4 for metals, C is material/environment dependent. The threshold ΔK_th determines whether a crack of given size is dormant. For damage-tolerant design, inspection intervals are derived by integrating Paris's law from initial detectable crack size a_0 to critical size a_c.

**Thermodynamics of Phase Equilibria.** The Gibbs free energy of mixing ΔG_mix = ΔH_mix − TΔS_mix determines phase stability. CALPHAD (CALculation of PHAse Diagrams) parametrises the Gibbs energy of each phase using Redlich-Kister polynomials and optimises interaction parameters against experimental data. Phase boundaries are computed from the common tangent construction (equal chemical potentials μ_i in coexisting phases). Spinodal decomposition occurs when ∂²G/∂c² < 0, driving spontaneous composition fluctuation without nucleation — the basis of Cu-Ni-based spinodal alloys and some permanent magnet microstructures.

## Mathematical Framework

**Ashby Performance Indices.** For a beam of given stiffness and minimum mass: M = E^(1/2)/ρ. For strength-limited plate: M = σ_f^(2/3)/ρ. For fracture-limited design: M = K_IC/ρ. For thermal shock resistance: M = σ_f·λ/(Eα), where λ is thermal conductivity and α is thermal expansion coefficient. These indices are derived by eliminating the free geometric variable from the objective function subject to the performance constraint, yielding a slope on the log-log Ashby chart: log(σ) = (p/q)·log(ρ) + const, where M = σ^(p/q)/ρ.

**Pareto Fronts and Multi-Objective Optimisation.** When two performance indices conflict (e.g., stiffness E and thermal conductivity λ), no single material maximises both. The Pareto front is the set of non-dominated candidates: material A dominates B if A ≥ B on all objectives and A > B on at least one. Weighted-sum scalarisation: M_combined = w₁·M₁ + w₂·M₂ converts multi-objective to single-objective but is sensitive to weighting. Tchebycheff scalarisation min_x max_i[w_i(M_i* − M_i(x))] is more robust to non-convex Pareto fronts.

**Constraint-Based Screening.** Materials selection proceeds as: (1) Translation — identify function, objective, constraints, free variables; (2) Screening — eliminate all materials violating hard constraints (T_max > T_operating, K_IC > K_IC_min); (3) Ranking — sort survivors by performance index; (4) Documentation — verify data provenance and manufacturing compatibility. The screening step is Boolean; the ranking step is continuous optimisation over a discrete set.

**Diffusion and Kinetics.** Fick's second law governs diffusion-controlled processes: ∂c/∂t = D·∇²c. The diffusion coefficient follows Arrhenius: D = D₀·exp(−Q_d/RT). Carburisation depth scales as x ~ √(Dt). For precipitation hardening, the time to peak hardness scales as t_peak ~ exp(Q/RT), setting the aging temperature-time trade-off. TTT diagram noses occur where the product of nucleation rate and growth rate is maximised.

**Weibull Statistics for Brittle Materials.** Ceramic failure probability: P_f = 1 − exp[−(σ/σ_0)^m · V/V₀], where m is the Weibull modulus (m = 5–10 for ceramics, 20–30 for hardmetals), σ_0 is characteristic strength, V is specimen volume. Low m indicates high scatter; high m indicates reliable material. Size scaling: σ_2/σ_1 = (V₁/V₂)^(1/m). This is critical for ceramic bearing and cutting tool life prediction.

## Historical Context

- **1863** — Henry Clifton Sorby demonstrates optical metallography on polished and etched steel sections; first quantitative microstructure observation.
- **1870s** — Gibbs formulates thermodynamics of heterogeneous systems; phase rule: F = C − P + 2.
- **1900** — Roberts-Austen publishes first Fe-C binary phase diagram based on thermal analysis.
- **1920** — Griffith derives fracture energy criterion for brittle solids: G_c = 2γ_s (surface energy).
- **1950** — Taylor formulates dislocation density hardening relationship.
- **1956** — Irwin introduces stress intensity factor K and K_IC concept; LEFM established.
- **1970s** — CALPHAD methodology formalised by Kaufman and Bernstein; Thermo-Calc development begins at KTH Stockholm.
- **1975** — Nd-Fe-B and SmCo rare-earth permanent magnets discovered; materials property space expands dramatically.
- **1985** — Michael Ashby publishes Cambridge Engineering Selector; systematic Ashby chart methodology for materials selection.
- **1989** — Ashby's "Materials Selection in Mechanical Design" (1st ed.) formalises performance index approach.
- **1996** — Materials Project computational database project initiated at MIT/LBNL, based on DFT high-throughput calculations.
- **2000s** — High-throughput DFT screening (AFLOW, Materials Project) computes properties for 10⁵–10⁶ hypothetical compounds.
- **2011** — ICSD (Inorganic Crystal Structure Database) surpasses 150,000 entries.
- **2020s** — Machine learning interatomic potentials (MLIP, M3GNet, CHGNet) enable DFT-accuracy MD at classical MD cost.

## Current State of the Art (2025–2026)

**Databases.** Materials Project (materialsproject.org) contains >140,000 inorganic compounds with DFT-computed formation energies, band gaps, elastic tensors, and phonon spectra. AFLOW (aflow.org) hosts >3.5 million compounds. ICSD holds >220,000 experimentally characterised crystal structures. Granta CES EduPack/Selector remains the industry standard for engineering property data with full provenance.

**Computational Tools.** VASP, Quantum ESPRESSO, and ABINIT are the dominant plane-wave DFT codes. Thermo-Calc with CALPHAD databases (TCFE, TCNI, TTAL) is standard for phase equilibria in engineering alloys. LAMMPS with neural network potentials (NNP) enables atomistic simulations at 10⁹ atom scales. CHGNet and M3GNet (2023) are universal MLIP architectures trained on Materials Project data, achieving DFT-level formation energy prediction at 10⁶× lower cost.

**Additive Manufacturing Microstructure.** AM process-structure-property linkage is an active research frontier. Integrated computational materials engineering (ICME) chains DFT → CALPHAD → phase-field (MOOSE/PRISMS) → crystal plasticity FEM to predict AM microstructure from process parameters. The 2024 AM benchmarks (NIST AM-Bench 2022 dataset) provide ground-truth data for model validation.

**Experimental High-Throughput.** Combinatorial sputtering and automated characterisation (XRD, nanoindentation arrays) enable experimental screening of 100s of compositions per week. Self-driving labs (Acceleration Consortium, Toronto; Emerald Cloud Lab) couple Bayesian optimisation with robotic experimentation for closed-loop materials discovery. First demonstrations of autonomous alloy optimisation reaching target hardness in <30 experimental iterations (2024).
