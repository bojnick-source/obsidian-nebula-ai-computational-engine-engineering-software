"""Shared base for all FORGE specialist and mathematician agents."""
from __future__ import annotations

AGENT_OUTPUT_CONTRACT_REMINDER = """\

## Agent Output Contract (MANDATORY)
Return a JSON object with ALL of these fields:
{
  "model_choice": "Rationale for chosen engineering model",
  "equations": ["$$LaTeX equation 1$$", "$$LaTeX equation 2$$"],
  "units": "All values in SI units (m, kg, s, Pa, N, K, ...)",
  "sanity_checks": [
    {"type": "limiting_case|conservation|dimensional", "detail": "..."}
  ],
  "calculation_path": "Step-by-step reproducible derivation...",
  "numerical_answer": "Final numerical result with units",
  "assumptions": ["Assumption 1", "Assumption 2"]
}
"""
