# Tactical Switches

> Pre-approved scope reductions activated at 2× budget/time overrun. No approval needed at activation — they are pre-approved here.

---

## Switch Table

| Switch ID | Activation Condition | What Is Disabled | What Remains Mandatory | Re-enable Condition |
|---|---|---|---|---|
| `SWITCH_NO_ANTAGONIST` | Antagonist phase >2× budget | Antagonist debate, A2A debate lifecycle | Specialist + all verification gates | Overrun resolved; budget confirmed |
| `SWITCH_NO_ILC` | ILC generation >2× budget | ILC link generation, cluster synthesis | Core memory: intake, retrieval, strengthening | Overrun resolved |
| `SWITCH_LITE_VERIFY` | Verification phase >2× budget | Adversarial + contradiction + confidence calibration gates | Contract + unit + dimensional + provenance gates | Must be re-enabled before V1 |
| `SWITCH_STUB_SOLVER` | Solver subprocess >2× timeout | Live CalculiX/GMSH invocation | Task continues with stub result; gap flags required | Solver wrapper smoke test passes |
| `SWITCH_NO_SYNTHESIS` | Synthesis phase >2× budget | Memory synthesis proposals | Intake + retrieval + strengthening + contradiction handling | Overrun resolved |
| `SWITCH_LITE_MODE` | Full system >2× budget | Antagonist + ILC + adversarial + synthesis + live solvers | Specialist + basic verification + vault write | Full mode re-enabled manually |

---

## Logging Requirements

On activation, log:
```json
{
  "event": "tactical_switch_activated",
  "switch_id": "SWITCH_NO_ANTAGONIST",
  "trace_id": "...",
  "trigger": "antagonist_phase budget_overrun_2x",
  "activated_at": "ISO8601",
  "disabled_components": ["antagonist_debate", "a2a_debate_lifecycle"]
}
```

On deactivation:
```json
{
  "event": "tactical_switch_deactivated",
  "switch_id": "SWITCH_NO_ANTAGONIST",
  "deactivated_at": "ISO8601",
  "duration_seconds": 3600
}
```

---

## Configuration

Tactical switch thresholds configured in `forge-core/configs/degraded_modes.yaml`.
