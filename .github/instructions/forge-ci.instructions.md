---
applyTo: ".github/**"
---

# FORGE — CI/CD Instructions

## CI Gate Order

All PRs must pass in this order:

1. `yamllint .` — zero errors, zero warnings
2. `ruff check . --ignore E501` — zero errors
3. `pytest --tb=short -q` — zero collection errors, all tests pass
4. `python tools/validate_registry.py` — exit 0 (263+ agents, all cards valid)

**Never merge with any gate failing or masked.**

## What yamllint Checks

- Config: `.yamllint.yml` (max line 120, document-start optional)
- Excludes: `briefcase/node_modules/`, `node_modules/`, `.github/workflows/`
- Workflow files excluded from yamllint because GitHub Actions requires `on:` as
  a bare key (which yamllint would flag as truthy)

## What ruff Checks

- Config: `pyproject.toml` [tool.ruff]
- Ignored: E501 (line length — handled by per-file conventions)
- Target: Python 3.11

## What pytest Checks

- Paths: `forge-tests/`, `tests/`, `tools/tests/`, `forge_agent/tests/`,
  `forge-assembly/tests/`, `forge-output/tests/`
- Config: root `pyproject.toml` [tool.pytest.ini_options]
- Async tests require `pytest-asyncio` installed

## Dependency Installation

```yaml
# CORRECT — two attempts, explicit failure
pip install -e "forge_agent/[mcp]" || pip install -e "forge_agent/[mcp]" --no-build-isolation

# WRONG — silently hides all failures
pip install -e "forge_agent/[mcp]" || pip install ... || true
```

Never add `|| true` — if both install attempts fail, CI must fail visibly.

## Adding a New CI Job

New jobs go in `.github/workflows/ci.yml`. Pattern:

```yaml
  my-new-check:
    name: Descriptive name
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: pip install required-package
      - name: Run check
        run: command-that-fails-with-nonzero-exit
```

## Security Workflow

- `.github/workflows/security.yml` runs detect-secrets scan weekly + on PR to main
- Requires `.secrets.baseline` to be committed (generate: `detect-secrets scan > .secrets.baseline`)
- Runs pip-audit on all dependencies

## Nightly Fixtures

- `.github/workflows/nightly-fixtures.yml` — daily 02:00 UTC
- Validates `forge-tests/fixtures/` against schemas
- Currently placeholder; populate when fixture validation logic is ready
