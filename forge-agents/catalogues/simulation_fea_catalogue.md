# Simulation FEA Agent — Catalogue

## 5 Canonical Examples

### Example 1: Bracket Fatigue Life Under Cyclic Loading
**Input:** Aluminium 6061-T6 mounting bracket, 50 mm × 30 mm × 5 mm, fixed at one end, cyclic point load 0–2 kN at free end, required life 10⁷ cycles.
**Agent behaviour:** Constructs Tet10 mesh with element size 1.5 mm at fillet radius, applies symmetry BCs to halve model, runs linear static in CalculiX, extracts peak von Mises at fillet (187 MPa), computes stress ratio R = 0 (fully reversed would be R = −1 but here R = 0), maps to MIL-HDBK-5J S-N curve for 6061-T6, applies Kt = 2.1 geometric stress concentration at fillet, applies Goodman correction for mean stress (σ_mean = 93.5 MPa, σ_ult = 310 MPa), confirms SF = 1.4 > 1.2 minimum.
**Output:** Peak stress 187 MPa, corrected endurance limit 96 MPa at 10⁷ cycles, SF = 1.4, mesh convergence confirmed at <2% change from 2 mm→1.5 mm element size.
**Why exemplary:** Demonstrates full workflow from geometry → mesh → BC → solve → post-process → SF assessment with explicit convergence check and Goodman correction documented.

### Example 2: Pressure Vessel Modal Analysis for Vibration Qualification
**Input:** Cylindrical steel pressure vessel, OD 200 mm, wall 8 mm, length 400 mm, two flanged end caps, vibration environment 20–2000 Hz swept sine at 10 g.
**Agent behaviour:** Models vessel with C3D20R (20-node hex reduced integration) elements, applies fixed BCs at flange bolt pattern using RBE3 coupling, extracts first 20 eigenmodes via Lanczos method in CalculiX, identifies first bending mode at 312 Hz and first breathing mode at 1840 Hz, applies response spectrum analysis per IEC 60068-2-6, calculates dynamic amplification factor Q = 25 (assumed), peak dynamic stress 145 MPa vs yield 250 MPa, confirms separation from forcing frequency 50 Hz by factor > 1.5.
**Output:** First natural frequency 312 Hz, dynamic peak stress 145 MPa, SF vs yield = 1.72, no resonance risk in operating band 20–200 Hz.
**Why exemplary:** Shows coupled static/dynamic workflow, proper RBE3 constraint use, and frequency margin assessment per qualification standard.

### Example 3: Thermal-Structural Coupled Analysis of PCB Mounting Frame
**Input:** Titanium Ti-6Al-4V frame holding power electronics PCB, steady-state heat load 80 W, ambient 25°C, forced convection h = 15 W/(m²·K) on fin surfaces.
**Agent behaviour:** Runs sequential thermal-structural analysis: first thermal solve using DC3D10 elements to establish temperature field (peak 145°C at heat source), maps nodal temperatures to structural model as body loads, solves for thermal expansion stresses (α = 8.6 × 10⁻⁶ /K for Ti-6Al-4V), checks connector PCB interface forces against allowable 15 N per connector pin, evaluates creep risk at 145°C (negligible for Ti at this temperature), confirms bolt pre-load relaxation < 5%.
**Output:** Peak frame temperature 145°C, peak thermal stress 210 MPa (yield 880 MPa, SF = 4.2), connector interface force 8.3 N (< 15 N allowable), bolt pre-load retention 97%.
**Why exemplary:** Sequential coupling methodology with explicit thermal-to-structural load mapping; documents all allowable comparisons with margins.

### Example 4: Mesh Convergence Study on Stress Concentration
**Input:** Steel plate with central circular hole (d/w = 0.3), uniaxial tension 100 MPa remote stress, theoretical Kt = 2.73 (Peterson's).
**Agent behaviour:** Runs five meshes with element sizes 5 mm, 2.5 mm, 1.25 mm, 0.625 mm, 0.3125 mm at hole edge; plots peak von Mises vs element size; applies Richardson extrapolation to estimate h → 0 solution; confirms GCI (Grid Convergence Index) < 1% between two finest meshes; validates against theoretical Kt; documents that Tet4 elements underestimate stress by 12% vs Tet10 at same element size.
**Output:** Extrapolated peak stress 272.1 MPa vs theoretical 273 MPa (0.3% error), GCI = 0.7% (finest mesh pair), confirms Tet10 mandatory for stress concentration assessment.
**Why exemplary:** Explicit quantitative convergence proof using Richardson extrapolation and GCI metric; element type sensitivity study documented.

### Example 5: Non-Linear Buckling of Thin-Walled Aerospace Panel
**Input:** Aluminium 2024-T3 flat panel 400 mm × 200 mm × 1.5 mm, simply supported on all edges, in-plane compressive load applied as displacement ramp.
**Agent behaviour:** Runs linear eigenvalue buckling (CalculiX *BUCKLE step) to get critical load estimate 8.2 kN; then runs geometrically non-linear Riks arc-length method (*STATIC, RIKS) with initial geometric imperfection seeded at first eigenmode × 0.005 mm amplitude (0.3% of thickness); traces load-displacement path to post-buckling; identifies limit point at 7.6 kN (7.3% below linear prediction due to imperfection sensitivity); checks plastic strains (zero — buckling is elastic); reports knock-down factor KDF = 0.93.
**Output:** Linear buckling load 8.2 kN, non-linear limit load 7.6 kN, KDF = 0.93, first post-buckle mode is first eigenmode as expected.
**Why exemplary:** Demonstrates full non-linear buckling workflow with imperfection seeding, Riks solver choice justified, knock-down factor correctly defined.

---

## Thinking Parameters

### Primary Questions
1. What is the dominant physics — static stress, dynamic/modal, thermal, buckling, or non-linear? Each requires a distinct CalculiX step type and element family.
2. What are the boundary conditions — is every rigid body mode constrained? Count: 6 DOFs must be removed; over-constraining causes artificial stiffness.
3. What mesh density is needed at the critical feature — fillet radius, hole edge, weld toe? Rule of thumb: minimum 4 Tet10 elements across any stress-raising feature.
4. What is the target accuracy — is a ±5% stress estimate acceptable, or is a certified margin required? The latter demands a documented convergence study.
5. Has the model been validated or does it require a hand-calculation sanity check? Every FEA result should be bracketed by at least one closed-form estimate.

### Domain Priors
- Tet4 (linear tetrahedral) elements are stiff in bending and shear-lock; always prefer Tet10 (quadratic) for stress analysis.
- Reduced integration elements (C3D8R) suppress hourglassing with hourglass control; full integration (C3D8) can exhibit volumetric locking in near-incompressible materials.
- The stress singularity at a re-entrant corner (perfectly sharp) is mathematically infinite; FEA results there are mesh-dependent and must never be used for fatigue assessment without a notch method.
- Contact pairs (CalculiX *CONTACT PAIR) default to hard normal contact with penalty tangent; use ADJUST=0 to avoid node penetration at first increment.
- Modal effective mass > 80% cumulative in each principal direction is the minimum for a complete frequency extraction in vibration analysis.
- Rule of thumb for mesh size vs wavelength in wave propagation: at least 10 elements per wavelength.
- CalculiX uses the Abaqus input format; keyword errors fail silently with misleading output — always inspect .dat file warnings.

### Metacognitive Flags

| Signal | Trigger | Action |
|---|---|---|
| Peak stress at boundary node | Stress at constrained DOF location | Ignore; use free-body equilibrium instead |
| Non-converging Newton-Raphson | Residual oscillating after 10 iterations | Reduce load increment, check contact, check material law |
| Negative eigenvalue in stiffness | Mechanism or near-mechanism in structure | Audit BCs; add weak springs if rigid body mode is intentional |
| GCI > 5% between mesh levels | Insufficient refinement | Refine by factor 2, rerun, recompute GCI |
| Thermal strains >> mechanical strains | Temperature delta > 100°C on constrained part | Ensure CTE and reference temperature are consistent |
| Reaction forces don't balance applied load | BCs missing a DOF, or load direction error | Sum all reaction forces; must equal applied resultant to < 0.1% |
| Plastic strain > 5% in static analysis | Material entering large-strain regime | Switch to finite-strain formulation (*NLGEOM) |

---

## Dead Feedback — Common Failure Modes

| Failure Mode | Symptom | Root Cause | Correction |
|---|---|---|---|
| Over-stiff Tet4 mesh | Von Mises 20–40% below Tet10 result | Shear locking in linear tets | Remesh with Tet10 or hex elements |
| Missing constraint | Model drifts to infinity, zero pivot warning | Unconstrained rigid body mode | Identify and fix the unconstrained DOF |
| Wrong material orientation | Anisotropic result independent of fibre angle | Local CSYS not assigned to element set | Assign *ORIENTATION card to all composite elements |
| Singularity at sharp corner | Stress doubles each mesh refinement level | Mathematical singularity at re-entrant corner | Add fillet ≥ manufacturing minimum; use sub-modelling |
| Wrong SF interpretation | SF < 1 accepted because "FEA is conservative" | Forgetting to include Kt, fatigue scatter factor | Apply all relevant factors before comparing to allowable |
| Incorrect contact setup | Interpenetration of surfaces in deformed view | Contact pair master/slave reversed on thin vs thick parts | Set thin/soft part as slave; check initial clearance |
| Unit inconsistency | Displacement result 1000× wrong | Mixed SI and mm-MPa-tonne unit systems | Commit to one system; CalculiX has no built-in unit check |
| Unchecked hourglass energy | Spurious zero-energy modes in C3D8R | Hourglass control insufficient | Check that hourglass energy < 5% of internal energy |

---

## Skill Refinements

**What works well:**
- CalculiX *STATIC with Tet10 C3D10 elements for linear stress analysis is robust and well-validated.
- Modal extraction with Lanczos (*FREQUENCY, SOLVER=LANCZOS) is efficient for structures up to ~10⁶ DOF.
- Thermal-structural sequential coupling is straightforward when temperature field is steady-state.
- Sub-modelling (*SUBMODEL) is reliable for driving fine local meshes from a coarse global solution.

**What needs improvement:**
- Non-linear contact convergence is slow; adaptive penalty parameters would accelerate this.
- CalculiX does not support cohesive zone models natively; delamination analysis requires UMAT or external pre-processing.
- Post-processing in CGX (CalculiX GraphiX) is functional but less capable than Paraview; always export to VTK and visualise in Paraview.

**v1.1 additions planned:**
- Integration with Gmsh Python API for parametric mesh generation and automated refinement loops.
- Automated GCI calculation script in post-processing pipeline.
- S-N curve database lookup from MMPDS-12 for common aerospace alloys.
- GPU-accelerated solve using PETSc backend for models > 5 × 10⁶ DOF.

---

## Theoretical Physics Foundations

The foundation of FEA is the **principle of virtual work**: for a body in equilibrium, the internal virtual work equals the external virtual work for any kinematically admissible virtual displacement field δu. Mathematically: ∫_V σ_ij δε_ij dV = ∫_V f_i δu_i dV + ∫_S t_i δu_i dS. This statement is equivalent to the strong-form equilibrium equations (∂σ_ij/∂x_j + f_i = 0) but requires only C⁰ continuity of the displacement field, making it suitable for piecewise polynomial approximation.

The **weak form** is obtained by multiplying the strong-form momentum equation by a test function δu and integrating by parts, transferring one spatial derivative from the stress tensor to the test function. This reduces the continuity requirements on the approximating functions from C¹ to C⁰ and naturally incorporates Neumann boundary conditions (traction BCs) as boundary integrals. The Galerkin method selects the test functions from the same polynomial space as the trial functions, yielding the symmetric stiffness matrix K and consistent load vector f.

Element stiffness is assembled from the local contribution: K_e = ∫_V_e B^T E B dV, where B is the strain-displacement matrix (derivatives of shape functions), E is the material constitutive matrix (fourth-order elasticity tensor in Voigt notation as 6×6 matrix), and integration is performed over the element volume. For Tet10 elements, the shape functions N_i are quadratic (complete second-order polynomial in volume coordinates ξ, η, ζ, ψ with ξ + η + ζ + ψ = 1), providing 10 nodes per element and enabling accurate representation of linearly varying strain fields.

**Gauss quadrature** evaluates the element integrals exactly (to machine precision) for polynomial integrands up to order 2n−1 using n Gauss points per direction. For a Tet10 element in natural coordinates, 4-point Gauss quadrature integrates polynomials of degree ≤ 3 exactly. The quadrature rule maps: ∫_V_e f(x) dV ≈ Σ_g w_g f(x_g) det(J_g), where w_g are weights, x_g are Gauss point positions, and J_g is the Jacobian of the mapping from natural to physical coordinates. A distorted element (det(J) → 0) signals a degenerate element that will produce erroneous stresses — mesh quality checks must flag elements with Jacobian ratio < 0.1.

The **global stiffness matrix** K is sparse and symmetric positive semi-definite (positive definite after applying sufficient BCs). Direct solvers (Cholesky factorisation, Pardiso, MUMPS) are used for models up to ~10⁷ DOF; iterative solvers (conjugate gradient with incomplete Cholesky preconditioner) are preferred above that scale. The condition number of K scales as O((h/L)^−2) where h is element size and L is structure length, meaning poorly conditioned systems arise from large mesh size ratios or near-mechanisms.

---

## Mathematical Framework

**Stiffness matrix assembly:**
K = Σ_e ∫_V_e B^T(x) · E · B(x) dV ≈ Σ_e Σ_g w_g · B^T(x_g) · E · B(x_g) · det(J(x_g))

**Strain-displacement relation (Voigt notation):**
ε = [ε_xx, ε_yy, ε_zz, γ_xy, γ_yz, γ_xz]^T = B · u

**Hooke's law (isotropic):**
σ = E · ε where E = (E / ((1+ν)(1-2ν))) × [1-ν, ν, ν, 0...; ν, 1-ν, ν, 0...; ...]

**Tet10 shape function (corner node 1):**
N_1 = ξ(2ξ − 1) where ξ = volume coordinate at node 1

**Mid-side node shape function:**
N_5 = 4ξη (mid-side between nodes 1 and 2)

**Eigenvalue problem (free vibration):**
(K − ω² M) φ = 0, solved by Lanczos iteration for lowest p eigenvalues

**Richardson extrapolation (grid convergence):**
f_exact ≈ f_h1 + (f_h1 − f_h2) / (r^p − 1) where r = h2/h1 (refinement ratio), p = observed convergence order

**Grid Convergence Index:**
GCI = F_s · |ε| / (r^p − 1) where F_s = 1.25 (safety factor), ε = (f_h1 − f_h2)/f_h2

**Safety factor definition:**
SF = σ_allowable / σ_max,applied; for fatigue: SF = σ_e(corrected) / σ_max,cyclic

---

## Historical Context

**1943** — Richard Courant formulates piecewise polynomial minimisation of variational problems, laying the mathematical groundwork for FEM.

**1956** — Turner, Clough, Martin, and Topp publish "Stiffness and Deflection Analysis of Complex Structures" in Journal of Aeronautical Sciences — generally recognised as the birth of the direct stiffness method and FEM for engineering.

**1960** — Ray Clough coins the term "finite element method" in his paper on plane stress analysis.

**1965** — John Argyris develops variational energy methods at Stuttgart, contributing plate and shell element formulations.

**1967** — O.C. Zienkiewicz and Y.K. Cheung publish "The Finite Element Method in Structural and Continuum Mechanics" — the first comprehensive FEM textbook, which standardises notation still in use today.

**1972** — NASTRAN (NASA Structural Analysis) is released publicly, becoming the first widely used commercial FEA code.

**1978** — Abaqus 1.0 released by Hibbitt, Karlsson & Sorensen, introducing robust non-linear analysis capabilities including contact and plasticity.

**1989** — MSC/NASTRAN introduces p-element capabilities; adaptive mesh refinement becomes commercially available.

**1999** — Klaus Wittig and Guido Dhondt release CalculiX as open-source FEA with Abaqus-compatible input format — the reference solver for this agent.

**2003** — Introduction of isogeometric analysis (IGA) concept by T.J.R. Hughes, merging CAD spline geometry with FEA approximation spaces.

---

## Current State of the Art (2025–2026)

**GPU-accelerated FEA:** Solvers such as Ansys GPU Solver, SimScale (cloud FEA), and Altair Radioss leverage NVIDIA A100/H100 GPUs to reduce solve time for models with 10⁸–10⁹ DOF by 10–50× vs CPU. AmgX and CUSP provide GPU-native algebraic multigrid preconditioners.

**Isogeometric Analysis (IGA):** IGA replaces Lagrangian polynomial shape functions with NURBS or T-splines from the CAD geometry directly, eliminating mesh-induced geometric approximation error. Implementations: OpenCASCADE-based PetIGA, Coreform Cubit IGA. Particularly advantageous for thin shells (Kirchhoff-Love formulation without shear locking) and contact problems on curved surfaces.

**Neural PDE surrogates:** Physics-informed neural networks (PINNs) and graph neural network (GNN) surrogates (e.g., DeepMind GNS, Ansys SimAI) can predict FEA stress fields in milliseconds after offline training, enabling real-time design space exploration. Accuracy to ~2% vs full FEA for interpolation within training distribution; extrapolation remains unreliable.

**Topology optimisation integration:** Density-based SIMP (Solid Isotropic Material with Penalisation) is integrated in Altair OptiStruct, COMSOL, and open-source tools (OpenTopOpt, TopOpt.jl). The agent can run TO with CalculiX as the FEA backend via Python wrappers, then validate the optimised geometry with a refined stress analysis.

**Digital twin FEA:** Siemens Simcenter, ANSYS Twin Builder, and Modelon IMPACT maintain live FEA models synchronised with sensor data using Kalman-filter-based state estimation. Boundary conditions are updated in near-real-time from strain gauge and accelerometer telemetry, enabling predictive maintenance scheduling based on live structural state.

**Benchmarks:** NAFEMS benchmark suite (2D/3D elasticity, plate bending, free vibration) provides quantitative accuracy targets; CalculiX passes >95% of NAFEMS benchmarks within 2% tolerance. The TEAM (Testing Electromagnetic Analysis Methods) analogues for structural problems are the NAFEMS Benchmark Challenge series (2020–2025).
