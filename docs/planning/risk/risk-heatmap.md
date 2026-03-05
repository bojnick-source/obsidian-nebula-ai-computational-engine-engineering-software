# Risk Heatmap

```
         │ Low Impact │ Med Impact │ High Impact │ Critical Impact
─────────┼────────────┼────────────┼─────────────┼─────────────────
High     │            │    R-03    │   R-07      │
Likeli.  │            │            │             │
─────────┼────────────┼────────────┼─────────────┼─────────────────
Med      │            │    R-10    │ R-01, R-05  │  R-06
Likeli.  │            │            │ R-08        │
─────────┼────────────┼────────────┼─────────────┼─────────────────
Low      │            │            │ R-04, R-09  │  R-02
Likeli.  │            │            │             │
```

## Priority Order (for mitigation effort)

1. R-06 — Confidence miscalibration (medium likelihood, critical impact) — engineering safety
2. R-02 — Vault amnesia (low likelihood, critical impact) — system integrity
3. R-01 — Solver unreliability (medium likelihood, high impact) — MVP critical path
4. R-07 — Hidden assumptions (high likelihood, high impact) — engineering safety
5. R-05 — Provider outage (medium likelihood, high impact) — availability
6. R-03 — Scope creep (high likelihood, medium impact) — planning discipline
7. R-08 — Geometry import (medium likelihood, high impact) — V1 concern
8. R-09 — Contradiction injection (low likelihood, high impact) — V1 concern
9. R-04 — Contract drift (low likelihood, high impact) — architectural integrity
10. R-10 — Swan license (medium likelihood, medium impact) — tool availability
