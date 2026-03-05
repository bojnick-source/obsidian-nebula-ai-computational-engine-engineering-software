# FORGE Risk Register (Detailed)

> Full risk register with context. See RISK_REGISTER.md at repo root for summary.

---

## R-01: Solver Subprocess Unreliability

**Likelihood:** Medium
**Impact:** High
**Phase:** Build / production

**Context:** CalculiX and GMSH are invoked as subprocess tools via MCP wrappers. Subprocess-based invocation is inherently fragile — version mismatches, malformed input, filesystem issues, and resource limits can all cause failures. At MVP, these tools are the only path to a real FEA result.

**Trigger:** >2 consecutive CI failures in wrapper smoke tests OR >3 consecutive failures in production

**Mitigation:**
1. Implement degraded mode (`SWITCH_STUB_SOLVER`) before any live invocation
2. Wrapper smoke tests in CI nightly
3. Timeout and resource limits enforced in sandbox
4. Error codes logged for every failure
5. Wrapper specs written before implementation

**Owner:** Lane E (tool wrappers)

---

## R-02: Vault Amnesia

**Likelihood:** Low
**Impact:** Critical (pipeline-stopping)

**Context:** If notes written to the vault are not retrievable immediately after write, the memory system is broken. The system cannot operate reliably without persistent memory. This is treated as a hard dependency.

**Trigger:** Retrieval sanity test (amnesia check) fails

**Mitigation:**
1. Amnesia check is mandatory after every vault write (cannot be disabled)
2. Vault backup policy with integrity checks
3. Git-backed vault (every write is a commit)
4. Restore procedures documented and tested

**Owner:** Lane C (memory core)

---

## R-03: Planning Scope Creep

**Likelihood:** High
**Impact:** Medium

**Context:** FORGE is a large system with many attractive R&D directions. Without discipline, planning can continue indefinitely, blocking build from starting.

**Trigger:** New subsystem added to P0 scope without justification; planning phase exceeds N weeks without a build start

**Mitigation:**
1. Planning cut line enforced (mvp-cut-line.md)
2. Addendum intake rules (does it affect MVP critical path?)
3. P0/P1/P2 tagging applied to all planning items
4. Planning baseline freeze declared when P0 items are complete

**Owner:** Program level

---

## R-04: Agent Output Contract Drift

**Likelihood:** Low
**Impact:** High

**Context:** If agent prompts produce outputs that don't conform to the contract, all downstream consumers (verification, vault) break. Contract drift is hard to detect without automated validation.

**Trigger:** Schema validation errors in production; contract gate miss rate increases

**Mitigation:**
1. Agent output contract is frozen (v1)
2. Contract gate is mandatory in verification stack
3. Prompt tests include contract conformance assertions
4. Contract changes require ADR + version bump

**Owner:** Lane D (agents), Lane F (verification)

---

## R-05: LLM Provider Outage

**Likelihood:** Medium
**Impact:** High

**Context:** FORGE depends on LLM providers for all specialist agent outputs. A provider outage halts all non-lite tasks. At MVP with single provider, there is no failover.

**Trigger:** Primary provider health check fails for >30s

**Mitigation:**
1. Degraded mode `DEGRADED_PROVIDER` defined and documented
2. Provider failover chain planned for V1
3. Lite mode (non-LLM path) for non-engineering tasks
4. Task queue with retry for transient outages

**Owner:** Lane H (ops)

---

## R-06: Confidence Miscalibration

**Likelihood:** Medium
**Impact:** Critical (engineering safety)

**Context:** If the system produces high-confidence incorrect engineering answers, downstream design decisions may be based on flawed data. This is the highest-risk failure mode from an engineering safety perspective.

**Trigger:** Red-team fixture miss rate increases; adversarial verifier challenges not caught

**Mitigation:**
1. `what_would_falsify` field mandatory in all findings
2. Adversarial verifier (V1) specifically targets overconfident claims
3. Red-team fixture pack with known-wrong outputs
4. Confidence calibration gate (V1)
5. Human review for high-consequence findings

**Owner:** Lane F (verification)

---

## R-07: Hidden Assumption Propagation

**Likelihood:** High
**Impact:** High

**Context:** Specialist agents may embed assumptions (e.g., linear elastic behavior near yield, quasi-static loading) without making them explicit. These hidden assumptions can invalidate engineering conclusions.

**Trigger:** Post-hoc review discovers undisclosed assumptions in vault findings

**Mitigation:**
1. Agent output contract requires explicit `assumptions` list (empty list OK, null not OK)
2. Assumption gate (V1) scans for hidden assumptions using adversarial LLM call
3. `what_would_falsify` encourages assumption disclosure
4. ME specialist prompt v1.0.0 explicitly instructs assumption disclosure

**Owner:** Lane D (agents), Lane F (verification)

---

## R-08: Geometry Import Invalid for FEA

**Likelihood:** Medium
**Impact:** High

**Context:** CAD geometry imported from external tools (CATIA, Blender, Fusion360) may be visually correct but invalid for FEA — non-manifold meshes, incorrect normals, wrong scale, missing thickness.

**Trigger:** GMSH fails to mesh imported geometry OR CalculiX produces non-physical results on imported geometry

**Mitigation:**
1. Import validation gate (V1) — fail-fast before solver invocation
2. Classification gate: visual-only vs. engineering-ready
3. Geometry validation spec: `docs/toolchain/geometry-import-validation.md`
4. At MVP: only programmatically generated test geometry (no CAD import in scope)

**Owner:** Lane E (tools), Lane J (external ecosystem)

---

## R-09: Contradiction Injection Corrupting Vault

**Likelihood:** Low
**Impact:** High

**Context:** If contradictory information is written to the vault without detection, subsequent reasoning may be based on inconsistent premises, compounding errors over time.

**Trigger:** Contradiction gate miss rate increases; vault contains conflicting findings for same quantity

**Mitigation:**
1. Contradiction gate (V1) checks all findings against existing vault entries
2. Disputed note tier prevents overwriting (versioning)
3. Overwatch flag on all disputes
4. Vault integrity checks in nightly CI

**Owner:** Lane F (verification), Lane C (memory)

---

## R-10: Swan License Blocking Topology Optimization

**Likelihood:** Medium
**Impact:** Medium

**Context:** Swan (topology optimization library from academic researchers) has uncertain licensing for commercial use. Phoenix pipeline prefers Swan for advanced topology optimization.

**Trigger:** License negotiation fails or is too restrictive

**Mitigation:**
1. FreeTO as primary topology optimization tool (open-source, no license risk)
2. beso as V1 secondary fallback
3. Swan tracked as R&D conditional
4. OpenLSTO evaluated as alternative

**Owner:** Lane E (tools)

---

## Review Log

| Date | Reviewed By | Changes |
|---|---|---|
| 2026-03-05 | Planning phase | Initial register created |
