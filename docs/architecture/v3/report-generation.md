# Report Generation Pipeline (Context 1B)

> Structured agent outputs → professional engineering reports.
> Stack: Jinja2 templates → HTML assembly → WeasyPrint PDF.
> Math: SymPy → LaTeX → KaTeX (synchronous, zero dependencies).
> Visualizations: PyVista (3D) + matplotlib (2D) + Plotly (interactive).

---

## Pipeline

```
FORGE run_complete event
  │
  ▼
Result Assembler
  ├── Reads blackboard snapshot (final state)
  ├── Reads vault notes written during run (by trace_id)
  └── Assembles structured ReportData object
  │
  ▼
Visualization Generator (parallel)
  ├── PyVista: CalculiX .frd → ccx2paraview → VTU → stress contours, deformed shape
  ├── OpenFOAM foamToVTK → VTU → velocity/pressure fields
  ├── matplotlib: convergence histories, stress-strain curves, Pareto frontiers
  ├── Plotly: interactive elements (self-contained <div>)
  └── SymPy: formula → LaTeX substitution → KaTeX rendering
  │
  ▼
Jinja2 Template Rendering
  ├── Template: templates/engineering_report.html.j2
  ├── Injects: all figures, tables, calculation chains, traceability metadata
  └── Outputs: report.html
  │
  ├──▶ WeasyPrint → report.pdf (print-ready)
  └──▶ report.html (interactive: vtk.js 3D viewer, Plotly hover, expandable traces)
```

---

## Report Structure (ASME V&V 10 / NAFEMS aligned)

1. Executive Summary
2. Scope and Objectives
3. Geometry Description
   - Component dimensions
   - PyVista render (undeformed mesh)
4. Material Properties
   - Table with provenance citations
   - Temperature-dependent curves if applicable
5. Mesh Details
   - Element count, type, quality metrics
   - Mesh convergence study plot (matplotlib)
6. Boundary Conditions and Loading
   - Diagrams with annotated constraint types and load magnitudes
7. Analysis Settings
   - Solver, analysis type, tolerance criteria
8. Results
   - Displacement contour (PyVista, deformed + undeformed overlay)
   - Von Mises stress contour (PyVista, with colorbar)
   - Max values table with locations
   - Interactive 3D viewer (vtk.js embedded in HTML)
9. Code Compliance
   - Acceptance criteria table: actual vs. allowable
   - Safety factors per load case
10. Verification and Validation
    - Gate results (contract/unit/dimensional/provenance)
    - Mesh convergence plot
    - Comparison with analytical solution (if applicable)
11. Traceability
    - Agent contributions table: agent_id, confidence, assumptions
    - Calculation chains (SymPy → LaTeX via KaTeX)
    - Vault note references
12. Conclusions and Recommendations

---

## Traceability Metadata

Every figure, table, and conclusion in the report carries embedded metadata:

```html
<!-- In HTML output: expandable trace panel -->
<details class="forge-trace">
  <summary>Analysis trace ▸</summary>
  <table>
    <tr><td>Agent</td><td>me_specialist v1.0.0</td></tr>
    <tr><td>Confidence</td><td>0.87</td></tr>
    <tr><td>Assumptions</td><td>Linear elastic; quasi-static; 20°C</td></tr>
    <tr><td>Vault note</td><td><a href="...">aladdin-3b/motor_mount/finding-001</a></td></tr>
    <tr><td>Trace ID</td><td>a3f1b2c4-...</td></tr>
  </table>
</details>
```

In PDF output: subtle footnotes with agent ID, confidence, and vault reference.

---

## Calculation Chain Rendering (SymPy → KaTeX)

```python
# forge-output/src/forge_output/math_renderer.py
import sympy as sp

def render_calculation_chain(formula_str: str, substitutions: dict) -> str:
    """
    Returns HTML string with KaTeX-rendered calculation chain:
      symbolic formula → substituted values → numerical result
    """
    expr = sp.sympify(formula_str)
    # symbolic form
    latex_symbolic = sp.latex(expr)
    # substitute values
    subst_expr = expr.subs(substitutions)
    latex_substituted = sp.latex(subst_expr)
    # numerical result
    result = float(subst_expr.evalf())

    return f"""
    <span class="calc-chain">
      <katex>\\sigma_{{max}} = {latex_symbolic} = {latex_substituted} = {result:.2f}\\text{{ MPa}}</katex>
    </span>
    """
```

---

## Visualization Specs

### PyVista Off-Screen Rendering
```python
import pyvista as pv
pv.start_xvfb()  # headless

mesh = pv.read("results/stress.vtu")
plotter = pv.Plotter(off_screen=True)
plotter.add_mesh(mesh, scalars="von_mises", cmap="jet",
                 clim=[0, yield_strength * 0.6])
plotter.add_scalar_bar("σ_VM [MPa]")
plotter.screenshot("figures/von_mises_stress.png", window_size=[1920, 1080])
```

### Topology Optimization Animation
```python
plotter = pv.Plotter(off_screen=True)
plotter.open_gif("figures/topo_opt.gif")
for iteration_mesh in iteration_meshes:
    plotter.clear()
    # threshold density field at 0.3 to show solid regions
    thresholded = iteration_mesh.threshold(0.3, scalars="density")
    plotter.add_mesh(thresholded, color="steelblue")
    plotter.write_frame()
plotter.close()
```

---

## Typst Alternative (math-heavy documents)

For reports with dense mathematical derivations, **Typst** compiles faster than LaTeX and is more maintainable:

```bash
pip install typst-py
```

The pipeline supports both WeasyPrint (HTML→PDF, better for mixed content) and Typst (`.typ`→PDF, better for math-heavy theoretical reports). Template choice is configurable per report type.

---

## Key Dependencies

```toml
[project.dependencies]
jinja2 = ">=3.0"
weasyprint = ">=60"
pyvista = ">=0.47"
meshio = ">=5.3"
plotly = ">=5.0"
sympy = ">=1.12"
matplotlib = ">=3.8"
```

Required external tools (installed separately):
- `ccx2paraview` (CalculiX VTK export)
- `foamToVTK` (OpenFOAM, bundled with OpenFOAM)
- `typst` (optional, for math-heavy reports)
