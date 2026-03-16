# FORGE — Developer Quick Reference

## Setup

```sh
pip install pytest pytest-asyncio pyyaml ruff yamllint
pip install numpy python-frontmatter
pip install anthropic httpx asyncio-throttle watchdog fastmcp pydantic jinja2
pip install -e "forge_agent/[mcp]"
pip install -e forge-assembly/
pip install -e forge-output/
```

## Run Tests

```sh
pytest --tb=short -q          # all tests
pytest tests/                 # smoke + regression tests only
pytest forge_agent/tests/     # forge_agent unit tests
pytest tools/tests/           # tools unit tests
```

## Lint

```sh
yamllint .                    # YAML lint (uses .yamllint.yml — excludes .github/workflows/)
ruff check . --ignore E501    # Python lint
```

## Registry

```sh
python tools/validate_registry.py          # validate all 274 agents (exit 0 = PASS)
python tools/validate_registry.py --report # JSON report
```

## Generate Agent Scaffolds

```sh
# Single agent:
python tools/scaffold_agent.py \
    --id aerodynamics_specialist \
    --role specialist \
    --domain "Aerodynamics — Lift, Drag, Propulsion" \
    --domain-short "aerodynamics" \
    --pair aerodynamics_antagonist \
    --status planned

# Batch from manifest:
python tools/scaffold_agent.py --batch tools/agent_manifest.yaml
```

## Conventions

- Agent IDs: `snake_case`, suffix `_specialist` or `_antagonist`
- SKILL.md: minimum 60 lines, 8 `##` headings required (CI enforced)
- Agent cards: YAML list items must be 2-space indented (`  - item`)
- Branch pattern: `claude/<description>-<SESSION_ID>`
- Current dev branch: `claude/briefcase-phase-implementation-gK4j5`

## CI Checks

All PRs run: yamllint → ruff → pytest. All three must pass (no `|| true`).
Registry validation is a separate tool, not yet in CI — run manually before PRs.

## Polyglot Architecture Doctrine

> **Right tool for the right job. Choices justified by purpose, not preference.**
> AI agents help plan language allocation.

FORGE is intentionally polyglot. **Do not add code in a language not in this table.**

| Language / Stack | Purpose | Justification |
|---|---|---|
| **C++** | Core runtime, orchestration, blackboard, model router, agent lifecycle, A2A/gRPC, main loop | Deterministic performance, memory control, latency targets (<100 ms router, <50 ms blackboard) |
| **Python** | MCP server wrappers, tool integration, Obsidian vault interface, maintenance automation, glue, fast iteration | Ecosystem (foamlib, PyCCX, FEniCSx API, FastMCP), rapid prototyping, acceptable latency for tool dispatch |
| **MATLAB / Octave** | FreeTO, Swan, topology optimization, established math/engineering toolboxes | Existing validated code, MATLAB Engine API bridges to C++/Python, Octave fallback for unlicensed environments |
| **GPU stacks (CUDA/Python/C++)** | PhysX 5.6, Warp differentiable physics, Newton robotics, Isaac Sim, PhysicsNeMo | Physics simulation at scale requires GPU. Warp = Python→CUDA JIT. PhysX = native C++/CUDA. |
| **YAML / JSON** | Configuration, blackboard schema, forge.yaml, agent contracts, test fixtures | Human-readable, version-controllable, parseable by any language in the stack |

### Anti-Patterns (banned)

| Anti-pattern | Why banned |
|---|---|
| Python for core runtime loop or blackboard | GIL + unpredictable GC prevent sub-50 ms latency guarantees |
| C++ for MCP tool wrappers | Massive ecosystem cost; tools already have Python bindings |
| MATLAB outside topology optimization / validated toolboxes | License dependency, not embeddable in real-time path |
| GPU stacks for anything not requiring massively parallel physics | CUDA adds build complexity; only justified by simulation-at-scale |
| Adding a language without an entry in this table | Every language must have a defensible purpose. No preference-driven additions. |

### Latency Contracts by Language

| Path | Language | Target |
|---|---|---|
| Blackboard read / write | C++ | < 50 ms |
| Model router decision | C++ | < 100 ms |
| MCP tool dispatch | Python | < 500 ms |
| Vault read / write | Python | < 1 s (async queued) |
| FEA solve dispatch | MATLAB / Python | < 60 s (solver-bound) |
| GPU physics step | CUDA | < 10 ms / step |

### Decision Authority

- Changing a language assignment requires an ADR in `docs/governance/decisions.md`.
- Adding a new language requires an ADR **and** proof no existing language serves the purpose.
- AI agents must flag any code that violates this table before committing.

Full spec: `docs/architecture/polyglot-doctrine.md`

## Obsidian Vault

`forge-vault/` is a fully configured Obsidian vault (≥ v1.12.4). Open it directly
in Obsidian. Required community plugins: **Dataview**, **Templater**, **obsidian-git**.

```
forge-vault/
  .obsidian/          ← Obsidian config (committed)
  HOME.md             ← vault home note / quick nav
  inbox/              ← NotebookLM exports awaiting Librarian processing
  notebooks/          ← Source PDFs uploaded to NotebookLM
  engineering/        ← Verified engineering findings
  mathematics/        ← Formulations and solver notes
  ilc/                ← Inter-domain link candidates
  projects/           ← Per-project knowledge (Aladdin-3B, Vanguard, Phoenix)
  indexes/            ← Auto-maintained indexes (gaps, contradictions, stale)
```

## NotebookLM

External research (PDFs, papers) is pre-processed in **Google NotebookLM** before
entering the vault. The workflow: upload to NotebookLM → export summary markdown to
`forge-vault/inbox/` → Librarian agent validates → verified note lands in
`engineering/` or `mathematics/`.

Full spec: `forge-memory/obsidian/notebooklm.md`

---

## LEAP 71 Integration

This repository integrates the LEAP 71 open-source computational engineering stack as domain
knowledge inside FORGE agents. LEAP 71's stack is C#; FORGE uses it as knowledge in SKILL.md files.

### Software Stack (three tiers)

```
Layer 1: PicoGK          — voxel geometry kernel (github.com/leap71/PicoGK)
Layer 2: ShapeKernel     — BaseShapes, LocalFrame (github.com/leap71/LEAP71_ShapeKernel)
Layer 3: Domain libs:
  - LatticeLibrary       — beam lattice + TPMS (github.com/leap71/LEAP71_LatticeLibrary)
  - HelixHeatX           — heat exchanger CEM (github.com/leap71/LEAP71_HelixHeatX)
  - QuasiCrystals        — aperiodic tilings (github.com/leap71/LEAP71_QuasiCrystals)
  - RoverWheel           — parametric rover wheels (github.com/leap71/LEAP71_RoverWheel)
```

### C# Runtime Location

The C# PicoGK runtime lives in `mesh-morph-lhs/`. To build:

```sh
cd mesh-morph-lhs
dotnet build
dotnet run
```

Add PicoGK package to a .NET project (.NET 9+ required):

```sh
dotnet add package PicoGK
```

### LEAP 71 FORGE Agents (knowledge layer)

| Agent ID | Domain |
|---|---|
| `picogk_geometry` | PicoGK core: Voxels, Lattice, IImplicit, Boolean ops, export |
| `shape_kernel_specialist` | ShapeKernel: BaseShapes, LocalFrame, CEM composition |
| `shape_kernel_antagonist` | ShapeKernel critique: nomenclature, Boolean order, wall thickness |
| `lattice_infill_specialist` | LatticeLibrary: ICellArray, ILatticeType, IBeamThickness, TPMS |
| `lattice_infill_antagonist` | LatticeLibrary critique: speculative infill, nSubSample, post-processing |
| `quasicrystal_metamaterials_specialist` | Penrose patterns, icosahedral quasi-crystals |
| `quasicrystal_metamaterials_antagonist` | Quasi-crystal critique: inflation explosion, preview mode |
| `rover_wheel_specialist` | WheelLayers, WheelElements, tread patterns, coordinate transforms |
| `rover_wheel_antagonist` | Rover wheel critique: layer overlap, symmetry, missing tread |

### LEAP 71 Copilot Instructions

`.github/instructions/forge-leap71.instructions.md` — applies to `mesh-morph-lhs/**` and all
LEAP71-related agent directories. Contains:
- All golden rules (voxel-first, inverse design, nomenclature, no speculative lattice)
- Full API reference for PicoGK Boolean ops, LatticeLibrary, TPMS, QuasiCrystals, RoverWheel
- Known pitfalls table

### Key LEAP 71 Rules

1. **Voxel-first**: All geometry is voxel-based — never build B-rep and convert
2. **Inverse design**: Design fluid void volumes first; derive walls by subtraction
3. **Nomenclature mandatory**: `fRadius` not `radius`; `vecPt` not `pt`; `voxResult` not `result`
4. **No speculative lattice**: LatticeLibrary only after `topology_optimization` handoff prescribes it
5. **Boolean naming**: Use instance methods `vox.voxBoolSubtract()`, `vox.voxBoolAdd()`, `vox.voxBoolIntersect()` — the old `Sh.voxSubtract()` / `Sh.voxAdd()` / `Sh.voxIntersect()` statics are `[Obsolete]` as of ShapeKernel v1.7
6. **Quasi-crystal generation limit**: ≤ 3 inflation iterations (120^N face growth)

---

## Known AI Mistake Patterns

This section documents mistakes previously caught by Copilot PR reviews. Read before writing any code.

### P1 Bugs (previously caught)

**1. Interface/implementation mismatch — missing sync methods (obsidian_manager.py)**
- Symptom: Server calls `vault.search_notes()`, `vault.get_note()`, etc. but the class only exposes async `search()` / `read_note()` — every real invocation raises `AttributeError`.
- Rule: When you write a server that calls methods on a manager class, verify every method name exists AND has the correct sync/async signature. Do not assume async↔sync equivalence.

**2. Accepted-but-ignored parameters (disassembly.py)**
- Symptom: `build_disassembly_dag()` accepted `tool_access_results` but never used it — blocked interfaces still appeared removable.
- Rule: If a function parameter has no code paths that read it, either use it or remove it. Never accept a parameter silently.

**3. Circuit-breaker race condition (retry.py)**
- Symptom: In `HALF_OPEN` state `allow_call()` returned `True` for every concurrent caller — many requests hammered an unhealthy endpoint simultaneously.
- Rule: `HALF_OPEN` must allow exactly ONE probe. Use a flag (`_probe_in_flight`) so subsequent callers are rejected until the probe resolves.

### P2 / CI Issues (previously caught)

**10. Missing pyproject.toml for pip-installed sub-packages**
- Symptom: `pip install -e forge-output/` (or any sub-package) fails in CI with
  "Could not find a version that satisfies the requirement" or "not a valid editable install".
  Tests pass locally because `conftest.py` dynamically adds `forge-*/src` to `sys.path`,
  masking the missing build config.
- Rule: Every sub-package that is `pip install -e`'d in CI must have a `pyproject.toml`
  (or `setup.py`). Run `pip install -e <pkg>/` locally before committing a new package.

**11. Wrong setuptools build backend (`setuptools.backends.legacy:build`)**
- Symptom: `BackendUnavailable: Cannot import 'setuptools.backends.legacy'` in CI.
  The module `setuptools.backends` was introduced in setuptools **69.0.0**. Declaring
  `requires = ["setuptools>=68"]` allows setuptools 68.x to be installed in pip's
  isolated build environment — which has no `backends` module. Both the primary install
  and the `--no-build-isolation` fallback fail, aborting the CI job.
- Rule: Always use `build-backend = "setuptools.build_meta"` (available since setuptools 40+).
  Never use `setuptools.backends.legacy:build`. If upgrading the minimum, set `>=69`.

**4. Silent CI failures**
- Symptom: `yamllint ... || true` and `ruff ... || true` let lint failures pass CI silently.
- Rule: Never use `|| true` on lint/test commands in CI. Failures must block merges.

**5. YAML truthy key `on:`**
- Symptom: GitHub Actions `on:` top-level key triggers yamllint `truthy` warning.
- Rule: `.github/workflows/` is excluded from yamllint (see `.yamllint.yml`). If adding new workflow YAML outside that path, quote the key: `"on":`.

**6. YAML line-too-long in shell steps**
- Symptom: Long `echo "..."` strings inside workflow `run:` blocks exceed 120 chars.
- Rule: Break long shell strings with `\` continuation or split across multiple `echo` calls.

**7. Error code inconsistency**
- Symptom: Markdown docs used `ERR_HIDDEN_ASSUMPTION` but the canonical catalog in `docs/contracts/error-codes.md` defines `ERR_VERIFY_HIDDEN_ASSUMPTION`.
- Rule: Always use error codes from `docs/contracts/error-codes.md`. Do not invent codes inline.

**8. Broken relative links**
- Symptom: `../../../../FORGE_CATALOG.md` from `docs/planning/catalog/` resolves to 4 levels up but the file is only 3 levels up.
- Rule: Count directory depth carefully. `docs/planning/catalog/` → root = `../../../`.

**9. Retry count ambiguity**
- Symptom: "retry >2×" was ambiguous — does it mean 2 retries or 2 total attempts?
- Rule: State retry policy as "N total attempts (1 initial + N-1 retries)".

### General Code Quality Rules

- Never silently accept a function parameter without using it.
- Always check that method names called on an object actually exist on that class.
- When writing async code that wraps sync, verify every caller gets the correct flavour.
- Validate YAML indentation: list items = 2-space indent (`  - item`), not 4-space.
- Run `yamllint .` and `ruff check . --ignore E501` before every commit.
- Run `pytest --tb=short -q` and confirm 0 errors during collection.
- When creating a new `forge-*` sub-package: always create `pyproject.toml` with
  `build-backend = "setuptools.build_meta"` and verify `pip install -e <pkg>/` succeeds
  locally before pushing. Conftest.py sys.path injection masks missing pyproject.toml locally
  but CI will fail on the install step.
