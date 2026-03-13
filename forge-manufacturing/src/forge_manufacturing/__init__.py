"""forge-manufacturing: FORGE digital thread and manufacturing process system.

Provides:
  - Pydantic data models for smart airframe manufacturing specs (model.py)
  - Spec validation and topological sort (validate.py)
  - Build traveler / pipeline runner (runner.py)
  - Artifact file I/O utilities (artifacts.py)
  - SHA-256 hashing utilities (hashutil.py)
  - Python→C++ engine bridge (engine_bridge.py)

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/sfcs_mdp/)
"""

from __future__ import annotations

__version__ = "0.1.0"
