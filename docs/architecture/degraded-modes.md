# Degraded Modes

> Documented fallback behaviors when components fail. Every critical path must have a degraded mode.

---

## Degraded Mode Table

| Trigger | Component | Mode | Behavior | Re-entry Criteria |
|---|---|---|---|---|
| Primary LLM provider unavailable | Model Router | `DEGRADED_PROVIDER` | Route to secondary provider | Primary health check passes for >60s |
| All providers unavailable | Model Router | `DEGRADED_NO_LLM` | Halt non-lite tasks; queue for retry | Any provider health check passes |
| CalculiX subprocess fails 3× (3 failed attempts) | FEA Wrapper | `DEGRADED_SOLVER` | Stub solver output; flag result for manual review | Wrapper smoke test passes |
| GMSH subprocess fails 3× (3 failed attempts) | Mesh Wrapper | `DEGRADED_MESH` | Flag task; halt solver phase | Wrapper smoke test passes |
| Vault write fails 3× (3 failed attempts) | Memory System | `DEGRADED_VAULT_WRITE` | Halt pipeline; escalate | Vault write test passes |
| Vault read fails | Memory System | `DEGRADED_VAULT_READ` | Continue with empty context; add gap flags | Vault read test passes |
| Verification gate fails | Verification | `DEGRADED_VERIFY_FAIL` | Reject output; do not write to vault | — (output must be resubmitted) |
| Cost threshold exceeded | Cost Tracker | `DEGRADED_COST_LIMIT` | Pause task queue; alert; await approval | Budget approved or threshold raised |
| Secret rotation fails | Security | `DEGRADED_SECRETS` | Use cached credentials (time-limited); alert | Rotation confirmed |

---

## Tactical Switches (2× Overrun Scenario)

Tactical switches are pre-approved scope reductions that can be activated if a phase is running at 2× estimated budget/time.

| Switch | What it disables | What remains |
|---|---|---|
| `SWITCH_NO_ANTAGONIST` | Antagonist debate phase | Specialist + verification only |
| `SWITCH_NO_ILC` | ILC link generation | Core memory operations only |
| `SWITCH_LITE_VERIFY` | Adversarial + contradiction gates | Contract + unit + dimensional + provenance |
| `SWITCH_STUB_SOLVER` | Live solver invocation | Stub output with gap flags |
| `SWITCH_NO_SYNTHESIS` | Memory synthesis proposals | Intake + retrieval + strengthening only |

---

## Activation Logging

Every degraded mode or tactical switch activation is logged with:
- Timestamp
- Trigger event (trace_id, error_code)
- Mode activated
- Duration
- Re-entry timestamp (when resolved)

See `forge-ops/telemetry/` for log format.

---

## Degraded Mode Config

Degraded mode chains are configured in `forge-core/configs/degraded_modes.yaml`.
