# FORGE Risk Register

> Top risks with triggers and mitigations. Review at each milestone gate.

---

## Risk Table

| ID | Risk | Likelihood | Impact | Trigger | Mitigation | Status |
|---|---|---|---|---|---|---|
| R-01 | Solver subprocess unreliability (CalculiX/GMSH) | Medium | High | >2 consecutive CI failures | Degraded mode: stub solver + manual review flag | Open |
| R-02 | Vault amnesia (memory not persisting/retrieving) | Low | Critical | Retrieval sanity test fails | Halt pipeline; vault is hard dependency; restore from snapshot | Open |
| R-03 | Planning scope creep before build starts | High | Medium | New subsystem added without P0 justification | Planning cut line; addendum intake rules enforced | Open |
| R-04 | Agent output contract drift | Low | High | Schema validation errors in production | Frozen interface policy; version bump required for changes | Open |
| R-05 | LLM provider outage (primary) | Medium | High | Health check fails >30s | Failover chain to secondary; degraded mode activation | Open |
| R-06 | Confidence miscalibration (overconfident wrong answers) | Medium | Critical | Red-team fixture misses increase | Adversarial verifier + red-team regression suite | Open |
| R-07 | Hidden assumption propagation | High | High | Undetected assumptions in specialist output | Assumption gate in verification stack | Open |
| R-08 | Geometry import producing invalid FEA meshes | Medium | High | Non-manifold/bad normals detected post-import | Import validation gate; fail-fast before solver invocation | Open |
| R-09 | Contradiction injection corrupting vault | Low | High | Contradiction gate miss rate increases | Contradiction gate + vault backup/snapshot policy | Open |
| R-10 | Swan license blocking topology optimization path | Medium | Medium | License negotiation fails | FreeTO as primary fallback; beso as secondary | Open |

---

## Risk Heatmap

```
Impact
 Critical |        R-02                    R-06
     High |   R-05  R-04  R-08  R-09  R-07  R-01
   Medium |                          R-10
      Low |
          +----+----+----+----+----+----
           Low  Med  Med  High High High  Likelihood
```

---

## Review Schedule

| Phase | Review |
|---|---|
| Planning baseline freeze | Full register review |
| v0.1 gate | R-01, R-02, R-03 |
| V1 gate | Full register review |
| Monthly (during build) | R-01 through R-05 |

See `docs/planning/risk/risk-register.md` for detailed register with full context.
