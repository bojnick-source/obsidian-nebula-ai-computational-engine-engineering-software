# FORGE Execution Plan — Master Index

| Field        | Value                                          |
|--------------|-------------------------------------------------|
| Date         | 2026-03-04                                      |
| Status       | ACTIVE                                          |
| Authors      | FORGE Core Team                                 |
| Supersedes   | All prior planning fragments                    |
| Rule         | **Planning Freeze in effect — code only after this document** |

---

## 1. The DARK_leaf Lesson

### 1.1 What Happened

The DARK_leaf v2 project scored **71/100** on its evaluation rubric. An
analysis of lost points revealed a consistent pattern:

- **Planning over building**: Weeks spent on documents that earned zero points.
- **Scope explosion**: 68 agents designed, zero agents tested end-to-end.
- **Untested assumptions**: Architecture decisions made without validation
  experiments (e.g., C++ as the primary language, Supermemory as mandatory).
- **No freeze discipline**: New planning docs were created every session,
  displacing implementation work.

### 1.2 Why This Plan Exists

This master index is the **last planning document**. It consolidates all
prior planning into three canonical files and then invokes the Planning
Freeze Protocol (Section 10). Every session after this one must produce
code, tests, or validated vault content — not documents.

### 1.3 The Core Insight

> The rubric rewards working systems, not planning artifacts.
> Every hour spent planning after this point is an hour stolen from building.

---

## 2. Deduction-to-Fix Map

The following table maps each category of lost points to the specific fix
that FORGE implements. Target: raise the score from **71 → 93**.

| #  | Category                  | Points Lost | Root Cause                              | Fix                                              | Target Recovery |
|----|---------------------------|-------------|-----------------------------------------|--------------------------------------------------|-----------------|
| 1  | Untested agent pipeline   | −8          | No end-to-end test existed              | Pipeline Tester agent (TEST-01) + golden fixtures | +7              |
| 2  | No adversarial checks     | −5          | Verification was structural only        | Adversarial Verifier (V-ADV) at T=0.3            | +4              |
| 3  | Scope bloat               | −4          | 68 agents, none working                 | MVP Scope Lock: 7 agents only                    | +4              |
| 4  | No confidence scores      | −3          | Outputs lacked uncertainty quantification | Mandatory confidence field + scoring pipeline    | +3              |
| 5  | Planning displacement     | −3          | New docs every session, no code         | Planning Freeze Protocol                         | +3              |
| 6  | Missing provenance        | −2          | Results had no source tracking          | `sources` field mandatory in output contract     | +2              |
| 7  | No cost controls          | −2          | Unlimited API spend                     | Budget gate in model router                      | +1              |
| 8  | No gap detection          | −2          | Knowledge holes went untracked          | Librarian gap_flags + vault schema               | +2              |
|    | **Total**                 | **−29**     |                                         |                                                  | **+26 (→ 97 theoretical, 93 realistic)** |

The realistic target accounts for imperfect execution and the fact that some
points require V1 features (topology optimization, additional tool wrappers).

---

## 3. MVP Scope

### 3.1 Agents

7 agents only. See FORGE_CATALOG.md §4 for the full roster.

| ID       | Name                 | Milestone |
|----------|----------------------|-----------|
| ORCH-01  | Orchestrator         | M3        |
| E-01     | ME Specialist        | M4        |
| E-05     | Materials Specialist | M4        |
| V-STRUCT | Structural Verifier  | M4        |
| V-ADV    | Adversarial Verifier | M4        |
| LIB-01   | Librarian            | M3        |
| TEST-01  | Pipeline Tester      | M5        |

### 3.2 Memory

- **Primary**: Obsidian vault (local, file-based).
- **Optional**: Supermemory (API-based, degraded mode fallback).
- MVP ships with `memory.mode: "degraded"` in `forge.yaml`.

### 3.3 Tools

- **CalculiX** (T-01): Structural FEA solver. M6 deliverable.
- **GMSH** (T-06): Mesh generation. M6 deliverable.
- **FreeTO**: Deferred to V1 (Swan license, ADR-005).

---

## 4. Dependency Resolution

All external dependencies were audited. Each has a resolution and fallback.

| ID  | Dependency               | Status      | Resolution                                   | Fallback                         |
|-----|--------------------------|-------------|----------------------------------------------|----------------------------------|
| D1  | Anthropic API access     | ✅ Resolved | API key provisioned, claude-opus-4-6 available | Degrade to claude-sonnet-4-5     |
| D2  | OpenAI API access        | ✅ Resolved | API key provisioned, gpt-5.2 available       | Route to Anthropic frontier      |
| D3  | DeepSeek API access      | ⏳ Pending  | API key provisioned, model not yet validated  | Omit from roster until Week 2    |
| D4  | Supermemory API          | ⚠️ Optional | Attempted in M2, not required for MVP        | Obsidian-only degraded mode      |
| D5  | CalculiX + GMSH binaries | ⏳ Planned  | Install via package manager in M6            | Manual calculation fallback      |

---

## 5. The C++ Decision

### 5.1 Context

DARK_leaf v2 assumed C++ was necessary for performance. This assumption was
never validated. Meanwhile, weeks were spent on C++ toolchain setup instead
of agent implementation.

### 5.2 Decision

**Python is the MVP language.** (See ADR-001.)

### 5.3 Rationale

- Python has superior library support for LLM orchestration.
- The bottleneck is API latency (100–2000ms), not local compute.
- C++ port is scheduled for V1-17, **only if** Python latency exceeds targets:
  - Orchestration loop: < 500ms excluding API calls.
  - Blackboard read/write: < 10ms per operation.
  - Vault I/O: < 50ms per note.

### 5.4 Validation Gate

If any of the above latency targets are exceeded during M5 performance
testing, the C++ port is immediately scheduled for V1. If all targets are
met, C++ is deprioritized indefinitely.

---

## 6. Validation Experiments

Three experiments are scheduled to validate architectural assumptions before
committing to them irreversibly.

### 6.1 Experiment 1: Cost Model (Week 1)

| Field      | Value |
|------------|-------|
| Question   | What is the per-analysis API cost with the current provider fleet? |
| Method     | Run 10 representative engineering queries, measure token usage and cost |
| Success    | Average cost < $0.50 per analysis |
| Failure    | Average cost > $1.00 → re-evaluate model assignments |
| Deadline   | End of Week 1 |

### 6.2 Experiment 2: DeepSeek Validation (Week 2)

| Field      | Value |
|------------|-------|
| Question   | Can DeepSeek-Reasoner match claude-sonnet-4-5 quality on engineering tasks? |
| Method     | Run 5 golden-fixture problems through both models, blind comparison |
| Success    | DeepSeek scores within 10% of Sonnet on accuracy metrics |
| Failure    | DeepSeek scores > 10% below → remove from roster |
| Deadline   | End of Week 2 |

### 6.3 Experiment 3: Three-Class Agent Hierarchy (Week 3–4)

| Field      | Value |
|------------|-------|
| Question   | Does the Orchestrator → Specialist → Verifier hierarchy produce higher quality than flat dispatch? |
| Method     | Compare pipeline output vs. single-agent output on 5 test problems |
| Success    | Pipeline scores ≥ 15% higher on verification metrics |
| Failure    | Pipeline shows < 5% improvement → simplify to two-class hierarchy |
| Deadline   | End of Week 4 |

---

## 7. Revised Timeline

14–18 week Python MVP timeline. Scope-reduction trigger at Week 10.

| Week   | MS  | Phase                  | Deliverable                                       | Gate Criteria                              |
|--------|-----|------------------------|---------------------------------------------------|--------------------------------------------|
| 1      | M1  | Foundation             | Project skeleton, forge.yaml, CLI, logging, tests | `forge --version` prints, 10+ tests pass   |
| 2      | M2  | Memory & Routing       | Blackboard, model router, vault scaffold          | Router selects correct provider, blackboard R/W works |
| 3–4    | M3  | Core Agents I          | Orchestrator + Librarian agents functional        | 12-step loop executes with mock specialists |
| 5–6    | M4  | Core Agents II         | ME, Materials, Structural, Adversarial agents     | All 7 agents respond to test prompts       |
| 7–8    | M5  | Integration & Testing  | End-to-end pipeline, golden fixtures, Pipeline Tester | 3 golden fixtures pass, confidence scores generated |
| 9–10   | M6  | Tool Integration       | CalculiX + GMSH wrappers, tool-augmented analysis | FEA problem solved end-to-end              |
| 11–12  | M7  | Hardening              | Error handling, fallback chains, budget enforcement | Graceful degradation on provider failure   |
| 13–14  | M8  | Polish & Documentation | README, user guide, final vault content           | Demo-ready, documentation complete         |
| 15–18  | M9  | Buffer & Stretch       | Performance tuning, additional golden fixtures     | All rubric targets met                     |

### Scope-Reduction Trigger

At **Week 10**, evaluate progress against the timeline:

- If M5 is not complete → cut M6 tool integration from MVP, move to V1.
- If M4 is not complete → cut to 5 agents (defer V-ADV and TEST-01).
- If M3 is not complete → escalate; fundamental architecture issue.

---

## 8. Revised Rubric

Execution-weighted rubric reflecting the DARK_leaf lesson: building > planning.

| Category                         | Old Weight | New Weight | What Changed                              |
|----------------------------------|------------|------------|-------------------------------------------|
| Working agent pipeline           | 15         | 25         | Increased: this is the core deliverable   |
| Verification & confidence        | 10         | 15         | Increased: adversarial verification added |
| Knowledge persistence (vault)    | 10         | 12         | Slight increase: gap detection added      |
| Tool integration (FEA)           | 10         | 12         | Unchanged priority                        |
| Cost controls & budget           | 5          | 8          | Increased: was completely missing         |
| Testing (golden fixtures)        | 10         | 12         | Increased: Pipeline Tester is an agent    |
| Documentation & architecture     | 20         | 8          | **Decreased**: was overweighted           |
| Code quality & structure         | 10         | 5          | Slight decrease                           |
| Error handling & degradation     | 5          | 3          | Slight decrease                           |
| Planning & process               | 5          | 0          | **Removed**: no more points for planning  |
| **Total**                        | **100**    | **100**    |                                           |

---

## 9. Document Consolidation

7 prior planning documents have been consolidated into 3 canonical files.

| Old Document                     | Status    | Consolidated Into                   |
|----------------------------------|-----------|-------------------------------------|
| FORGE Architecture Overview      | Archived  | FORGE_CATALOG.md §2                 |
| Agent Roster (68 agents)         | Archived  | FORGE_CATALOG.md §4 (7 agents)     |
| Provider Fleet                   | Archived  | FORGE_CATALOG.md §3                 |
| Memory Architecture              | Archived  | FORGE_CATALOG.md §6                 |
| Timeline v1                      | Archived  | FORGE_EXECUTION_PLAN.md §7          |
| C++ vs Python Analysis           | Archived  | FORGE_EXECUTION_PLAN.md §5          |
| Decision Log                     | Archived  | DECISIONS.md                        |

All archived documents are preserved in `docs/planning/catalog/` with an
`ARCHIVE_NOTE.md` explaining their status.

---

## 10. Planning Freeze Protocol

### 10.1 The Rules

Effective immediately after this document is committed:

1. **No new planning documents.** If it's a `.md` file in `docs/planning/`,
   it must already exist.
2. **Edits to existing planning docs** are allowed only for factual corrections
   (typos, broken links, wrong dates). No structural changes.
3. **Every coding session must produce code.** A session that produces only
   notes or plans is a failed session.
4. **ADRs are the only exception.** New ADR entries may be added to
   `DECISIONS.md` when architectural decisions are made during implementation.
5. **Vault content is not planning.** Writing domain knowledge to the vault
   (e.g., `vault/domains/mechanical/beam_theory.md`) is considered building.
6. **CHANGELOG updates are mandatory.** Every session that changes code must
   update `CHANGELOG.md`.
7. **If in doubt, write code.** The tiebreaker always favors implementation.

### 10.2 What to Do Monday (Decision Tree)

```
Start of session
  │
  ├── Is there a failing test?
  │     YES → Fix it. Ship the fix. Update CHANGELOG.
  │     NO  ↓
  │
  ├── Is the current milestone deliverable incomplete?
  │     YES → Work on it. Write code + tests. Update CHANGELOG.
  │     NO  ↓
  │
  ├── Is there a validation experiment due this week?
  │     YES → Run it. Record results. Update DECISIONS.md if needed.
  │     NO  ↓
  │
  ├── Is there vault content to write?
  │     YES → Write it. This counts as building.
  │     NO  ↓
  │
  └── Advance to next milestone deliverable.
        Write code + tests. Update CHANGELOG.
```

---

## 11. Pre/Post Session Checklists

### 11.1 Pre-Session Checklist (Start of Every Coding Session)

- [ ] `git pull` — ensure latest code.
- [ ] Check `CHANGELOG.md` — what changed last session?
- [ ] Check timeline (§7) — what milestone are we in?
- [ ] Check for failing tests: `pytest tests/ -q`.
- [ ] Decide session goal: one concrete deliverable.
- [ ] Set a timer: no more than 30 minutes without a commit.

### 11.2 Post-Session Checklist (End of Every Coding Session)

- [ ] All tests pass: `pytest tests/ -q`.
- [ ] `CHANGELOG.md` updated with session changes.
- [ ] Code committed and pushed.
- [ ] No new planning documents created (Planning Freeze).
- [ ] Session produced code, tests, or vault content (not just plans).
- [ ] Note any blockers for next session in a commit message.

---

## 12. Risk Register

| ID   | Risk                           | Likelihood | Impact | Mitigation                                         |
|------|--------------------------------|------------|--------|-----------------------------------------------------|
| R-01 | Schedule slip (M5+ delayed)    | Medium     | High   | Scope-reduction trigger at Week 10 (§7)            |
| R-02 | Scope creep (agent additions)  | High       | High   | MVP Scope Lock doctrine; 7 agents only             |
| R-03 | Provider outage (Anthropic)    | Low        | High   | Fallback chain in model router; multi-provider fleet |
| R-04 | Provider outage (OpenAI)       | Low        | High   | Fallback chain in model router; multi-provider fleet |
| R-05 | Budget overrun (API costs)     | Medium     | Medium | Budget gate, daily ceiling, cost validation (§6.1) |
| R-06 | DeepSeek quality insufficient  | Medium     | Low    | DeepSeek is optional; remove from roster if fails   |
| R-07 | Supermemory unavailable        | High       | Low    | Already in degraded mode; Obsidian-only is default  |
| R-08 | C++ port urgency               | Low        | Medium | Latency targets defined; port only if exceeded      |
| R-09 | Planning relapse               | Medium     | Medium | Planning Freeze Protocol; session checklists        |
| R-10 | Golden fixture insufficient    | Low        | Medium | Start with 3 fixtures, expand during M5 buffer      |

### Mitigation Priority

Focus mitigation effort on **R-01** (schedule) and **R-02** (scope) — the
two risks that killed DARK_leaf v2. All other risks have manageable fallbacks.

---

## Appendix A: Glossary

| Term              | Definition                                                  |
|-------------------|--------------------------------------------------------------|
| Blackboard        | Ephemeral typed-dict store for inter-agent communication     |
| DAG               | Directed acyclic graph; used for task decomposition          |
| Golden Fixture    | Test case with a known textbook answer                       |
| Gap Flag          | A note in the vault marking a known knowledge gap            |
| MVP               | Minimum Viable Product — 7 agents, 3 providers, Python only |
| Planning Freeze   | No new planning docs; code only after master index           |
| Vault             | Obsidian-based knowledge store in `vault/`                   |
| V1                | Post-MVP version targeting 68 agents and C++ port            |

## Appendix B: Cross-References

| Document                  | Path                              | Purpose                    |
|---------------------------|-----------------------------------|----------------------------|
| FORGE Catalog             | `docs/planning/FORGE_CATALOG.md`  | Architecture & roster      |
| Execution Plan (this doc) | `docs/planning/FORGE_EXECUTION_PLAN.md` | Timeline & process   |
| Decision Log              | `docs/planning/DECISIONS.md`      | ADRs                       |
| Configuration             | `forge.yaml`                      | Runtime config             |
| Changelog                 | `CHANGELOG.md`                    | Version history            |
