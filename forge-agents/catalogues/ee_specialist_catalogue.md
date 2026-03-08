# EE Specialist — Catalogue

## 5 Canonical Examples

### Example 1: UAV Power Budget and Battery Sizing
**Input:** Fixed-wing UAV, 45-minute endurance, 250 W peak propulsion, 35 W avionics continuous, 8 W payload, 3.7 V LiPo pack architecture, target Dod = 80%.
**Agent behaviour:** Summed power loads by phase (climb 250 W × 4 min, cruise 95 W × 39 min, landing 120 W × 2 min), computed energy per phase, totalled to 71.4 Wh mission energy, de-rated to 80% DoD giving 89.3 Wh minimum capacity, applied Peukert correction for 15C peak rate, added 10% capacity margin for temperature, selected 6S 22,000 mAh (97.7 Wh) pack.
**Output:** 6S 22,000 mAh LiPo, 485 g, energy density 201 Wh/kg, peak discharge 132 A (6C), margin 9.3%.
**Why exemplary:** Phase-by-phase energy integration used rather than average power × time; Peukert effect and temperature de-rating applied explicitly; discharge C-rate verified against cell specification.

### Example 2: Signal Integrity Analysis for High-Speed Digital Link
**Input:** 1 Gbps LVDS trace on 4-layer PCB, 22 cm length, target bit error rate <10⁻¹², stackup FR4 ε_r = 4.3.
**Agent behaviour:** Computed propagation delay T_pd = L√(ε_r)/c = 1.52 ns, characteristic impedance Z_0 = (87/√(ε_r + 1.41))·ln(5.98H/0.8W+T) using IPC-2141 microstrip formula targeting 100 Ω differential, analysed skin effect loss α_skin = R_s/(2Z_0) at 500 MHz (f_knee), computed dielectric loss α_d = π·f·√ε_r·tan_δ/c, flagged total insertion loss 5.8 dB at Nyquist; recommended GND via stitching every λ/20.
**Output:** Differential pair routed at 4/4 mil W/S, 100 Ω ±5%, insertion loss 5.8 dB (margin 2.2 dB vs 8 dB budget), eye height 185 mV at receiver.
**Why exemplary:** Skin effect and dielectric loss computed separately; eye diagram estimated from loss vs frequency before simulation; stackup impedance formula applied with actual layer geometry.

### Example 3: LDO vs Buck Converter Selection for Noise-Sensitive Analog Rail
**Input:** 3.3 V analog supply from 5 V input, 150 mA load, ADC with SNR requirement 90 dB, PCB area constrained to 20 mm².
**Agent behaviour:** Computed LDO power dissipation P = (5−3.3)×0.150 = 255 mW (requiring 2×2 mm QFN heatsink), computed Buck switching ripple V_r = ΔI_L·ESR + ΔI_L/(8·f·C) at 1 MHz = 3.2 mV, assessed Johnson noise floor from 90 dB SNR constraint (V_noise_max = 3.3V/10^(90/20) = 10.4 µV_rms), compared LDO PSRR (80 dB at 1 kHz, 40 dB at 1 MHz) vs Buck ripple passthrough, recommended LDO with pre-regulator 4.0 V Buck to cut LDO dissipation.
**Output:** Two-stage: switching pre-reg (5→4.0V, TPS62160) + LDO post-reg (4.0→3.3V, ADP7118); total P_diss = 105 mW; ripple at ADC <8 µV_rms; area 18.5 mm².
**Why exemplary:** Johnson noise floor derived from ADC SNR requirement to set ripple budget; two-stage architecture reached through heat analysis, not assumed.

### Example 4: Motor Driver MOSFET Selection for High-Efficiency ESC
**Input:** 3-phase BLDC, 48 V bus, 30 A continuous, 100 A peak (100 ms), f_sw = 20 kHz, T_ambient = 45 °C, target η > 97%.
**Agent behaviour:** Computed conduction loss P_cond = I²_RMS × R_DS(on) for each MOSFET pair; evaluated switching loss P_sw = 0.5·V_DS·I_D·(t_r+t_f)·f_sw from MOSFET datasheet; minimised P_total = P_cond + P_sw across candidate devices (GaN vs Si MOSFET); GaN (EPC2302: R_DS(on)=8.5 mΩ, t_r=3 ns) outperformed Si MOSFET (R_DS(on)=4.5 mΩ but t_r=35 ns) above 15 kHz; thermal resistance chain calculated to verify T_j < 150 °C.
**Output:** EPC2302 GaN FET, P_total = 9.8 W per phase (3% loss), η = 97.1%, T_j = 127 °C with 6 cm² copper pour heatsink.
**Why exemplary:** Switching loss computed from actual waveform parameters not rule-of-thumb; GaN vs Si crossover frequency explicitly derived; thermal chain verified end-to-end.

### Example 5: EMI Filter Design for Conducted Emissions Compliance
**Input:** DC-DC converter, 200 kHz switching, measured conducted emissions 22 dBµV above CISPR 25 Class 5 limit at 200 kHz, insertion loss target 25 dB.
**Agent behaviour:** Separated common-mode (CM) and differential-mode (DM) emission paths using current probe measurement; computed required filter topology (LC π-filter for DM, CM choke for CM), designed DM inductor L = 22 µH / C = 10 µF for f_cutoff = 10 kHz (40 dB/decade slope → 36 dB attenuation at 200 kHz), added 6 dB CM choke, verified resonance damping R_damp = √(L/C)/2, ensured no parallel resonance with source impedance.
**Output:** CM choke 100 µH + DM LC (22 µH / 10 µF / 2.2 Ω damping), insertion loss 38 dB at 200 kHz, CISPR 25 Class 5 compliance with 13 dB margin.
**Why exemplary:** CM/DM current separation done first; resonance damping resistor sized to prevent peaking; source impedance interaction checked.

## Thinking Parameters

### Primary Questions (ask before every task)
1. What is the power flow path — source to load — and where are the dominant loss mechanisms (conduction, switching, quiescent, thermal)?
2. What is the noise/signal budget, and have I traced every signal from source to destination accounting for losses, reflections, crosstalk, and EMI coupling paths?
3. Have I checked both steady-state and transient conditions — startup, fault, ESD — for every component operating point?
4. Is the thermal management adequate: have I computed junction temperatures for every power semiconductor under worst-case ambient and load?
5. Does the design comply with applicable standards (CE/FCC, CISPR, IEC, MIL-STD-461), and have I allocated margin for production variation?

### Domain Priors
- Power budgets must be built phase-by-phase; average power × time underestimates peak thermal stress and battery sizing.
- Signal integrity problems are almost always impedance discontinuities, return path gaps, or insufficient decoupling — check these first before simulating.
- Switching losses dominate at high frequency; conduction losses dominate at low frequency; there is an optimal switching frequency that minimises total loss for a given topology.
- MOSFET R_DS(on) increases 2–3× from 25 °C to 150 °C; thermal runaway is possible in parallel MOSFET arrays without careful matching.
- EMI problems found in test cost 10–50× more to fix than those caught in design — plan CM choke and ground stitch pads as standard practice.
- Johnson (thermal) noise V_n = √(4kTRΔf) sets the noise floor for any resistive circuit element; it cannot be reduced by circuit design, only by reducing R, T, or bandwidth.

### Metacognitive Flags
| Signal | Trigger condition | Action |
|---|---|---|
| Thermal runaway risk | Junction temperature within 15 °C of T_j_max under worst case | Revisit heatsink or de-rate; add thermal shutdown monitor |
| Impedance mismatch | Trace Z₀ changes > 20% without matching network | Flag SI risk; require TDR simulation or measurement |
| Power budget overage | Peak power draw exceeds battery C-rate × capacity | Re-evaluate motor sizing or upgrade cell chemistry |
| Missing decoupling | Switching IC within 2 cm of ADC without decoupling plan | Flag EMI coupling; require 100 nF + 10 µF per power pin within 5 mm |
| Standard ambiguity | EMI standard not confirmed for target market | Halt EMI filter design; confirm CISPR 25 / CISPR 32 / MIL-STD-461 applicability |
| Ground plane gap | Split ground plane or via stitching gap under high-speed return current path | Flag as SI/EMI risk; recommend continuous reference plane |

## Dead Feedback — Common Failure Modes

| Failure Mode | Symptom | Root Cause | Correction |
|---|---|---|---|
| Average-power battery sizing | Battery depletes in field before nominal endurance | Peak phase energy not accounted for; Peukert correction omitted | Redo energy budget phase-by-phase; apply Peukert n exponent |
| R_DS(on) at 25 °C used | MOSFET overheats in production | Datasheet max R_DS(on) at 25 °C used; temperature coefficient ignored | Use R_DS(on) × k_T(T_j) where k_T ≈ 2.5 at 150 °C |
| CM choke omitted | Fails CISPR 25 conducted emissions at first attempt | DM filter sized but CM path through chassis not considered | Add CM choke; measure CM vs DM current separately |
| Bypass capacitor resonance | Unexpected noise peak at 10–50 MHz | Parallel resonance between bypass cap ESL and adjacent capacitance | Add series damping resistor; use multi-value decoupling (1 nF || 100 nF || 10 µF) |
| Trace impedance ignored | BER >10⁻⁹ on high-speed link | 50 Ω source driving 75 Ω trace without matching; reflections degrade eye | Match impedance at source and load; control trace width to target Z₀ |

## Skill Refinements (v1.0 → next)
- What works well: Power budget construction, MOSFET loss analysis, EMI filter topology design, signal integrity impedance analysis, thermal chain calculation.
- What needs improvement: RF/microwave matching network design (Smith chart fluency), multi-phase power converter control loop design (type-III compensator), mixed-signal PCB floor-planning heuristics.
- Proposed v1.1 additions: Integrate SPICE netlist generation for filter verification; add antenna gain and link budget analysis for RF subsystems; incorporate IPC-2141/IPC-2152 current-carrying capacity formulae for trace sizing.

## Theoretical Physics Foundations

**Maxwell's Equations as the Foundation of Circuit Theory.** All of electrical engineering ultimately reduces to Maxwell's equations: ∇×E = −∂B/∂t (Faraday), ∇×H = J + ∂D/∂t (Ampère-Maxwell), ∇·D = ρ_free (Gauss electric), ∇·B = 0 (Gauss magnetic). Kirchhoff's voltage law (∮E·dl = 0) is the quasi-static approximation of Faraday's law when ∂B/∂t is small, valid when circuit dimensions ≪ λ. At microwave frequencies, lumped circuit theory breaks down and distributed transmission-line analysis (telegrapher's equations) is required: ∂V/∂x = −L'∂I/∂t − R'I; ∂I/∂x = −C'∂V/∂t − G'V.

**Skin Effect and Frequency-Dependent Losses.** At high frequencies, current concentrates in a surface layer of depth δ_s = √(2ρ/ωµ), where ρ is resistivity, ω = 2πf, and µ is permeability. For copper at 100 MHz, δ_s ≈ 6.6 µm, far smaller than typical trace thickness. Surface resistance R_s = ρ/δ_s = √(ρωµ/2). For a trace of width w, the AC resistance per unit length R' = R_s/(2w) (both sides). Skin effect increases insertion loss as √f, while dielectric loss increases as f·tan_δ. The crossover where dielectric loss exceeds skin loss occurs near f_cross = R_s²/(ρ_d²·π·ε_r·tan_δ²·Z₀²) depending on geometry — this sets the FR4 vs low-loss laminate decision boundary for high-speed designs.

**Johnson-Nyquist Noise.** Any resistor R at temperature T generates thermal noise with power spectral density S_V = 4kTR (V²/Hz), derived by Nyquist from the fluctuation-dissipation theorem. The RMS noise voltage in bandwidth B is V_n = √(4kTRB). For R = 50 Ω, T = 290 K, B = 1 GHz: V_n = 28 nV_rms. This sets the fundamental noise floor for amplifiers and ADC input circuits. Noise figure F = (SNR_in)/(SNR_out) quantifies how much a device degrades the signal-to-noise ratio; the Friis formula chains noise figures of cascaded stages: F_total = F₁ + (F₂−1)/G₁ + (F₃−1)/(G₁G₂) + ...

**Semiconductor Physics and the p-n Junction.** The MOSFET is the workhorse of power electronics. In the saturation region, drain current I_D = (µ_n C_ox W/2L)(V_GS − V_th)². The on-state resistance R_DS(on) = 1/(µ_n C_ox (W/L)(V_GS − V_th)) increases with temperature due to reduced carrier mobility: µ_n(T) ∝ T^(−2.3) for electrons in silicon. For GaN HEMTs, the 2DEG (two-dimensional electron gas) at the AlGaN/GaN interface achieves µ_n > 1500 cm²/V·s at room temperature, enabling R_DS(on)·A_device (specific on-resistance) 10–100× lower than silicon for the same breakdown voltage, following the theoretical limit: R_sp,min = 4V_B²/(ε_s µ_n E_c³).

**Electromagnetic Compatibility — Near-Field Coupling.** Capacitive coupling between traces: I_coupled = C_m · dV/dt, where C_m is mutual capacitance (pF/cm for adjacent PCB traces with small separation). Inductive coupling: V_induced = M · dI/dt, where M is mutual inductance. The backward crosstalk coefficient K_B = (L_m/L + C_m/C)/4 for microstrip lines. Crosstalk is minimised by: reducing parallel trace length, increasing separation (crosstalk ∝ 1/d² for microstrip), using differential signalling (common-mode rejection), and maintaining an unbroken return current path under the aggressor trace.

## Mathematical Framework

**Complex Impedance and Phasors.** For sinusoidal steady state, V = IZ where Z_R = R, Z_L = jωL, Z_C = 1/(jωC). Series RLC resonance at ω₀ = 1/√(LC), quality factor Q = ω₀L/R = 1/(ω₀CR). Parallel RLC: Z_max = R_p at resonance. Transfer function H(s) = V_out(s)/V_in(s) in Laplace domain; frequency response H(jω) by substituting s → jω.

**Power Electronics Loss Modelling.** Total converter loss: P_loss = P_cond + P_sw + P_core + P_gate + P_Q. Conduction loss for MOSFET: P_cond = I²_RMS · R_DS(on)(T_j). Switching loss: P_sw = (1/2)·V_DS·I_D·(t_r + t_f)·f_sw + Q_oss·V_DS·f_sw. Gate drive loss: P_gate = Q_g·V_gate·f_sw. Core loss (Steinmetz): P_core = k·f^α·B̂^β·V_core, where α ≈ 1.5–2.5, β ≈ 2–3 for common ferrite materials.

**Filter Design — Butterworth LC.** N-th order Butterworth low-pass filter has maximally flat magnitude response: |H(jω)|² = 1/(1 + (ω/ω_c)^(2N)). Component values from normalised prototype scaled to desired ω_c and impedance level Z_0: L_k = L_k,norm · Z_0/ω_c; C_k = C_k,norm/(Z_0·ω_c). Insertion loss at frequency f > f_c: IL ≈ 20N·log₁₀(f/f_c) dB (far from cutoff). For EMI filters, N = 2 (single LC) gives 40 dB/decade; N = 3 gives 60 dB/decade.

**Signal Integrity — Transmission Line.** Characteristic impedance: Z₀ = √((R' + jωL')/(G' + jωC')). For lossless line: Z₀ = √(L'/C'). Reflection coefficient at load: Γ_L = (Z_L − Z₀)/(Z_L + Z₀). Voltage standing wave ratio: VSWR = (1 + |Γ|)/(1 − |Γ|). Time-domain reflectometry (TDR) locates discontinuities by time-of-flight: Δt = 2·d·√ε_eff/c.

**Battery Peukert Correction.** Effective capacity C_eff = C_rated·(I_rated/I_discharge)^(n−1), where n is the Peukert exponent (n ≈ 1.05–1.15 for LiPo, 1.2–1.3 for lead-acid). At high discharge rates, available capacity is significantly reduced; this correction prevents underestimating required pack size.

## Historical Context

- **1827** — Georg Ohm publishes V = IR; establishes quantitative relationship between voltage, current, and resistance.
- **1831** — Michael Faraday discovers electromagnetic induction; establishes basis for transformers and generators.
- **1845** — Kirchhoff formulates KCL and KVL from charge conservation and energy conservation.
- **1865** — James Clerk Maxwell publishes "A Dynamical Theory of the Electromagnetic Field"; unifies electricity, magnetism, and light.
- **1880s** — Oliver Heaviside reformulates Maxwell's 20 equations into 4 vector equations; introduces impedance concept and transmission-line analysis.
- **1906** — Lee de Forest invents the triode vacuum tube; enables amplification and active circuits.
- **1927** — Nyquist and Johnson independently derive thermal noise formula; Shannon later links to information theory.
- **1947** — Bardeen, Brattain, and Shockley demonstrate bipolar junction transistor at Bell Labs.
- **1960** — Kao and Hofstein demonstrate MOSFET; becomes dominant device in VLSI.
- **1973** — SPICE (Simulation Program with Integrated Circuit Emphasis) released from UC Berkeley; transforms circuit design methodology.
- **1990s** — Power factor correction ICs and PWM controllers enable switch-mode power supply proliferation.
- **2004** — GaN-on-Si HEMT demonstrated for power electronics; commercial GaN FETs reach market 2010.
- **2010s** — PCIe Gen3/4 drives signal integrity from MHz to 8–16 GHz; loss-managed PCB laminates (Megtron 6, Tachyon 100G) become standard.
- **2020** — GaN at 650 V achieves volume production; wide-bandgap power electronics mainstreamed.

## Current State of the Art (2025–2026)

**GaN and SiC Power Semiconductors.** GaN Systems, EPC, Navitas, and STMicroelectronics offer 650 V GaN FETs with R_DS(on) < 25 mΩ in QFN packages. SiC MOSFETs (Wolfspeed, Infineon, STM) dominate >900 V applications with R_DS(on) as low as 15 mΩ at 1200 V. The theoretical specific on-resistance advantage of GaN vs Si is >100× at 650 V. Integrated gate drivers with built-in protection (overcurrent, thermal, UVLO) in same package (GaN ICs: Navitas NV6115) are reducing BOM and improving reliability.

**Digital Twin PCB Simulation.** Cadence Clarity 3D, Ansys SIwave, and Keysight ADS provide full-wave EM simulation of PCB structures with automatic port extraction. Automated SI/PI co-simulation workflows extract S-parameters from layout and feed IBIS/SPICE models for time-domain eye diagram prediction. AI-assisted routing (Cadence Cerebrus, Synopsys DSO.ai) optimises routing for signal integrity constraints.

**AI-Assisted Schematic and Layout Generation.** LLM-based tools (Flux.ai, Bria, Copilot for PCB) generate schematic netlists from natural-language specifications and auto-place components based on signal flow. As of 2025, these tools handle reference design adaptation reliably but require human review for power integrity and EMI compliance. Formal methods for circuit verification (model checking of timing and functional properties) are emerging in safety-critical automotive designs.

**Battery Technology.** LFP (LiFePO₄) cells achieve 160–180 Wh/kg at cell level with >4000 cycle life; dominant in UAV and EV applications where cycle life outweighs energy density. Silicon-anode NMC cells (Sion Power Licerion, Amprius Si) achieve >400 Wh/kg at cell level in 2024 demonstrations, targeting next-generation HAPS and long-endurance UAV. Solid-state batteries (Toyota, Samsung SDI) approaching commercialisation with 2025–2027 timeline for automotive packs at >500 Wh/L.
