# swan-topology — Topology Optimization Source

MATLAB source from [SwanLab/Swan](https://github.com/SwanLab/Swan) (CIMNE, Barcelona).
Source commit: `main` branch as of 2026-03-15.

Swan is the **preferred solver** for the `topology_optimization` FORGE workflow agent.

## What Was Copied

| Path | Content |
|---|---|
| `src/` | Full MATLAB source — all modules (14 MB) |
| `Test/TopOptTests/` | Canonical topology optimization test cases and inputs |
| `Tutorials/` | Wiki tutorials and Chomog network tutorial |
| `startupSwan.m` | MATLAB path setup (adapt `userpath` to this directory) |
| `UserVariables.m` | Global configuration (GiD path, default export software) |
| `README_upstream.md` | Original upstream README |

Excluded: `Old/` (legacy archive), `Test/FemTests/` (59 MB binary .mat data files),
all other `Test/` subdirectories (unrelated to topology optimization).

## Quick Start (MATLAB)

```matlab
% 1. In startupSwan.m, set userpath = '<path-to-this-directory>'
% 2. Copy startupSwan.m → ~/Matlab/R202X/toolbox/local/startup.m
% 3. Open MATLAB — Swan is on path automatically
% 4. Run a canonical test:
filename = 'CantileverBeam_Triangle_Linear';
a.fileName = filename;
gid = FemDataContainer(a);
ptype      = 'MACRO';
method     = 'SIMPALL';
materialType = 'ISOTROPIC';
cost       = {'compliance', 'perimeter'};
weights    = [1 0.1];
constraint = {'volumeConstraint'};
constraint_case = {'EQUALITY'};
target     = 0.3;
optimizer  = 'AlternatingPrimalDual';
designVariable = 'Density';
maxiter    = 100;
```

## Module Map

### `src/Problems/Optimization/` — Core Optimizers

| File | Role |
|---|---|
| `DesignVariables/Density.m` | SIMP density variable |
| `DesignVariables/LevelSet.m` | Level-set design variable |
| `DesignVariables/MultiLevelSet.m` | Multi-phase level-set |
| `Optimizers/Constrained/OptimizerMMA.m` | Method of Moving Asymptotes |
| `Optimizers/Constrained/OptimizerAugmentedLagrangian.m` | Augmented Lagrangian |
| `Optimizers/Constrained/InteriorPoints/OptimizerInteriorPoint.m` | Interior Point (IPM) |
| `Optimizers/Constrained/Bisection/OptimizerBisection.m` | Bisection method |
| `Optimizers/Unconstrained/OptimizerProjectedGradient.m` | Projected gradient |
| `Optimizers/PrimalUpdaters/HamiltonJacobi.m` | HJ level-set advection |
| `Optimizers/PrimalUpdaters/SLERP.m` | Spherical linear interpolation |
| `Topology/MaterialInterpolators/SimpAllExplicitInterpolator.m` | SIMP-ALL (Ferrer 2019) |
| `Topology/MaterialInterpolators/SimpInterpolationP3.m` | SIMP p=3 |
| `Topology/MaterialInterpolators/MultiMaterialInterpolation.m` | Multi-material |

### `src/Functionals/` — Cost and Constraint Functions

| File | Role |
|---|---|
| `ComplianceFunctional.m` | Structural compliance J = u·K·u |
| `VolumeConstraint.m` | Volume fraction constraint |
| `PerimeterFunctional.m` | Perimeter regularisation |
| `IsoPerimetricFunctional.m` | Isoperimetric perimeter |
| `IsotropicPerimeterNormPFunctional.m` | Anisotropy-aware perimeter |
| `FilteredVolumeFunctional.m` | Filtered volume (PDE filter) |
| `FilteredVolumeConstraint.m` | Filtered volume constraint |

### `src/Problems/Elasticity/` — FEA

| File | Role |
|---|---|
| `ElasticProblem.m` | Linear elasticity FEM solver |
| `ElasticProblemMicro.m` | Homogenisation FEM (unit cell) |

### `src/Problems/Filters/` — Density Filters

PDE-based filter (Helmholtz), linear filter (P1), projection filter (Heaviside).

### `src/Mesh/` — Mesh Handling

GiD and GMSH mesh readers, boundary mesh creator, unfitted mesh utilities.

### `src/Monitoring/` — Convergence Monitoring

Real-time plot of cost, constraint, and volume fraction per iteration.

### `src/ThirdParty/` — Output Wrappers

Paraview (VTK), GiD, GMSH post-processing output adapters.

## Key Input Parameters

Every Swan run is a MATLAB script setting these variables before calling the solver:

```matlab
ptype          % 'MACRO' | 'MICRO'
method         % 'SIMPALL' | 'SIMP' | 'LevelSet'
materialType   % 'ISOTROPIC' | 'ANISOTROPIC'
cost           % cell array: {'compliance'} | {'compliance','perimeter'}
weights        % row vector, sum need not = 1
constraint     % cell array: {'volumeConstraint'} | {'volumeConstraint','perimeterConstraint'}
constraint_case % {'EQUALITY'} | {'INEQUALITY'}
target         % volume fraction target (e.g. 0.3)
optimizer      % 'MMA' | 'AlternatingPrimalDual' | 'AugmentedLagrangian' | 'IPM' | 'Bisection'
designVariable % 'Density' | 'LevelSet' | 'MultiLevelSet'
filterCostType % {'P1'} | {'PDE'} | {'P1','PDE'} (one entry per cost term)
maxiter        % integer
plotting       % true | false
```

## Solver Hierarchy in FORGE

```
topology_optimization (FORGE agent)
  └─ preferred solver: Swan (MATLAB, this directory)
       ├─ Level-Set  → for AM + anisotropy constraints
       ├─ SIMP-ALL   → for density + metamaterial design
       └─ Fallback: FreeTO (MATLAB/Octave SIMP) → ToPy (Python) → scipy_simp
```

## Physical Path (FORGE integration)

```
swan-topology/src/      ← addpath(genpath(...)) target
swan-topology/Test/TopOptTests/Input/   ← canonical problem definitions
```

FORGE `topology_optimization` agent references this directory as the Swan installation root.
Set `SWAN_PATH=<repo_root>/swan-topology` before calling via MATLAB engine or subprocess.

## Upstream Reference

| Field | Value |
|---|---|
| Repository | https://github.com/SwanLab/Swan |
| License | MIT |
| Institution | CIMNE — UPC Barcelona |
| Lead developer | Dr. Alexandre Ferrer (`aferrer@cimne.upc.edu`) |
| Key paper | SIMP-ALL: Ferrer et al., *IJNME* 2019, DOI 10.1002/nme.6140 |
