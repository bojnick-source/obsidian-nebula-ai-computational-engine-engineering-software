"""Architecture Integrity Audit — Repository Layer 1 Tests.

Validates:
1. No circular imports across FORGE sub-packages
2. All public module entry points are importable without runtime errors
3. No missing __init__.py files in package directories
4. Import graph consistency (cross-package imports flow in one direction)

These tests run without any solver / AI calls — pure import-time validation.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _add_src_paths() -> None:
    """Ensure all sub-package src/ dirs are on sys.path."""
    for src in ("forge-assembly/src", "forge-output/src"):
        p = REPO_ROOT / src
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


_add_src_paths()


def _try_import(module_name: str) -> tuple[ModuleType | None, str | None]:
    """Return (module, None) on success or (None, error_msg) on failure."""
    try:
        mod = importlib.import_module(module_name)
        return mod, None
    except Exception as exc:
        return None, str(exc)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Entry-point importability
# ─────────────────────────────────────────────────────────────────────────────

FORGE_AGENT_MODULES = [
    "forge_agent",
    "forge_agent.core.token_budget",
    "forge_agent.core.governance",
    "forge_agent.core.loop_guard",
    "forge_agent.core.intelligence_router",
    "forge_agent.core.context_assembler",
    "forge_agent.core.retry",
    "forge_agent.core.provider_clients",
    "forge_agent.agents.verifier",
    "forge_agent.memory.obsidian_manager",
]

FORGE_ASSEMBLY_MODULES = [
    "forge_assembly",
    "forge_assembly.placement",
    "forge_assembly.mass_props",
    "forge_assembly.fasteners",
    "forge_assembly.disassembly",
    "forge_assembly.maintenance",
    "forge_assembly.tool_access",
]

FORGE_OUTPUT_MODULES = [
    "forge_output",
    "forge_output.event_schema",
    "forge_output.reports.assembler",
    "forge_output.vault.writer",
]


@pytest.mark.parametrize("module_name", FORGE_AGENT_MODULES)
def test_forge_agent_module_importable(module_name: str) -> None:
    """Every forge_agent public module must import without error."""
    mod, err = _try_import(module_name)
    assert mod is not None, f"Import failed for {module_name!r}: {err}"


@pytest.mark.parametrize("module_name", FORGE_ASSEMBLY_MODULES)
def test_forge_assembly_module_importable(module_name: str) -> None:
    """Every forge_assembly public module must import without error."""
    mod, err = _try_import(module_name)
    assert mod is not None, f"Import failed for {module_name!r}: {err}"


@pytest.mark.parametrize("module_name", FORGE_OUTPUT_MODULES)
def test_forge_output_module_importable(module_name: str) -> None:
    """Every forge_output public module must import without error."""
    mod, err = _try_import(module_name)
    assert mod is not None, f"Import failed for {module_name!r}: {err}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. No circular imports — import each module fresh and verify it loads cleanly
# ─────────────────────────────────────────────────────────────────────────────

def test_no_circular_import_forge_agent_core() -> None:
    """forge_agent.core modules must not have circular import dependencies."""
    core_path = REPO_ROOT / "forge_agent" / "core"
    errors = []
    for py_file in sorted(core_path.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        module_name = f"forge_agent.core.{py_file.stem}"
        _, err = _try_import(module_name)
        if err and "circular" in err.lower():
            errors.append(f"{module_name}: {err}")
    assert errors == [], "Circular imports detected:\n" + "\n".join(errors)


def test_no_circular_import_forge_assembly() -> None:
    """forge_assembly modules must not have circular import dependencies."""
    asm_path = REPO_ROOT / "forge-assembly" / "src" / "forge_assembly"
    errors = []
    for py_file in sorted(asm_path.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        module_name = f"forge_assembly.{py_file.stem}"
        _, err = _try_import(module_name)
        if err and "circular" in err.lower():
            errors.append(f"{module_name}: {err}")
    assert errors == [], "Circular imports detected:\n" + "\n".join(errors)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Package structure: every package directory has __init__.py
# ─────────────────────────────────────────────────────────────────────────────

def test_forge_agent_subpackages_have_init() -> None:
    """Every forge_agent sub-directory that contains .py files must have __init__.py."""
    root = REPO_ROOT / "forge_agent"
    missing = []
    for d in sorted(root.rglob("*")):
        if not d.is_dir():
            continue
        if "__pycache__" in d.parts:
            continue
        py_files = [f for f in d.glob("*.py") if not f.name.startswith("__")]
        if py_files and not (d / "__init__.py").exists():
            missing.append(str(d.relative_to(REPO_ROOT)))
    assert missing == [], (
        "Package directories missing __init__.py:\n" + "\n".join(missing)
    )


def test_forge_assembly_subpackages_have_init() -> None:
    """Every forge_assembly sub-directory that contains .py files must have __init__.py."""
    root = REPO_ROOT / "forge-assembly" / "src" / "forge_assembly"
    missing = []
    for d in sorted(root.rglob("*")):
        if not d.is_dir():
            continue
        if "__pycache__" in d.parts:
            continue
        py_files = [f for f in d.glob("*.py") if not f.name.startswith("__")]
        if py_files and not (d / "__init__.py").exists():
            missing.append(str(d.relative_to(REPO_ROOT)))
    assert missing == [], (
        "Package directories missing __init__.py:\n" + "\n".join(missing)
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Import direction: forge_assembly must NOT import from forge_agent
#    (assembly is a lower-level domain library, agent is higher-level)
# ─────────────────────────────────────────────────────────────────────────────

def test_forge_assembly_does_not_import_forge_agent() -> None:
    """forge_assembly must not depend on forge_agent (wrong dependency direction)."""
    asm_root = REPO_ROOT / "forge-assembly" / "src" / "forge_assembly"
    violations = []
    for py_file in sorted(asm_root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        content = py_file.read_text()
        if "import forge_agent" in content or "from forge_agent" in content:
            violations.append(str(py_file.relative_to(REPO_ROOT)))
    assert violations == [], (
        "forge_assembly imports from forge_agent (wrong direction):\n"
        + "\n".join(violations)
    )


def test_forge_output_does_not_import_forge_agent() -> None:
    """forge_output must not depend on forge_agent (wrong dependency direction)."""
    out_root = REPO_ROOT / "forge-output" / "src" / "forge_output"
    violations = []
    for py_file in sorted(out_root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        content = py_file.read_text()
        if "import forge_agent" in content or "from forge_agent" in content:
            violations.append(str(py_file.relative_to(REPO_ROOT)))
    assert violations == [], (
        "forge_output imports from forge_agent (wrong direction):\n"
        + "\n".join(violations)
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. No bare `except:` clauses — swallowed exceptions break diagnostics
# ─────────────────────────────────────────────────────────────────────────────

def test_no_bare_except_in_forge_agent() -> None:
    """forge_agent source must not use bare `except:` (use `except Exception:`)."""
    root = REPO_ROOT / "forge_agent"
    violations = []
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in py_file.parts or "tests" in py_file.parts:
            continue
        for i, line in enumerate(py_file.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped == "except:" or stripped.startswith("except:  #"):
                violations.append(f"{py_file.relative_to(REPO_ROOT)}:{i}")
    assert violations == [], (
        "Bare `except:` clauses found (use `except Exception:`):\n"
        + "\n".join(violations[:10])
    )
