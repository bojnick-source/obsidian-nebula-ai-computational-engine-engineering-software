# FORGE Requirements

> Derived from v0.1-spec.md, v0.1-acceptance-test.md, tiered-roadmap.md. Last updated: 2026-03-18.

---

## Phase 1 — Briefcase Phase Implementation (COMPLETE)

**Status:** Verified 2026-03-17. All gates pass. 337 tests pass.

**Delivered:**
- C++ forge-core: Blackboard, ConcurrencyGuard, ModelRouter, Orchestrator scaffold,
  JSONLLogger, EventEmitter, common IDs/time
- Python forge_agent: VerifierAgent, run_all_gates() (ContractGate, UnitGate,
  DimensionalGate, ProvenanceGate), GMSH MCP wrapper, CalculiX MCP wrapper,
  ObsidianVaultManager + amnesia_check, AgentJournal, MechanicalEngineer prompt,
  briefcase Tauri app (TypeScript/Rust)
- forge-tests: v0_1_acceptance fixture YAML, verifier_red_team fixtures,
  phase_1_1 blackboard fixture
- 276 agents in registry with SKILL.md

**NOT delivered (critical gaps identified):**
- Python pipeline runner tying all phase implementations together
- Librarian Python runtime implementation
- pytest test suite exercising v0.1 acceptance criteria (AC-01 → AC-10)
- Missing planned test fixtures (phase_1_2, phase_1_3, golden outputs)

---

## Phase 2 — v0.1 MVP Pipeline Integration + Acceptance Tests

**Entry gate:** Phase 1 verified (DONE).
**Exit gate:** v0.1 acceptance criteria AC-01 through AC-10 all pass in pytest.

### Requirements

#### R2-01: Python Pipeline Runner
A `forge_agent/core/pipeline.py` module that runs the 9-phase FORGE loop:
1. `intake` — validate TaskRequest, assign trace_id, write to blackboard dict
2. `routing` — select provider/model (use ModelRouter adapter or config)
3. `decomposition` — single-task for MVP
4. `memory_preflight` — retrieve top-k relevant vault notes via ObsidianVaultManager
5. `specialist` — call ME Specialist (Anthropic API) with task + preflight context
6. `tool_execution` — invoke GMSH then CalculiX via MCP envelope; write results to blackboard
7. `verification` — run `run_all_gates(specialist_output)` + VerifierAgent; block vault write on failure
8. `persistence` — call `ObsidianVaultManager.upsert_note()` then `amnesia_check()`; log failure but don't halt output
9. `output` — assemble `TaskResult` from blackboard; emit JSONL summary

Each phase must:
- Emit JSONL start + end events with `trace_id`, `phase`, `status`, `duration_ms`
- Propagate the same `trace_id` UUID to all artifacts
- Write phase outputs to a blackboard dict keyed by `"<phase>.<field>"`

Acceptance: pytest test can instantiate PipelineRunner, inject mock tool calls,
and verify that all 10 v0.1 ACs pass.

#### R2-02: Librarian Python Runtime
A `forge_agent/agents/librarian.py` module implementing:
- `LibrarianAgent.intake(note_dict) → str path` — classify + write note to vault
- `LibrarianAgent.retrieve(domain, component, top_k) → list[dict]` — search + return notes
- `LibrarianAgent.amnesia_check(path) → bool` — wraps ObsidianVaultManager.amnesia_check
- `LibrarianAgent.detect_gaps(blackboard) → list[str]` — identify missing knowledge

Acceptance: pytest roundtrip test: write a note via intake, retrieve by domain+component,
amnesia_check returns True.

#### R2-03: v0.1 Acceptance Test Suite
`forge_agent/tests/test_v01_acceptance.py` covering AC-01 through AC-10:

| AC | Test |
|---|---|
| AC-01 | trace_id same across blackboard, specialist output, tool invocations, vault note |
| AC-02 | ME Specialist output conforms to agent-output-contract.md (static contract check) |
| AC-03 | GMSH wrapper returns success envelope with element_count > 0 (mock ccx not required) |
| AC-04 | CalculiX wrapper returns success envelope with max_von_mises_mpa present (mock) |
| AC-05 | run_all_gates() returns all PASS for valid structural output |
| AC-06 | Vault note written with correct frontmatter fields (type, trace_id, domain, component) |
| AC-07 | amnesia_check returns True immediately after vault write |
| AC-08 | TaskResult contains result_summary, unresolved_gaps, what_would_falsify, confidence, artifact_refs |
| AC-09 | Pipeline blocks vault write when a verification gate fails |
| AC-10 | JSONL log has start+end events for all 9 phases; all contain trace_id |

GMSH and CalculiX are mocked via `unittest.mock`. Real vault I/O uses a tmp directory.

#### R2-04: Missing Test Fixtures
Populate planned-but-empty fixture directories per FIXTURE_INDEX.md:

- `forge-tests/fixtures/phase_1_2/` — memory intake (vault write + read-back)
- `forge-tests/fixtures/phase_1_3/` — gap detection (missing knowledge detection)
- `forge-tests/fixtures/golden/verifier_red_team/` — expected verdicts for red-team inputs

Each fixture must follow the YAML schema defined in FIXTURE_INDEX.md.

---

## Phase 3 — v0.1 Acceptance Gate (Planned)

**Entry gate:** Phase 2 complete; all R2-0x tests pass.
**Exit gate:** v0.1 acceptance test runs against live GMSH + CalculiX (not mocked);
all 10 ACs pass; v0.1 milestone declared complete.

Scope: Live solver integration, degraded-mode path, log completeness audit.

---

## Phase 4 — V1 Build (Planned)

Entry gate: v0.1 acceptance gate passed and frozen.
Scope: Antagonist system, A2A debate, provider failover, additional tool wrappers
(FreeTO, OpenFOAM, SU2), ILC link detection, Vanguard pipeline.
