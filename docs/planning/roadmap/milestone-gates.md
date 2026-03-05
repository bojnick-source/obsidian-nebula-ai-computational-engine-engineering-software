# Milestone Gates

> Criteria that must be met to declare a milestone complete.

---

## Gate: Planning Baseline Freeze

**Passes when:**
- All P0 documents created and reviewed
- All contracts frozen (v1 status)
- All architecture docs complete
- v0.1 acceptance test written
- Risk register has ≥5 top risks with triggers and mitigations
- Decision log has ≥5 frozen ADRs
- FORGE Master Index accurate and current

**Artifacts:** This repo's planning scaffold.

---

## Gate: v0.1 MVP

**Passes when:**
- All 10 AC in `docs/planning/mvp/v0.1-acceptance-test.md` pass
- Live solver path (not stub) completes successfully
- All JSONL log completeness checks pass
- No unverified data found in vault after test run
- Amnesia check passes

**Artifacts:** Test run report in `forge-tests/reports/`

---

## Gate: v0.1a Fallback

**Passes when:**
- All 6 AC in `docs/planning/mvp/v0.1a-fallback-spec.md` pass
- Degraded mode activation is logged correctly
- Stub result is clearly flagged in vault and output

---

## Gate: V1

**Passes when:**
- All V1 scope items integrated (per tiered-roadmap.md)
- Full red-team verifier pass (catch rate ≥ targets in `forge-verification/docs/catch-rate-targets.md`)
- Provider failover path tested
- HashiCorp Vault secrets operational
- Vanguard pipeline has a passing happy-path run
- Cost tracking events operational

---

## Gate Checklist Template

For each gate:
1. Run acceptance test suite
2. Review log completeness
3. Review vault state post-test
4. Update `FORGE_MASTER_INDEX.md` with gate result
5. Tag release in git
