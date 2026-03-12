"""Root conftest.py — ensures all FORGE sub-packages are importable.

Adds package source directories to sys.path so tests can run without
`pip install -e` for each package (useful when editable installs fail).
The repo root is also added so `import forge_agent` resolves correctly.
"""
import sys
from pathlib import Path

_root = Path(__file__).parent

# Repo root — makes `import forge_agent` work without pip install
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Sub-package src/ directories
for _src in ("forge-assembly/src", "forge-output/src", "forge-learning/src"):
    _src_path = _root / _src
    if _src_path.exists() and str(_src_path) not in sys.path:
        sys.path.insert(0, str(_src_path))
