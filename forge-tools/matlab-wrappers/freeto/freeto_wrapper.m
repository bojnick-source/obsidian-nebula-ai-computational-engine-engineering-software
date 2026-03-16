function result = freeto_wrapper(problem)
% FREETO_WRAPPER  MCP-compatible MATLAB wrapper for FreeTO topology optimiser.
%
% FreeTO (github.com/ooibhadode/FreeTO) — Freeform 3D Topology Optimization
% using structured hexahedral meshes. Supports SIMP and SEMDOT methods with
% STL-based geometry input, multi-load-case support, and symmetry constraints.
%
% Inputs
% ------
%   problem : struct with fields:
%
%   REQUIRED
%     .domain_stl    - path to STL file defining the design domain
%     .force_stl     - path to STL file for the primary load region (force1)
%     .fixed_stl     - path to STL file for fully fixed boundary region
%     .mesh_control  - integer mesh refinement parameter (e.g. 80)
%     .volume_frac   - target volume fraction in (0, 1) (e.g. 0.3)
%     .youngs_mod    - Young's modulus in Pa (e.g. 210e9 for steel)
%
%   OPTIONAL
%     .poissons_ratio  - Poisson's ratio (default: 0.3)
%     .method          - 'SIMP' (default) | 'SEMDOT'
%     .Fmagx           - load magnitudes in x per load case, 1×N (default: 0)
%     .Fmagy           - load magnitudes in y per load case, 1×N (default: 0)
%     .Fmagz           - load magnitudes in z per load case, 1×N (default: 0)
%     .force2_stl      - STL for second load region (additional load case)
%     .force3_stl      - STL for third load region
%     .xfixed_stl      - STL for x-direction-only constraint region
%     .yfixed_stl      - STL for y-direction-only constraint region
%     .zfixed_stl      - STL for z-direction-only constraint region
%     .keepdom_stl     - STL for non-designable (always solid) region
%     .symmetry1       - mirror plane: 'x' | 'y' | 'z'
%     .symmetry2       - second mirror plane
%     .symmetry3       - third mirror plane
%     .symmetry1_dir   - mirror direction: 'right' (default) | 'left'
%     .symmetry2_dir   - mirror direction for plane 2
%     .symmetry3_dir   - mirror direction for plane 3
%     .keep_bc         - include load/support regions in result: 'Yes'/'No'
%     .model_name      - output STL filename (empty = no STL export)
%
% Outputs
% -------
%   result : struct with fields:
%     .compliance   - final compliance value (lower = stiffer structure)
%     .volume_frac  - volume fraction achieved
%     .eleden       - element density array [0,1] (active elements)
%     .gridden      - grid density array [0,1] (full domain)
%     .elenum_active  - number of active elements
%     .elenum_total   - total number of elements
%     .error          - error message string (empty if success)
%
% FreeTO path setup
% -----------------
%   addpath(genpath('/opt/FreeTO'));  % FreeTO root from github.com/ooibhadode/FreeTO
%
% Equivalent direct FreeTO call (GE bracket example):
%   FreeTO('GE_domain.stl', 'GE_force.stl', 80, 0.3, ...
%          'fixed', 'GE_fixed.stl', ...
%          'force2', 'GE_force.stl', ...
%          'Fmagy', [0 -2000], 'Fmagz', [1500 0], ...
%          'YoungsModulus', 210e9)
%
% This wrapper is called by the Python MCP server via MATLAB Engine API:
%   import matlab.engine
%   eng = matlab.engine.start_matlab()
%   result = eng.freeto_wrapper(problem, nargout=1)
%
% See: forge-tools/mcp-wrappers/matlab_engine_server.py

result = struct();
result.compliance    = Inf;
result.volume_frac   = 0;
result.eleden        = [];
result.gridden       = [];
result.elenum_active = 0;
result.elenum_total  = 0;
result.error         = '';

% ── Input validation ──────────────────────────────────────────────────────────
required = {'domain_stl', 'force_stl', 'fixed_stl', ...
            'mesh_control', 'volume_frac', 'youngs_mod'};
for i = 1:numel(required)
    if ~isfield(problem, required{i}) || isempty(problem.(required{i}))
        result.error = ['Missing required field: ' required{i}];
        return
    end
end

if problem.volume_frac <= 0 || problem.volume_frac >= 1
    result.error = 'volume_frac must be strictly in (0, 1)';
    return
end

if ~isfield(problem, 'poissons_ratio'), problem.poissons_ratio = 0.3;     end
if ~isfield(problem, 'method'),         problem.method = 'SIMP';           end
if ~isfield(problem, 'Fmagx'),          problem.Fmagx = 0;                 end
if ~isfield(problem, 'Fmagy'),          problem.Fmagy = 0;                 end
if ~isfield(problem, 'Fmagz'),          problem.Fmagz = 0;                 end
if ~isfield(problem, 'keep_bc'),        problem.keep_bc = 'Yes';           end

% ── FreeTO availability check ─────────────────────────────────────────────────
if exist('FreeTO', 'file') ~= 2
    result.error = ['FreeTO not found on MATLAB path. ' ...
                    'Clone github.com/ooibhadode/FreeTO and call: ' ...
                    'addpath(genpath(''/opt/FreeTO''))'];
    return
end

% ── Build property name-value argument list ───────────────────────────────────
% FreeTO(file, force1, MeshControl, volfrac, 'PropertyName', VALUE, ...)
props = {};

% Boundary conditions
props{end+1} = 'fixed';
props{end+1} = problem.fixed_stl;

if isfield(problem, 'xfixed_stl') && ~isempty(problem.xfixed_stl)
    props{end+1} = 'xfixed'; props{end+1} = problem.xfixed_stl;
end
if isfield(problem, 'yfixed_stl') && ~isempty(problem.yfixed_stl)
    props{end+1} = 'yfixed'; props{end+1} = problem.yfixed_stl;
end
if isfield(problem, 'zfixed_stl') && ~isempty(problem.zfixed_stl)
    props{end+1} = 'zfixed'; props{end+1} = problem.zfixed_stl;
end

% Additional load cases
if isfield(problem, 'force2_stl') && ~isempty(problem.force2_stl)
    props{end+1} = 'force2'; props{end+1} = problem.force2_stl;
end
if isfield(problem, 'force3_stl') && ~isempty(problem.force3_stl)
    props{end+1} = 'force3'; props{end+1} = problem.force3_stl;
end

% Load magnitudes
props{end+1} = 'Fmagx'; props{end+1} = problem.Fmagx;
props{end+1} = 'Fmagy'; props{end+1} = problem.Fmagy;
props{end+1} = 'Fmagz'; props{end+1} = problem.Fmagz;

% Material
props{end+1} = 'YoungsModulus';  props{end+1} = problem.youngs_mod;
props{end+1} = 'PoissonsRatio';  props{end+1} = problem.poissons_ratio;

% Optimization method
props{end+1} = 'optimization'; props{end+1} = problem.method;

% Non-designable region
if isfield(problem, 'keepdom_stl') && ~isempty(problem.keepdom_stl)
    props{end+1} = 'keepdom'; props{end+1} = problem.keepdom_stl;
end

% Symmetry constraints (up to 3 mirror planes)
sym_fields = {'symmetry1', 'symmetry2', 'symmetry3'};
dir_fields = {'symmetry1_dir', 'symmetry2_dir', 'symmetry3_dir'};
prop_names = {'Symmetry1', 'Symmetry2', 'Symmetry3'};
dir_names  = {'direction1', 'direction2', 'direction3'};
for i = 1:3
    if isfield(problem, sym_fields{i}) && ~isempty(problem.(sym_fields{i}))
        props{end+1} = prop_names{i}; props{end+1} = problem.(sym_fields{i});
        dir = 'right';
        if isfield(problem, dir_fields{i}), dir = problem.(dir_fields{i}); end
        props{end+1} = dir_names{i}; props{end+1} = dir;
    end
end

% BC inclusion
props{end+1} = 'keep_BC'; props{end+1} = problem.keep_bc;

% Output STL
if isfield(problem, 'model_name') && ~isempty(problem.model_name)
    props{end+1} = 'modelName'; props{end+1} = problem.model_name;
end

% ── FreeTO call ───────────────────────────────────────────────────────────────
try
    [comp, finalvol, eleden, gridden, elenum1, elenum2] = FreeTO( ...
        problem.domain_stl, problem.force_stl, ...
        problem.mesh_control, problem.volume_frac, ...
        props{:});

    result.compliance    = comp;
    result.volume_frac   = finalvol;
    result.eleden        = eleden;
    result.gridden       = gridden;
    result.elenum_active = elenum1;
    result.elenum_total  = elenum2;
catch ME
    result.error = ME.message;
end

end
