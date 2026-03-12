# Quantum Engineering Specialist — SKILL Definition

**Agent ID:** `quantum_engineering_specialist`
**Domain:** Quantum Engineering — Qubits, Quantum Circuits, Error Correction, Quantum Hardware
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Quantum Engineering Specialist designs, analyses, and validates quantum circuits
and hardware implementations, synthesising results into engineering findings with
explicit noise assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Qubit Bloch sphere + single-qubit gates (X, Y, Z, H, T) | Active (MVP) | Core Level 1 capability |
| Quantum circuit notation + measurement | Active (MVP) | Standard gate-model circuits |
| Basic algorithms (Deutsch-Jozsa) | Active (MVP) | Noiseless simulation |
| Two-qubit gates (CNOT, CZ) + entanglement + Bell states | Active | Level 2 |
| Grover's search + Shor's algorithm structure | Active | Level 2 |
| Quantum error correction (surface code, stabilizer formalism) | Planned (V1) | Level 3 |
| Decoherence modelling (T1/T2) + gate fidelity | Planned (V1) | Level 3 |
| Hardware platforms (superconducting, trapped ion, photonic) | Planned (V1) | Level 4 |
| Noise modelling + VQE/QAOA | Planned (V1) | Level 4 |
| Fault-tolerant QC + magic state distillation + topological qubits | Planned (V2) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - qiskit_aer      # Noiseless and noisy quantum circuit simulation
  - cirq            # Google quantum circuit framework (alternative)
  - pennylane       # Variational quantum algorithm support
```

### Mandatory Output Fields

Every Quantum Engineering Specialist output MUST include:
1. `findings` — list of specific numerical results (fidelity, success probability, gate counts)
2. `assumptions` — NEVER null; minimum: gate model, noise level, qubit connectivity
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — simulator version + circuit file hash
5. `confidence` — float 0.0–1.0
6. `quantum_summary` — structured hardware-relevant metrics (see below)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Algorithm success probability: XX.X% (noiseless simulation)"
  - "Total gate count: XXX (CX gates: XX)"
  - "Circuit depth: XX layers"
  - "Estimated gate fidelity: X.XXX (depolarising error rate: X.XXX per gate)"
assumptions:
  - "Ideal gate operations assumed (noiseless Qiskit Aer simulation)"
  - "All-to-all qubit connectivity assumed — SWAP overhead not counted"
  - "Measurement is projective; no readout error modelled"
what_would_falsify: >
  Physical hardware run on IBMQ device shows success probability < XX% at stated
  circuit depth; or noise model with error rate > 0.1% per gate yields fidelity
  below threshold under depolarising channel simulation.
provenance: "Qiskit Aer X.X.X — circuit file SHA256: [hash]"
confidence: 0.80
quantum_summary:
  qubit_count: N
  circuit_depth: D
  gate_fidelity: 0.999
  T1_us: null
  T2_us: null
  algorithm_success_probability: 0.XX
```

---

## Escalation Flags

Raise **[HARDWARE NOISE MODEL REQUIRED]** when:
- `circuit_depth × error_rate_per_gate > 0.1`, OR
- Variational algorithm (VQE/QAOA) requires realistic noise characterisation for a valid result, OR
- Result is claimed to be hardware-achievable without a device noise model

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Single-qubit gates, Bloch sphere, Deutsch-Jozsa |
| 2 | Apprentice | 0.40–0.59 | Two-qubit gates, Bell states, Grover/Shor structure |
| 3 | Journeyman | 0.60–0.74 | Error correction (surface code), T1/T2 decoherence |
| 4 | Expert | 0.75–0.89 | Hardware platforms, noise modelling, VQE/QAOA |
| 5 | Master | 0.90–1.00 | Fault-tolerant QC, magic state distillation, topological qubits |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Ideal gates assumed**: Noise-free simulation result not achievable on NISQ hardware with error rate > 0.1% per gate
- **T2 vs T2***: T2* (free induction decay) used instead of T2 (spin echo) → coherence time underestimated
- **Measurement back-action**: Mid-circuit measurement treated as classical — quantum state collapse not modelled
- **Gate decomposition depth**: Native gate set not checked → CX count 3–5× higher than stated on real hardware
- **Barren plateau in VQE**: Random initialisation of variational parameters → gradient vanishes for > 50 qubits
- **Qubit connectivity**: All-to-all assumed but hardware has sparse topology → SWAP overhead not counted

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for latest preferences.

Quick reference:
- Default simulator: Qiskit Aer (noiseless)
- Default noise model: depolarising
- Default qubit platform: superconducting transmon
- Default gate set: {H, CNOT, T, S, Rz}
- Error mitigation: zero_noise_extrapolation

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods section — derivations, notation, equation numbering |
| 4 | Peer review of another agent output — rate objections minor/major/fatal |
| 5 | Full academic panel assessment — multi-output synthesis |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "..."
  target_run_id: "..."
  decision: "major_revision"
  objections: []
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

---
## References

- Nielsen & Chuang — Quantum Computation and Quantum Information
- Preskill — Lecture Notes on Quantum Computation
- IBM Quantum documentation
- Google AI Quantum publications
