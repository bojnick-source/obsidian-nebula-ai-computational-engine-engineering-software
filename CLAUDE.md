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
python tools/validate_registry.py          # validate all 235 agents (exit 0 = PASS)
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
