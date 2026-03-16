# FORGE MATLAB / Octave Wrappers

Language tier: **MATLAB / Octave**
Role per [Polyglot Architecture Doctrine](../../docs/architecture/polyglot-doctrine.md):
FreeTO, Swan, topology optimization, established math/engineering toolboxes.

---

## Wrappers

| Wrapper | Tool | Method | License |
|---|---|---|---|
| `freeto/freeto_wrapper.m` | FreeTO | SIMP density | MIT |
| `swan/swan_wrapper.m` | Swan | Density / Level-set | Academic |

---

## How the Python MCP server calls MATLAB

The Python MCP server uses the **MATLAB Engine API for Python**:

```python
import matlab.engine
eng = matlab.engine.start_matlab("-nojvm -nodisplay")
result = eng.freeto_wrapper(problem_struct, nargout=1)
eng.quit()
```

Source: `forge-tools/mcp-wrappers/matlab_engine_server.py` *(planned)*

## Octave fallback

Set `FORGE_USE_OCTAVE=1` to route calls through `oct2py` instead of
the MATLAB Engine:

```python
import oct2py
oc = oct2py.Oct2Py()
result = oc.freeto_wrapper(problem)
```

Octave ≥ 7.3 required. MATLAB-only toolboxes (Statistics, Optimization)
are not available in Octave — topology optimisers do not require them.

## Adding a new wrapper

1. Create `<tool>/<tool>_wrapper.m` following the input/output struct pattern.
2. Add an entry to this README.
3. Add a Python MCP tool in `forge-tools/mcp-wrappers/` that calls it.
4. Add the tool ID to `docs/toolchain/canonical-toolchain-reference.md`.
