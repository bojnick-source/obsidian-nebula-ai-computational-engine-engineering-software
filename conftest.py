"""Root conftest.py — adds all FORGE sub-packages to sys.path.

This allows tests to run without `pip install -e` for each package,
which is useful in local dev environments where editable installs may fail.
"""
import sys
from pathlib import Path

_root = Path(__file__).parent

# Add package source directories so imports work without editable install
for _pkg in ("forge_agent", "forge-assembly/src", "forge-output/src", "forge-learning/src"):
    _pkg_path = _root / _pkg
    if _pkg_path.exists():
        sys.path.insert(0, str(_pkg_path))
