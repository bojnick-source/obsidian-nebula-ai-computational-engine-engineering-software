# FORGE MATLAB / Octave Wrappers

Language tier: **MATLAB / Octave**
Role per [Polyglot Architecture Doctrine](../../docs/architecture/polyglot-doctrine.md):
FreeTO, Swan, topology optimization, established math/engineering toolboxes.

---

## Wrappers

| Wrapper | Tool | Method | Source | License |
|---|---|---|---|---|
| `freeto/freeto_wrapper.m` | FreeTO | SIMP / SEMDOT | [github.com/ooibhadode/FreeTO](https://github.com/ooibhadode/FreeTO) | MIT |
| `swan/swan_wrapper.m` | Swan + FreeTO | Density / Level-set / SIMP | [github.com/SwanLab/Swan](https://github.com/SwanLab/Swan) | Academic |

---

## FreeTO

FreeTO (Freeform Topology Optimization) uses STL files to define geometry — domain, loads,
and boundary conditions — and outputs element density arrays and optional STL exports.

**Primary API:**
```matlab
[comp, finalvol, eleden, gridden, elenum1, elenum2] = FreeTO( ...
    domain_stl, force_stl, MeshControl, volfrac, ...
    'fixed',         fixed_stl, ...
    'force2',        force2_stl, ...          % optional second load case
    'Fmagy',         [0 -2000], ...           % load magnitudes per case
    'Fmagz',         [1500 0], ...
    'YoungsModulus', 210e9, ...
    'PoissonsRatio', 0.3, ...
    'optimization',  'SIMP', ...              % 'SIMP' | 'SEMDOT'
    'Symmetry1',     'y', ...                 % optional mirror planes
    'modelName',     'output.stl')            % optional STL export
```

**Path setup:**
```matlab
addpath(genpath('/opt/FreeTO'))   % clone from github.com/ooibhadode/FreeTO
```

**FORGE wrapper call:**
```matlab
problem.domain_stl   = 'stls/bracket_domain.stl';
problem.force_stl    = 'stls/bracket_force.stl';
problem.fixed_stl    = 'stls/bracket_fixed.stl';
problem.mesh_control = 80;
problem.volume_frac  = 0.3;
problem.youngs_mod   = 210e9;
problem.Fmagy        = -2000;
problem.Fmagz        = 1500;
result = freeto_wrapper(problem);
```

---

## Swan (with FreeTO backend option)

Swan supports level-set and density-based methods from a JSON input deck.
Set `problem.backend = 'freeto'` to delegate to FreeTO instead — useful when
the geometry is already in STL form and you want SIMP with hexahedral meshing.

**Swan call (default backend):**
```matlab
problem.backend    = 'swan';          % default
problem.input_file = 'bracket.json';
problem.method     = 'levelset';      % 'density' | 'levelset'
problem.volume_frac = 0.4;
problem.max_iter   = 100;
result = swan_wrapper(problem);
% result.output_vtk, result.compliance, result.converged
```

**FreeTO backend via Swan wrapper:**
```matlab
problem.backend      = 'freeto';      % delegates to freeto_wrapper()
problem.domain_stl   = 'bracket.stl';
problem.force_stl    = 'force.stl';
problem.fixed_stl    = 'fixed.stl';
problem.mesh_control = 80;
problem.volume_frac  = 0.3;
problem.youngs_mod   = 210e9;
problem.method       = 'SIMP';        % 'SIMP' | 'SEMDOT'
result = swan_wrapper(problem);
% result.compliance, result.eleden, result.gridden
```

**Path setup:**
```matlab
addpath(genpath('/opt/Swan'))     % github.com/SwanLab/Swan
addpath(genpath('/opt/FreeTO'))   % required when backend='freeto'
```

---

## How the Python MCP server calls MATLAB

```python
import matlab.engine
eng = matlab.engine.start_matlab("-nojvm -nodisplay")
result = eng.freeto_wrapper(problem_struct, nargout=1)
# or
result = eng.swan_wrapper(problem_struct, nargout=1)
eng.quit()
```

## Octave fallback

```python
import oct2py
oc = oct2py.Oct2Py()
result = oc.freeto_wrapper(problem)
```

Octave ≥ 7.3 required. Both FreeTO and Swan work in Octave
(no MATLAB-only toolboxes required).

## Adding a new wrapper

1. Create `<tool>/<tool>_wrapper.m` following the input/output struct pattern.
2. Add an entry to this README.
3. Add a Python MCP tool in `forge-tools/mcp-wrappers/`.
4. Add the tool ID to `docs/toolchain/canonical-toolchain-reference.md`.
