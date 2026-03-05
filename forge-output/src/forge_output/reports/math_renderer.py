"""SymPy → LaTeX → KaTeX rendering for auto-documented calculation chains."""

from __future__ import annotations

from typing import Any

try:
    import sympy as sp
    _SYMPY_AVAILABLE = True
except ImportError:
    _SYMPY_AVAILABLE = False


def render_calculation_chain(
    formula_str: str,
    substitutions: dict[str, float],
    description: str = "",
) -> str:
    """Return an HTML fragment with symbolic + numeric KaTeX rendering.

    Falls back to plain text if SymPy is unavailable.
    """
    if not _SYMPY_AVAILABLE:
        return f"<pre>{formula_str} = {_naive_eval(formula_str, substitutions)}</pre>"

    try:
        expr = sp.sympify(formula_str)
    except Exception as exc:
        return f"<pre>Parse error: {exc}</pre>"

    latex_symbolic = sp.latex(expr)

    # Build substituted expression
    sym_subs = {sp.Symbol(k): v for k, v in substitutions.items()}
    subst_expr = expr.subs(sym_subs)
    try:
        result = float(subst_expr.evalf())
    except Exception:
        result = float("nan")

    # Build numeric substitution LaTeX
    numeric_parts = ", ".join(f"{k}={v}" for k, v in substitutions.items())
    latex_numeric = sp.latex(subst_expr.evalf(4))

    desc_html = f"<p><em>{description}</em></p>" if description else ""

    return f"""
{desc_html}
<div class="calc-chain">
  <div class="calc-symbolic">
    <katex>{latex_symbolic}</katex>
  </div>
  <div class="calc-substituted">
    <katex>{latex_symbolic} \\Big|_{{{numeric_parts}}} = {latex_numeric} = {result:.4g}</katex>
  </div>
</div>
"""


def _naive_eval(formula: str, subs: dict[str, float]) -> str:
    """Very simple substitution for fallback (no SymPy)."""
    try:
        import re
        expr = formula
        for k, v in sorted(subs.items(), key=lambda x: -len(x[0])):
            expr = re.sub(rf"\b{k}\b", str(v), expr)
        return str(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception:
        return "N/A"
