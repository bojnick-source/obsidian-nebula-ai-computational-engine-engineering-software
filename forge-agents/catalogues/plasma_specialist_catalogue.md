# Plasma Specialist — Catalogue

## 5 Canonical Examples

### Example 1: Hall Effect Thruster Sizing for 12 U CubeSat
**Input:** 12 U CubeSat (24 kg), Δv = 800 m/s mission, 30 W power available, Xenon propellant, LEO → Lunar transfer.
**Agent behaviour:** Applied Tsiolkovsky equation m_prop/m_0 = 1 − exp(−Δv/v_e) with target I_sp = 1200 s (v_e = 11,772 m/s); computed m_prop = 1.43 kg; cross-checked against BHT-200 (Busek, 200 W, I_sp 1390 s) → not suitable at 30 W; evaluated ENPULSION IFM Nano (1 W–4 mN) and ThrustMe NPT30-I2 iodine thruster (30 W, I_sp 800 s); flagged I_sp penalty of iodine vs Xenon (−30%); recalculated m_prop = 2.05 kg for iodine, noting propellant mass fraction 8.5% of wet mass.
**Output:** ThrustMe NPT30-I2 selected: 30 W, T = 1.1 mN, I_sp = 800 s, m_prop = 2.05 kg, total impulse 16,200 N·s, burn time 17,200 hours cumulative.
**Why exemplary:** Tsiolkovsky applied correctly to wet vs dry mass; I_sp penalty for iodine vs Xenon quantified; power constraint was the binding constraint, not volume.

### Example 2: Plume Contamination Analysis for Solar Array Protection
**Input:** Hall thruster on 3-axis stabilised spacecraft, solar array 45° off thruster axis, array 1.2 m from thruster exit, fluence limit 10¹⁵ ions/cm².
**Agent behaviour:** Modelled plume as superposition of directed beam (core, half-angle 25°) and charge-exchange (CEX) ions (isotropic from near-field); computed CEX ion current density at array using σ_CEX = 60 Å² for Xe⁺-Xe collisions, neutral density from 1/r² expansion, integrated CEX flux along line of sight; computed sputtering yield Y for solar cell cover glass (SiO₂) vs Xe⁺ at 100–300 eV using Yamamura-Tawara formula; estimated deposited film from thruster-sputtered materials (carbon, ceramic) using angular distribution.
**Output:** CEX fluence at array = 3.2×10¹⁴ ions/cm² (margin 3.1× below limit); sputtering rate cover glass 0.8 nm/year; carbon film deposition 2.1 nm/year (not optically significant at <20 nm per 5-year mission).
**Why exemplary:** CEX collision cross-section applied quantitatively; both erosion (sputtering) and deposition pathways evaluated; fluence integrated over mission life, not just steady-state rate.

### Example 3: Thruster Magnetic Field Circuit Design
**Input:** 200 W Hall thruster design, target discharge channel inner radius 25 mm, outer radius 40 mm, peak radial B-field 150 G in channel, 50 G near exit plane.
**Agent behaviour:** Set up magnetic circuit with inner pole, outer pole, and coil; used reluctance model R = l/(µ₀µ_r A) for each segment; specified ampere-turns NI for field coil based on reluctance network solution; verified Hall parameter Ω_e = eB/(m_e·ν_e) >> 1 (target Ω_e > 10³ to magnetise electrons while leaving ions unmagnetised); verified ion Hall parameter Ω_i = eB/(m_i·ν_i) << 1 (target <0.01 for Xe⁺ at 150 G); computed magnetic mirror ratio to assess electron trapping efficiency.
**Output:** NI = 800 A·turns per coil, B_peak = 152 G (1.3% error), Ω_e = 4,200 >> 1, Ω_i = 0.0085 < 0.01; electron magnetisation confirmed; ion trajectory unaffected.
**Why exemplary:** Hall parameter condition explicitly verified for both electrons and ions; magnetic mirror ratio computed to confirm electron confinement; reluctance model used before FEA.

### Example 4: Propellant Budget Trade — Xenon vs Iodine vs Krypton
**Input:** 50 W Hall thruster, 500 m/s Δv, 15 kg spacecraft, launch volume constraint: propellant tank ≤ 0.5 U (500 cm³).
**Agent behaviour:** Compared I_sp and density for Xe (I_sp=1500s, ρ_liq=3,057kg/m³ at 57bar), Kr (I_sp=1700s, ρ_gas=stored at 100bar), I₂ (I_sp=900s, ρ_solid=4,930kg/m³); computed m_prop from Tsiolkovsky for each; computed propellant volume accounting for packing and tank structure (BV factor 0.85 usable); found I₂ requires smallest volume (108 cm³) despite lowest I_sp due to solid storage density; noted iodine requires heated feed system (>387 K sublimation point); flagged potential iodine contamination of ion optics if sublimation temperature not maintained.
**Output:** Iodine selected on volume; m_prop = 0.39 kg in 108 cm³; Xenon requires 892 cm³ (infeasible); Krypton requires 480 cm³ (marginal); iodine feed heater power +1.2 W added to power budget.
**Why exemplary:** Density and I_sp combined in volume-constrained trade; sublimation temperature operational constraint surfaced; feed system power penalty quantified.

### Example 5: Gridded Ion Engine Beam Current and Neutraliser Sizing
**Input:** 3 mN thrust target, I_sp = 3,000 s, Xenon, 12 cm beam diameter.
**Agent behaviour:** Derived thrust T = ṁ·v_e = I_b/e·m_Xe·v_e where I_b is beam current; v_e = I_sp·g₀ = 29,430 m/s; solved for I_b = T·e/(m_Xe·v_e) = 3×10⁻³/(1.6×10⁻¹⁹/(2.18×10⁻²⁵·29,430)) = 0.298 A; computed beam power P_beam = (1/2)·(m_Xe/e)·v_e²·I_b = 0.5×136.6×29,430²×0.298/1000 = 178 W; sized neutraliser hollow cathode at 10% of beam current = 30 mA emission current; flagged perveance limit: J ≤ (4ε₀/9)√(2e/m_i)·(V_b^(3/2)/d²) to verify grid transparency.
**Output:** Beam current 0.298 A, beam power 178 W, total thruster power ~240 W (including discharge, accel, neutraliser losses), neutraliser 30 mA; perveance at 1200 V verified within Child-Langmuir limit.
**Why exemplary:** Beam current derived from thrust equation, not assumed; Child-Langmuir perveance limit checked to prevent grid impingement; neutraliser sizing follows from beam current, not guessed.

## Thinking Parameters

### Primary Questions (ask before every task)
1. What are the binding constraints — power, propellant volume, Δv, or thrust level — and which sets the system trade space?
2. Are the electron and ion Hall parameters verified (Ω_e >> 1, Ω_i << 1) for any magnetised plasma device, and is the Debye length small relative to device dimensions?
3. Have I applied Tsiolkovsky correctly to the correct mass fraction (wet vs dry, including propellant feed system mass)?
4. What is the plume divergence half-angle, and have I computed CEX ion flux at all sensitive surfaces (solar arrays, star trackers, optics)?
5. Is the neutraliser or cathode current matched to beam current, and is the keeper/discharge voltage within safe operating bounds?

### Domain Priors
- Hall thrusters operate at Ω_e = eB/mν of order 10²–10⁴; below this range, electrons drift to anode and efficiency collapses.
- CEX ion formation rate scales with neutral pressure in plume; it peaks in near field (0–10 cm from exit) and must be evaluated at all sensitive spacecraft surfaces, not just on-axis.
- Iodine propellant enables solid-state storage (ρ = 4.93 g/cm³) but requires heater power and careful thermal management to prevent re-condensation in feed lines.
- Thruster throttling (reduce power) typically reduces I_sp and increases beam divergence; the efficiency curve must be evaluated at all operating points, not just nominal.
- Plume-induced spacecraft charging occurs primarily through CEX ions depositing positive charge on solar cells; need to verify differential charging < 1 V for sensitive electronics.
- Total impulse and propellant mass are primary system drivers; I_sp is the lever that trades propellant mass against power.

### Metacognitive Flags
| Signal | Trigger condition | Action |
|---|---|---|
| Hall parameter violation | Ω_e < 10 or Ω_i > 0.1 for proposed magnetic field | Redesign magnetic circuit; do not proceed to performance estimation |
| Plume contamination gap | Thruster firing direction not defined relative to solar arrays | Request spacecraft attitude and thruster position; block plume analysis until resolved |
| Tsiolkovsky mass fraction error | Propellant mass fraction > 40% of wet mass | Verify propulsion system mass (tank, feed, thruster) is included in dry mass |
| Child-Langmuir perveance exceeded | Grid voltage / gap / area outside space-charge limit | Grid spacing must be reduced or beam voltage raised; cross-screen to structural team |
| Iodine sublimation temperature not maintained | Feed line below 387 K with iodine propellant | Add 0.5–2 W heater; flag to thermal fluids specialist |
| Neutraliser current undersized | Neutraliser emission < 110% of beam current | Spacecraft will charge positive; increase neutraliser flow rate or cathode size |

## Dead Feedback — Common Failure Modes

| Failure Mode | Symptom | Root Cause | Correction |
|---|---|---|---|
| I_sp selected from nominal only | Propellant budget wrong in practice | Thruster operated at partial power (lower I_sp); throttle curve not evaluated | Integrate impulse over actual power timeline; use throttle-table model |
| Dry mass excludes feed system | Propellant budget 15–30% short | Tank + valve + feed line mass omitted from dry mass calculation | Include all propulsion subsystem hardware in dry mass |
| CEX flux underestimated | Solar array degrades in 6 months | Only beam core modelled; CEX isotropic component ignored | Add CEX ion production model from plume neutral density |
| Debye length too large | Plasma not quasi-neutral in channel | Low density operating point with λ_D comparable to channel width | Verify n_e >> ε₀kT_e/e²L² at all operating points |
| Neutraliser not co-fired | Spacecraft charges to −200 V, instruments damaged | Neutraliser ignition sequence not verified in power-on script | Require neutraliser interlock with beam enable; sequence: cathode → neutraliser → beam |

## Skill Refinements (v1.0 → next)
- What works well: Tsiolkovsky mass fraction analysis, Hall parameter verification, CEX flux estimation, thruster selection from power and Δv constraints.
- What needs improvement: Plasma instability prediction (azimuthal oscillations, breathing mode), full 3D PIC plume modelling, electrode erosion life prediction (sputter yield integration over energy distribution).
- Proposed v1.1 additions: Add electrospray / FEEP thruster sizing for sub-mN regime; integrate Hall2De or OpenFOAM-plasma plume simulation; add solar electric propulsion (SEP) power-thrust trajectory optimisation.

## Theoretical Physics Foundations

**Magnetohydrodynamics and Plasma as a Fluid.** A plasma can be described as a conducting fluid when the characteristic length scale L >> λ_D (Debye length) and the collision mean free path λ_mfp << L. The MHD equations couple fluid dynamics with Maxwell's equations. The induction equation ∂B/∂t = ∇×(v×B) − ∇×(η∇×B/µ₀) governs magnetic field evolution in a moving conductor; the magnetic Reynolds number Rm = µ₀σvL determines whether convection (Rm >> 1) or diffusion (Rm << 1) dominates. In Hall thrusters, Rm << 1 (collisional electrons) but Hall effect is critical: electrons carry current across B while ions cross B largely unimpeded.

**Debye Shielding and Quasi-Neutrality.** In a plasma, free charges rearrange to screen electrostatic perturbations over the Debye length λ_D = √(ε₀kT_e/(n_e e²)). For typical Hall thruster conditions (n_e = 10¹⁷–10¹⁸ m⁻³, T_e = 10–30 eV): λ_D ≈ 0.1–0.3 mm. The plasma is quasi-neutral (n_i ≈ n_e) on scales >> λ_D; sheaths of thickness ~5λ_D form at walls where the plasma meets a surface. The Bohm criterion governs the sheath entrance velocity: ions must enter the sheath at v_Bohm = √(kT_e/m_i) for stable sheath formation. This sets the ion current to channel walls and hence erosion rate.

**Lorentz Force and Ion Acceleration.** The Lorentz force F = q(E + v×B) accelerates ions in the crossed E×B field of a Hall thruster. Electrons are magnetised and drift azimuthally (Hall current J_θ = en_e v_θ); ions are unmagnetised and accelerated axially by the electric field. The ion exhaust velocity v_e = √(2eΔφ/m_i) where Δφ is the potential drop. For Xe⁺ accelerated through 300 V: v_e = √(2×1.6×10⁻¹⁹×300/(2.18×10⁻²⁵)) = 20,850 m/s, giving I_sp = v_e/g₀ = 2126 s. The thrust T = ṁ·v_e + (p_e − p_0)·A_exit; for electrostatic thrusters the pressure term is negligible.

**Charge-Exchange Collisions.** CEX reactions Xe⁺_fast + Xe_slow → Xe_slow⁺ + Xe_fast create slow ions from fast beam ions interacting with the neutral plume. The reaction cross-section for Xe⁺-Xe: σ_CEX = [A − B·ln(E_ion)]² where A ≈ 87.3 Å, B ≈ 13.6 Å at 100–2000 eV (Rapp & Francis model). CEX ion production rate: ṅ_CEX = n_0·n_i·σ_CEX·v_rel. These slow, near-isotropic ions populate the plume wings and can reach solar arrays and star trackers at large off-axis angles. They also represent lost momentum (I_sp reduction) and constitute the primary plume contamination mechanism.

**Ionisation Physics — Electron Bombardment.** In discharge plasmas, ionisation proceeds by electron impact: e + Xe → Xe⁺ + 2e, with rate coefficient K_ion(T_e) = ∫σ_ion(v)·v·f_e(v)dv where f_e is the electron energy distribution function (EEDF). For T_e = 10–25 eV in Xe, K_ion ≈ 10⁻¹⁴–10⁻¹³ m³/s. The ionisation efficiency determines propellant utilisation: η_u = (I_b/e·m_i)/(ṁ_prop). High η_u (>90%) requires sufficient neutral residence time in the ionisation zone, governed by L_ion/v_neutral where L_ion is the ionisation zone length and v_neutral = √(8kT_n/πm_Xe) is the neutral thermal velocity.

## Mathematical Framework

**Tsiolkovsky Rocket Equation.** Δv = v_e · ln(m_0/m_f) = g₀·I_sp·ln(1/(1 − ζ)), where ζ = m_prop/m_0 is the propellant mass fraction. Rearranging: m_prop = m_0·[1 − exp(−Δv/g₀I_sp)]. Total impulse: J_total = m_prop·g₀·I_sp. For electric propulsion power P, thrust T, and efficiency η: T = 2ηP/v_e = 2ηP/(g₀I_sp), so I_sp and thrust trade against each other at fixed power.

**Hall Parameter.** Ω = eB/(mν), where ν = collision frequency (ν = n_n·σ_col·v_th for electron-neutral collisions). For electrons: Ω_e = eB/(m_e·ν_en). Required condition for Hall thruster operation: Ω_e >> 1 (electrons magnetised) and Ω_i << 1 (ions unmagnetised). At B = 150 G = 0.015 T, cyclotron frequency ω_ce = eB/m_e = 2.64×10⁹ rad/s; for ν_en = 10⁸ s⁻¹ (typical), Ω_e = 26.4 >> 1. Ion cyclotron frequency for Xe⁺: ω_ci = eB/m_Xe = 1.1×10⁴ rad/s; Ω_i = 0.00011 << 1.

**Child-Langmuir Space-Charge Limit.** Maximum ion current density through an ion optic grid: J_max = (4ε₀/9)√(2e/m_i)·V_b^(3/2)/d², where V_b is beam voltage, d is grid gap. For Xe⁺, V_b = 1200 V, d = 1 mm: J_max = 15.4 mA/cm². Exceeding this limit causes space-charge saturation and beam interception on accelerator grid.

**Plume Neutral Density.** From thruster exit, neutral density falls as n_0(r) = ṁ_0·A_exit/(4πr²·m_Xe·v_n) for effusive expansion into vacuum. CEX production rate at position r: Q_CEX(r) = n_0(r)·n_i(r)·σ_CEX·v_i. Integrating along beam path gives total CEX flux at a surface at angle θ_off-axis.

**Thrust and I_sp from First Principles.** Thrust: T = ṁ_propellant·c_eff = I_b·(m_i/e)·v_e, where I_b is beam current. Power: P = (1/2)·(m_i/e)·I_b·v_e². Therefore T²/(2P) = T/v_e = ṁ, confirming T = √(2Pη·ṁ) at fixed efficiency η = P_beam/P_input. This equation shows why high I_sp costs power at fixed thrust: P ∝ T·v_e ∝ T·g₀·I_sp.

## Historical Context

- **1903** — Tsiolkovsky publishes "Exploration of the Universe with Reaction Machines"; derives rocket equation.
- **1926** — Robert Goddard launches first liquid-fuelled rocket (LOX/gasoline), achieving 12.5 m altitude.
- **1944** — V-2 rocket demonstrates guided ballistic trajectory; demonstrates feasibility of large-scale rocket propulsion.
- **1955** — Ernst Stuhlinger proposes ion propulsion for interplanetary travel; first theoretical treatment of high-I_sp electric propulsion.
- **1964** — SERT-1 (Space Electric Rocket Test) demonstrates first ion engine operation in space (NASA/LeRC); electron-bombardment thruster, 28 mN.
- **1970s** — Soviet SPT (Stationary Plasma Thruster) Hall thruster developed at MNIEE Fakel; SPT-50/100 family established.
- **1972** — Soviet Meteor satellite becomes first spacecraft to use Hall thrusters operationally (SPT-50).
- **1994** — First Western demonstration of SPT-100 on Intelsat satellite; triggers Western Hall thruster development.
- **1998** — Deep Space 1 demonstrates NSTAR ion engine (2.3 kW, 92 mN, I_sp 3100 s); first primary propulsion ion engine for deep space.
- **2003** — ESA SMART-1 lunar orbiter uses PPS-1350 Hall thruster; 1500 W, 88 mN.
- **2007** — Dawn mission launched with three NSTAR engines; orbits Vesta (2011) and Ceres (2015).
- **2015** — SpaceX Starlink v0.9 satellites use Krypton Hall thrusters (Starlink Hall thruster), making Krypton propellant operationally viable.
- **2019** — ThrustMe demonstrates NPT30-I2 iodine Hall thruster on Beihangkongshi-1 3U CubeSat; first in-space iodine propulsion (2021).
- **2020s** — Miniaturisation drives sub-100 W HET development; electrospray (FEEP) thrusters demonstrated at < 1 mN; ENPULSION IFM Nano operational on 60+ spacecraft.

## Current State of the Art (2025–2026)

**Miniaturised Hall Thrusters (<100 W).** BIT-3 (Busek), ThrustMe NPT30-I2, ENPULSION IFM Nano, and Exotrail ExoMG-nano operate in the 1–50 W range, enabling propulsion on 3–12 U CubeSats. Iodine propellant eliminates high-pressure Xenon tanks and Pressure vessels (COPV) — critical for rideshare launches. In-space demonstrations of iodine HETs have accumulated > 1000 hours of operation by 2025.

**Green Propellants.** AF-M315E (ASCENT, formerly LMP-103S) and SHP163 enable monopropellant performance superior to hydrazine (I_sp 250 vs 220 s) with reduced toxicity. GPIM (Green Propellant Infusion Mission, 2019) demonstrated ASCENT at 1 N thrust. These compete with electric propulsion for moderate Δv missions where power is scarce.

**Plasma Simulation Tools.** HPHall-2 and Hall2De (MIT) are standard 2D axisymmetric Hall thruster codes. OpenFOAM with MHD solver extensions and particle-in-cell (PIC) codes (VSim, Starfish, PICMC) model plume physics. Hybrid PIC-fluid codes (HPHall-2) treat electrons as fluid and ions as particles, balancing computational cost with kinetic accuracy. Machine learning surrogate models trained on PIC data are enabling real-time thruster control optimisation (2024 demonstrations by JPL).

**Propulsion Performance Databases.** ERPS (Electric Rocket Propulsion Society) database and NASA Electric Propulsion Information Summary (EPIS) catalogue performance data for > 200 operational thrusters. The Aerospace Corporation maintains a classified/export-controlled database of U.S. military EP systems. IEPC (International Electric Propulsion Conference) proceedings (biennial) provide the most current research performance data.
