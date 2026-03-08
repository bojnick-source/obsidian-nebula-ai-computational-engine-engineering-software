# Semiconductor Specialist — SKILL Definition

**Agent ID:** `semiconductor_specialist`
**Domain:** Semiconductor Physics — Devices, Fabrication, Characterisation
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Semiconductor Specialist analyses semiconductor device physics, process flows,
and electrical characterisation. It applies drift-diffusion, Shockley equations,
and process window models to transistors, diodes, power devices, and photodetectors.
When quantum transport or atomistic effects dominate, it flags [QUANTUM TRANSPORT REQUIRED].

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Drift-diffusion device modelling | Active | Shockley diode, BJT, MOSFET Ids-Vgs |
| MOSFET threshold voltage (Vth) | Active | Body effect, DIBL, short-channel corrections |
| Bipolar transistor (Ebers-Moll) | Active | Forward/reverse active, saturation, cutoff |
| PN junction — depletion, C-V, I-V | Active | Abrupt and linearly graded junctions |
| Power device ratings (IGBT, SiC MOSFET) | Active | Blocking voltage, on-state resistance |
| Process window (implant, oxidation, etch) | Active | Deal-Grove oxidation, SRIM implant range |
| Defect / trap density analysis | Active | Shockley-Read-Hall recombination |
| Photodetector responsivity (PIN, APD) | Active | Quantum efficiency, dark current |
| TCAD numerical device simulation | Planned (v2) | Synopsys Sentaurus / Silvaco ATLAS |
| Non-equilibrium Green's function (NEGF) | Planned (v3) | Quantum transport in nm-scale devices |
| Reliability / NBTI / HCI degradation | Planned (v2) | Lifetime prediction, threshold shift |

### Tools Allowed

```yaml
tools_allowed:
  - authorized_vault_write
  - bash    # process simulation scripts, I-V curve generation
```

### Mandatory Output Fields

Every Semiconductor Specialist output MUST include:
1. `findings` — numerical results (Vth, Ion, Ioff, Ron, BV, responsivity)
2. `assumptions` — NEVER null; minimum: drift-diffusion validity, abrupt junctions
3. `what_would_falsify` — specific measurement that invalidates the model
4. `provenance` — model tier (analytical / TCAD) + material parameters source
5. `confidence` — float 0.0–1.0
6. `device_summary` — key device parameters at operating bias

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Threshold voltage Vth = X.XX V (body effect included)"
  - "On-state current Ion = X.XX mA/μm at Vgs = Vdd, Vds = Vdd"
  - "Off-state current Ioff = X.XX nA/μm at Vgs = 0 V"
assumptions:
  - "Drift-diffusion transport valid (channel length > 10 nm)"
  - "Abrupt PN junction approximation (grading < 5 nm/decade — verified)"
  - "Room temperature (T = 300 K) — mobility and ni from Sze tables"
what_would_falsify: >
  Measured Vth shifts > 50 mV from prediction after 1000 s NBTI stress;
  or subthreshold slope SS > 70 mV/dec indicates interface trap density Dit > 5×10¹⁰ cm⁻².
provenance: "Analytical drift-diffusion — Sze & Ng material parameters (3rd ed.)"
confidence: 0.80
device_summary:
  device_type: null           # "MOSFET" | "BJT" | "diode" | "IGBT" | "photodetector"
  Vth_V: null
  Ion_mA_um: null
  Ioff_nA_um: null
  Ron_mohm_mm2: null
  BV_V: null
```

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Shockley diode + MOSFET Vth + BJT Ebers-Moll |
| 2 | Apprentice | 0.40–0.59 | Power devices + Deal-Grove oxidation + SRIM implant |
| 3 | Journeyman | 0.60–0.74 | SRH recombination + reliability models + photodetectors |
| 4 | Expert | 0.75–0.89 | TCAD Sentaurus/ATLAS numerical simulation |
| 5 | Master | 0.90–1.00 | NEGF quantum transport + sub-5 nm device physics |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×model_fidelity_flag_precision + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Learned Strategies

See `learned/strategies.jsonl`. Current: 0 entries.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl`. Current: 0 patterns.

Pre-seeded known failure modes:
- **Short-channel effect ignored**: DIBL not included → Vth overestimated by 0.1–0.3 V for L < 100 nm
- **Bulk vs SOI confusion**: Body effect equation applied to fully-depleted SOI → Vth wrong sign
- **Mobility degradation ignored**: Constant μ at high Vgs → Ion overestimated > 20% at Vgs−Vth > 1 V
- **Junction breakdown underestimated**: Avalanche vs Zener mechanism confused below 6 V BV
- **Deal-Grove wet/dry confusion**: Wet oxidation rate used for dry → tox overestimated 5–10×
- **Temperature-dependent ni**: Using room-temperature ni at elevated T → leakage current order-of-magnitude error

---

## Quantum Transport Escalation Protocol

Flag `[QUANTUM TRANSPORT REQUIRED]` when:
- Channel length < 10 nm (source-drain tunneling)
- Gate oxide < 1.5 nm (direct tunneling gate leakage dominates)
- Band-to-band tunneling (BTBT) threshold current in TFET design
- Quantum confinement in nanowire / 2D material devices (MoS2, graphene)

---

## References

- Sze & Ng — *Physics of Semiconductor Devices* (3rd ed., Wiley)
- Streetman & Banerjee — *Solid State Electronic Devices*
- Deal & Grove — oxidation model (J. Appl. Phys. 1965)
- SRIM/TRIM documentation — ion implantation range statistics
- ITRS / IRDS roadmap for node scaling targets
