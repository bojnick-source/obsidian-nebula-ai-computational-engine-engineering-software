# Aerodynamics Specialist Agent — Catalogue

## 5 Canonical Examples

### Example 1: UAV Wing Section Selection via XFOIL Analysis
**Input:** Fixed-wing UAV, cruise speed 25 m/s, wing area 0.6 m², AR = 8, target cruise L/D > 20, Re ≈ 3 × 10⁵, no high-lift devices.
**Agent behaviour:** Queries NACA 4-digit and Eppler families for Re = 3 × 10⁵; runs XFOIL analysis at α = −4° to 14° for NACA 2412, NACA 4412, Eppler E387, and Selig S1223; extracts Cl/Cd polar at target Cl = 0.8 (cruise); identifies E387 as peak L/D = 48 at Cl = 0.8 vs NACA 4412 L/D = 34; checks Cm at quarter-chord (−0.09 for E387 — acceptable for tail-volume trimming); verifies stall character (gradual for E387, abrupt for S1223 — rejected); reports transition location xtr/c = 0.23 (upper surface) using Michel criterion in XFOIL.
**Output:** Selected E387 airfoil, cruise L/D = 48, Cl_cruise = 0.81, Cd = 0.0168, xtr/c = 0.23, Cm_c/4 = −0.09. Whole-aircraft L/D estimated 18 after accounting for fuselage and interference drag (10% increment).
**Why exemplary:** Multi-candidate systematic XFOIL sweep with explicit stall character evaluation; Cm documented for stability analysis handoff.

### Example 2: Propeller Blade Element Momentum Analysis
**Input:** 2-bladed propeller, diameter 0.5 m, rotational speed 4500 RPM, flight speed 20 m/s, target static thrust > 80 N, NACA 4412 blade sections.
**Agent behaviour:** Divides blade into 20 radial stations from r/R = 0.15 to 1.0; applies combined BEM theory with Prandtl tip loss factor F = (2/π) × arccos(exp(−B(R−r)/(2r sin φ))) at each station; iterates on axial induction a and tangential induction a' using standard BEM loop (Δa < 0.001 convergence); computes local Re at each station (Re = V_rel × c(r) / ν); uses XFOIL-derived Cl(α), Cd(α) for NACA 4412 at local Re; integrates thrust dT = ρ Ω r² × 4πr F × a'(1+a') and torque dQ; applies Prandtl hub loss correction; outputs thrust and torque vs advance ratio J.
**Output:** Static thrust T = 87.3 N at J = 0 (V_inf = 0), cruise thrust 41 N at J = 0.53 (V = 20 m/s, 4500 RPM), propulsive efficiency η = 0.76, power absorbed 1.08 kW.
**Why exemplary:** Full BEM with both tip and hub loss corrections, local Re-dependent polars from XFOIL, convergence criterion documented.

### Example 3: Supersonic Inlet Shock System Design
**Input:** Turbojet inlet for M = 2.0 cruise, required captured mass flow rate 5 kg/s, total pressure recovery target > 0.92 (MIL-E-5007D).
**Agent behaviour:** Applies oblique shock theory using Rankine-Hugoniot relations for two-shock external compression; optimises ramp angles θ₁ = 9°, θ₂ = 12° to minimise total pressure loss; computes wave angles β₁ = 30.5°, β₂ = 38.2° using θ-β-M relation; post-shock Mach numbers M₁ = 1.64, M₂ = 1.27; applies normal shock at cowl lip (M₂ → 1.0); total pressure recovery = π₁ × π₂ × π_NS = 0.985 × 0.979 × 0.962 = 0.928 (meets target); computes capture area A_capture = ṁ / (ρ V) = 0.0165 m² from isentropic upstream flow; checks additive drag from spillage at off-design.
**Output:** Two-ramp inlet with θ₁ = 9°, θ₂ = 12°; total pressure recovery 0.928; capture area 165 cm²; additive drag at design point zero (perfect capture).
**Why exemplary:** Full shock system design with recovery calculated from product of individual shock pressure ratios; explicitly compared to MIL spec.

### Example 4: Wing Induced Drag Estimation via Prandtl Lifting-Line Theory
**Input:** Tapered wing, span b = 12 m, root chord c_r = 1.5 m, tip chord c_t = 0.6 m, sweep Λ = 0° (straight wing), NACA 2415 section, cruise CL = 0.4, altitude 3000 m.
**Agent behaviour:** Discretises wing into N = 40 Fourier sine series terms; applies lifting-line equation α(θ) = (CL_section/(2π)) + α_i + α_L0 at each spanwise station; solves for Fourier coefficients A_n via collocation; computes span efficiency factor e = 1/(1 + δ) where δ = Σ(n>1) n(A_n/A_1)²; calculates induced drag coefficient CDi = CL²/(π × AR × e); checks that non-elliptical taper reduces e from 1.0 (ideal ellipse) to 0.935 for this taper ratio λ = 0.4; computes Oswald efficiency e_0 = 0.85 for whole aircraft (including fuselage contribution via Hoak method).
**Output:** Span efficiency e_wing = 0.935, CDi = 0.00217, Oswald factor e_0 = 0.85, induced drag 47 N at cruise, 8.4% of total drag budget.
**Why exemplary:** Lifting-line solution with proper Fourier series formulation; distinguishes wing span efficiency from aircraft Oswald factor.

### Example 5: CFD Flag Assessment for Transonic Regime
**Input:** Commercial aircraft wing at M = 0.78, CL = 0.52, question whether XFOIL/panel methods are adequate or CFD (RANS) required.
**Agent behaviour:** Checks key flow physics flags: (1) M > 0.3 — compressibility not negligible, Prandtl-Glauert correction needed; (2) M = 0.78 — transonic regime with potential shock; (3) Kármán-Tsien correction degrades near M = 1; (4) XFOIL uses incompressible boundary-layer equations with weak compressibility correction — not valid for shock-boundary-layer interaction; (5) flags that local Mach number near leading edge may exceed M_crit ≈ 0.7 for typical supercritical sections; recommends SU2 or OpenFOAM RANS (k-ω SST turbulence model) with AGARD validation; estimates shock position using Kármán-Tsien Cp_min correction as first step; computes M_crit via Laitone formula: M_crit = M at which local Cp_min = Cp_critical.
**Output:** XFOIL flagged as inadequate for M > 0.7 with shock; recommends SU2 Euler + RANS with k-ω SST; M_crit estimated 0.69; shock expected at 55% chord at M = 0.78.
**Why exemplary:** Clear and justified escalation from low-fidelity to CFD with explicit physics-based criteria.

---

## Thinking Parameters

### Primary Questions
1. What is the Mach number regime — subsonic (M < 0.3), incompressible; subsonic compressible (0.3 < M < 0.7); transonic (0.7 < M < 1.3); supersonic (M > 1.3)? Each requires fundamentally different methods.
2. What is the Reynolds number? Low Re (< 5 × 10⁵) favours laminar flow; high Re (> 5 × 10⁶) means fully turbulent — XFOIL is most reliable between 10⁵ and 5 × 10⁶.
3. Is the flow attached? XFOIL Cl predictions degrade rapidly above stall angle; CFD is unreliable for massively separated flows without validated LES/DES.
4. What level of accuracy is needed — preliminary sizing (±10%), conceptual layout (±5%), or certification-level (±1%)? Drives method selection from BEM → panel → RANS → LES.
5. Are 3D effects important — tip vortices, sweep, dihedral, fuselage interference? Panel methods (VSPAERO, AVL) or full 3D CFD may be needed vs 2D strip analysis.

### Domain Priors
- Kutta-Joukowski theorem: L = ρ V Γ per unit span; circulation Γ = ∮ V · ds around a closed contour enclosing the aerofoil.
- For incompressible flow at low angles of attack, thin aerofoil theory gives dCl/dα = 2π per radian (10.9% error vs NACA 4412 experimental 6.1/rad at Re = 3 × 10⁶).
- Prandtl-Glauert compressibility correction: Cp = Cp_incomp / √(1 − M²); breaks down for M > 0.7.
- Stall is detected in XFOIL when the wake momentum thickness θ/c > 0.02 — this is a useful sanity check even before the polar shows discontinuity.
- For propellers and wind turbines, the Betz limit sets maximum power extraction at Cp_max = 16/27 ≈ 0.593.
- Sweep angle Λ delays M_crit: M_crit,swept ≈ M_crit,unswept / cos(Λ); Jones (1945) formula.
- In supersonic flow, all disturbances are confined within the Mach cone (half-angle μ = arcsin(1/M)); leading-edge sweep must exceed μ for subsonic leading edge.

### Metacognitive Flags

| Signal | Trigger | Action |
|---|---|---|
| XFOIL non-convergence | Polar shows sudden Cl jump or Cd spike | Increase panel density (PANE N 200); check trailing edge closure |
| Negative drag in panel method | Induced drag < 0 | Check downwash sign convention; Trefftz plane integration may have sign error |
| BEM loop not converging | Induction factors oscillating | Apply Glauert's empirical correction for a > 0.4 (heavy loading regime) |
| High Mach local Cp | Cp < Cp_critical on suction surface | Flag for transonic CFD; shock-induced separation likely |
| Tip vortex noise concern | Propeller tip speed > 0.7 Mach | Reduce tip speed or use swept/scimitar tip geometry |
| Cl_max underestimated | XFOIL polar smoother than test data | XFOIL overestimates Cl_max by 5–15% for thick aerofoils (t/c > 15%) |
| Negative Cm_ac | High-cambered section drives nose-down pitch | Verify tail volume coefficient is sufficient to trim |

---

## Dead Feedback — Common Failure Modes

| Failure Mode | Symptom | Root Cause | Correction |
|---|---|---|---|
| XFOIL at wrong Re | Polar shows laminar bubble over-optimism | Re entered in wrong units (e.g., 300 instead of 300,000) | Verify Re = ρVc/μ; standard sea-level air ν = 1.46 × 10⁻⁵ m²/s |
| BEM ignoring tip loss | Thrust overpredicted by 8–15% | Prandtl tip loss factor F = 1 assumed | Implement Prandtl F at each station; F → 0 at blade tip |
| Wrong reference area | CL 2× error | Planform area vs wetted area confusion | Always state reference area with coefficient |
| Incompressible method at M = 0.8 | L/D 30% optimistic | Prandtl-Glauert used beyond M = 0.7 validity | Switch to compressible panel method or RANS CFD |
| Symmetry plane missing in 3D panel | Non-physical results near centreline | Image method not applied for wing-body | Add mirror image panels below ground plane |
| Boundary layer transition not set | XFOIL predicts excessive laminar run | Ncrit = 9 may not match actual turbulence intensity | Set Ncrit = 1–3 for wind tunnel (high-Tu); Ncrit = 12–14 for free flight |
| Drag polars not corrected for 3D | Strip theory Cd used directly | Section Cd ignores interference, gaps, roughness | Add profile drag increment: ΔCd ≈ 0.002 for typical nacelles |
| Reversed normal vectors | Panel method gives negative lift for positive alpha | CAD surface normals pointing inward | Reverse normal direction on all panels |

---

## Skill Refinements

**What works well:**
- XFOIL with Eppler/Selig/UIUC section database for low-Re UAV and GA aircraft at Re = 10⁵–3 × 10⁶.
- BEM with Prandtl tip-loss and Glauert heavy-loading correction for propeller and wind turbine design up to tip-speed-ratio λ = 8.
- AVL (Athena Vortex Lattice) for rapid 3D aerodynamic and stability analysis of conventional configurations.
- Oblique shock / Prandtl-Meyer expansion tables for supersonic inlet and nozzle design.

**What needs improvement:**
- Post-stall Cl prediction — XFOIL provides no reliable data beyond stall; the agent should default to flat-plate theory extrapolation (Cl ≈ 2π sin α) or Viterna method.
- Dynamic stall (pitching wings, helicopter rotor) is beyond quasi-steady BEM; flagged for Leishman-Beddoes model.
- Ground effect aerodynamics require image method extension; not currently automated.

**v1.1 additions planned:**
- SU2 adjoint sensitivity workflow for drag minimisation under CL constraint.
- OpenFOAM DES turbulence workflow for separated flows (flaps, bluff bodies).
- VSPAERO integration for full configuration vortex-lattice with trimming.
- Noise prediction module using Ffowcs Williams–Hawkings acoustic analogy for propeller tones.

---

## Theoretical Physics Foundations

The **Kutta-Joukowski theorem** establishes the fundamental connection between circulation and lift: L = ρ V_∞ Γ per unit span, where Γ = ∮ V · dl is the circulation around any closed contour enclosing the aerofoil. This result follows from the complex potential w(z) = U_∞(z + a²/z) + (iΓ/2π) ln(z) for a cylinder of radius a in uniform flow with bound circulation Γ, transformed to an aerofoil cross-section via the Joukowski mapping ζ = z + c²/z. The Kutta condition (velocity finite at trailing edge) uniquely determines Γ and hence lift, providing the physical closure for potential flow theory.

**Prandtl's lifting-line theory** extends 2D aerofoil results to finite wings by modelling the wing as a bound vortex sheet with trailing vortices shed downstream. The fundamental integro-differential equation is: α(y) = α_L0(y) + CL(y)/(2π) + (1/4πU_∞) ∫_{-b/2}^{b/2} (dΓ/dy') dy'/(y−y'), where the last term represents the downwash from trailing vortices. For an elliptic circulation distribution Γ(y) = Γ₀ √(1−(2y/b)²), downwash is uniform: w_i = Γ₀/(2b), and the span efficiency factor e = 1, giving minimum induced drag CDi = CL²/(π AR) for a given lift.

The **Rankine-Hugoniot relations** govern flow properties across a normal shock: ρ₂/ρ₁ = (γ+1)M₁² / ((γ−1)M₁² + 2); p₂/p₁ = (2γM₁² − (γ−1)) / (γ+1); T₂/T₁ = (2γM₁² − (γ−1))((γ−1)M₁² + 2) / ((γ+1)²M₁²). For an oblique shock at wave angle β for incoming Mach M₁, the component normal to the shock M₁n = M₁ sin(β) is used in these relations, while the tangential component is unchanged, giving post-shock M₂ and flow deflection θ via the θ-β-M relation: tan(θ) = 2 cot(β)(M₁² sin²(β)−1) / (M₁²(γ + cos 2β) + 2).

**Boundary layer theory** (Prandtl 1904) reduces the full Navier-Stokes equations within the thin viscous layer adjacent to a surface. The momentum integral equation (von Kármán): dθ/dx + θ(2 + H)(1/U_e)(dU_e/dx) = Cf/2, where θ is momentum thickness, H = δ*/θ is shape factor (H ≈ 2.6 laminar, 1.3–1.6 turbulent), U_e is edge velocity, and Cf is skin friction coefficient. XFOIL integrates this equation with closure relations for H and Cf and uses the e^N amplification method (Michel or envelope e^N) to predict boundary layer transition from laminar to turbulent.

**Bernoulli's equation** for incompressible flow: p + ½ρV² + ρgh = constant along a streamline, from which Cp = (p − p_∞)/(½ρV_∞²) = 1 − (V/V_∞)². In compressible flow the isentropic relation replaces this: p/p₀ = (1 + (γ−1)/2 × M²)^(−γ/(γ−1)), and Cp = (2/(γM_∞²))((p/p_∞) − 1). Negative Cp (suction peak) drives lift; the minimum Cp location typically coincides with maximum local velocity, and drag divergence occurs when this local velocity reaches M = 1 (sonic condition on the suction surface).

---

## Mathematical Framework

**Kutta-Joukowski:**
L' = ρ V_∞ Γ [N/m], with Γ = ∮_C V · dl [m²/s]

**Thin aerofoil lift slope:**
dCl/dα = 2π [per radian] (incompressible, inviscid)

**Prandtl-Glauert compressibility correction:**
Cp = Cp_0 / √(1 − M_∞²), valid for M < 0.7

**Induced drag (elliptic distribution):**
CDi = CL² / (π × AR × e), where e ≤ 1 (span efficiency)

**BEM induction factor iteration:**
a = 1 / (4F sin²φ / (σ Cl cos φ) + 1)
a' = 1 / (4F sin φ cos φ / (σ Cl sin φ) − 1)
where φ = atan((1−a)V / ((1+a')Ωr)), σ = Bc/(2πr)

**Prandtl tip-loss factor:**
F = (2/π) arccos(exp(−(B(R−r))/(2r sin φ)))

**Oblique shock θ-β-M relation:**
tan θ = 2 cot β × (M₁² sin²β − 1) / (M₁²(γ + cos 2β) + 2)

**Isentropic total-to-static pressure ratio:**
p₀/p = (1 + (γ−1)/2 × M²)^(γ/(γ−1))

**Friis link budget (repurposed for wake rake drag):**
Cd = 2∫θ/c_ref (wake momentum deficit integral, Betz wake method)

---

## Historical Context

**1891** — Otto Lilienthal conducts systematic glider experiments, producing the first measured Cl vs α polars (Lilienthal tables, 1889). Inspired the Wright brothers.

**1903** — Wright Brothers first powered heavier-than-air flight, Kitty Hawk, 12 December. They used their own wind tunnel data corrected from Lilienthal's measurements.

**1904** — Ludwig Prandtl presents boundary layer theory at the Third International Congress of Mathematicians, Heidelberg — arguably the most important single paper in aerodynamics.

**1907** — Lanchester (UK) and Prandtl/Betz (Germany) independently develop vortex theory of lift; Prandtl publishes lifting-line theory in 1918.

**1915** — NACA (National Advisory Committee for Aeronautics) established in USA; begins systematic aerofoil wind tunnel testing culminating in NACA 4-digit, 5-digit, and 6-series aerofoil families.

**1928** — Prandtl and Tietjens publish Fundamentals of Hydro- and Aeromechanics, synthesising boundary layer and lifting-line theory.

**1945** — Robert T. Jones (NACA) publishes swept-wing theory for delaying M_crit; fundamental to all subsonic jet aircraft design.

**1960s** — CFD emerges with Murman-Cole (1971) transonic small-disturbance code; Jameson's FL07 (1975) for transonic potential flow; full RANS codes in 1980s.

**1986** — Mark Drela and Michael Giles release XFOIL (initially called ISES) at MIT — the reference tool for 2D viscous aerofoil analysis still widely used in 2026.

**1999** — SU2 precursor work at Stanford; SU2 open-sourced 2012 with adjoint-based aerodynamic shape optimisation.

---

## Current State of the Art (2025–2026)

**SU2 adjoint optimisation:** SU2 v7.x supports discrete adjoint for drag minimisation under lift and geometric constraints, solving the adjoint RANS equations in O(1) additional cost vs primal solve. Used by Airbus, Boeing, and DLR for shape optimisation with hundreds of design variables. Coupled with free-form deformation (FFD) boxes for smooth surface parameterisation.

**OpenFOAM DES for separated flows:** Delayed Detached Eddy Simulation (DDES) in OpenFOAM v10/v11 resolves large-scale turbulence in separated regions (e.g., flap coves, landing gear) while using RANS in attached boundary layers. Requires O(10⁷–10⁸) cells and O(10³–10⁴) CPU-hours per case; GPU-accelerated via AmgX backend.

**AI airfoil optimisation:** Bayesian optimisation (BoTorch) and generative models (VAE, GAN trained on UIUC/PARSEC databases) are used to propose novel aerofoil shapes. Models trained on XFOIL/RANS databases predict Cl, Cd, Cm within 1–2% for subsonic Re = 10⁵–10⁷ in milliseconds. Papers: Li et al. (2022) deep learning aerofoil optimiser; Yonekura & Suzuki (2021) GAN aerofoil generation.

**eVTOL rotor aeroacoustics:** NASA X-57 and Joby S4 programs drive blade element/acoustics coupled tools: ANOPP2 (NASA), PSU-WOPWOP. High-fidelity LBM (Lattice Boltzmann Method) from Dassault Systèmes PowerFLOW is used for broadband noise at rotor–stator interaction frequencies.

**Experimental validation tools (2025):** Five-hole probe systems with 50 kHz sampling, PIV (Particle Image Velocimetry) with 4k × 4k resolution, pressure-sensitive paint (PSP) for full-surface Cp mapping, and MEMS surface hot-film arrays for transition detection — all now integrated into digital wind tunnel workflows with direct comparison to CFD via co-located sensor virtual models.
