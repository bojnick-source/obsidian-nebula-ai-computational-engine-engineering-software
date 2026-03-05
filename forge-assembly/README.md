# forge-assembly

FORGE Assembly & DFA skill implementation.

Places components into a global coordinate system, checks geometric interference,
verifies physical tool access for every fastener, generates a disassembly sequence,
and classifies maintenance access levels.

## Package structure

```
src/forge_assembly/
  assembler.py       # Top-level AssemblyOrchestrator (runs all 9 steps)
  placement.py       # Steps 1-2: coordinate system + component placement
  interference.py    # Step 3: trimesh boolean interference + clearance
  mass_props.py      # Step 4: CG and mass budget
  fasteners.py       # Steps 5-6 setup: tool database + FASTENER_TOOL_MAP
  tool_access.py     # Step 6: DFA swept-volume tool access check
  disassembly.py     # Step 7: disassembly DAG + Kahn's topological sort
  maintenance.py     # Step 8: L1/L2/L3 maintenance classification
  vault_writer.py    # Step 9: Obsidian vault write (5 notes)
```

## Install

```bash
pip install trimesh scipy numpy python-frontmatter pyyaml
pip install -e forge-assembly/
```

## Quick start

```python
from pathlib import Path
from forge_assembly.assembler import AssemblyOrchestrator

orchestrator = AssemblyOrchestrator(
    vault_root=Path("/my-vault"),
    project="Aladdin-3B",
    mass_budget_kg=6.1,
)

report = orchestrator.run(
    components=components,     # list[dict] with id, name, mass_kg, stl_path
    interfaces=interfaces,     # list[dict] IF-XXX records
    fastener_specs=fasteners,  # list[FastenerSpec]
    frequently_replaced=["C-004", "C-005", "C-006"],  # motors, battery
)

orchestrator.print_summary(report)
```

## Test

```bash
pytest forge-assembly/tests/ -v
```

## Architecture

See `docs/architecture/assembly-dfa.md`.
