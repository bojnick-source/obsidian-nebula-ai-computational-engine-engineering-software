function result = swan_wrapper(problem)
% SWAN_WRAPPER  MCP-compatible MATLAB wrapper for Swan topology optimiser,
%               with FreeTO as an optional STL-geometry backend.
%
% Swan (github.com/SwanLab/Swan) — research-grade topology optimisation
% supporting level-set and density-based methods.
%
% FreeTO (github.com/ooibhadode/FreeTO) — freeform 3D topology optimisation
% with STL-geometry input, SIMP/SEMDOT methods, multi-load-case support,
% and structured hexahedral meshing.
%
% When problem.backend == 'freeto' this wrapper delegates entirely to
% freeto_wrapper(), returning a result struct with FreeTO's output fields.
% This allows the FORGE MCP server to use a single tool call for both engines.
%
% Inputs
% ------
%   problem : struct with fields:
%
%   SHARED (both backends)
%     .backend       - 'swan' (default) | 'freeto'
%     .volume_frac   - target volume fraction in (0, 1)
%     .method        - Swan: 'density'|'levelset'  FreeTO: 'SIMP'|'SEMDOT'
%
%   SWAN-SPECIFIC
%     .input_file    - path to Swan .json input deck  [required for Swan]
%     .output_dir    - directory for Swan output files
%     .max_iter      - max optimisation iterations (default: 100)
%
%   FREETO-SPECIFIC  (passed through to freeto_wrapper verbatim)
%     .domain_stl    - STL defining the design domain  [required for FreeTO]
%     .force_stl     - STL for primary load region
%     .fixed_stl     - STL for fully fixed boundary
%     .mesh_control  - mesh refinement integer (e.g. 80)
%     .youngs_mod    - Young's modulus in Pa (e.g. 210e9)
%     .poissons_ratio, .Fmagx, .Fmagy, .Fmagz  (see freeto_wrapper.m)
%     .force2_stl ... .force3_stl  — additional load cases
%     .xfixed_stl, .yfixed_stl, .zfixed_stl  — direction-only constraints
%     .keepdom_stl   — non-designable solid region
%     .symmetry1 .. .symmetry3 + .symmetry1_dir .. — mirror planes
%     .keep_bc, .model_name  — output control
%
% Outputs
% -------
%   Swan backend:
%     .output_vtk   - path to output VTK file
%     .compliance   - final compliance
%     .iterations   - actual iterations run
%     .converged    - logical
%     .error        - error string (empty if success)
%     .backend      - 'swan'
%
%   FreeTO backend (fields from freeto_wrapper):
%     .compliance, .volume_frac, .eleden, .gridden
%     .elenum_active, .elenum_total, .error
%     .backend      - 'freeto'
%
% Path setup
% ----------
%   Swan:   addpath(genpath('/opt/Swan'))
%   FreeTO: addpath(genpath('/opt/FreeTO'))
%
% This wrapper is called by the Python MCP server via MATLAB Engine API:
%   import matlab.engine
%   eng = matlab.engine.start_matlab()
%   result = eng.swan_wrapper(problem, nargout=1)
%
% See: forge-tools/mcp-wrappers/matlab_engine_server.py

result = struct();
result.error   = '';
result.backend = '';

% ── Backend selection ─────────────────────────────────────────────────────────
if ~isfield(problem, 'backend')
    problem.backend = 'swan';
end

backend = lower(strtrim(problem.backend));

% ── FreeTO delegation ─────────────────────────────────────────────────────────
if strcmp(backend, 'freeto')
    result = freeto_wrapper(problem);
    result.backend = 'freeto';
    return
end

% ── Swan path ─────────────────────────────────────────────────────────────────
result.output_vtk  = '';
result.compliance  = Inf;
result.iterations  = 0;
result.converged   = false;
result.backend     = 'swan';

% ── Input validation ──────────────────────────────────────────────────────────
if ~isfield(problem, 'input_file') || isempty(problem.input_file)
    result.error = 'Missing required field: input_file (Swan backend)';
    return
end

if ~isfield(problem, 'method'),   problem.method   = 'density'; end
if ~isfield(problem, 'max_iter'), problem.max_iter = 100;       end
if ~isfield(problem, 'volume_frac')
    result.error = 'Missing required field: volume_frac';
    return
end

% ── Swan availability check ───────────────────────────────────────────────────
if exist('TopOpt', 'class') ~= 8
    result.error = ['Swan TopOpt class not found on MATLAB path. ' ...
                    'Clone github.com/SwanLab/Swan and call: ' ...
                    'addpath(genpath(''/opt/Swan''))'];
    return
end

% ── Swan call ─────────────────────────────────────────────────────────────────
try
    settings = SettingsTopOpt(problem.input_file);
    settings.optimizer     = 'SLERP';
    settings.volumeTarget  = problem.volume_frac;
    settings.maxIterations = problem.max_iter;

    if strcmp(problem.method, 'levelset')
        settings.method = 'LevelSet';
    else
        settings.method = 'Density';
    end

    if isfield(problem, 'output_dir') && ~isempty(problem.output_dir)
        settings.outputPath = problem.output_dir;
    end

    tOpt = TopOpt(settings);
    tOpt.compute();

    result.output_vtk  = tOpt.getOutputFile();
    result.compliance  = tOpt.getCompliance();
    result.iterations  = tOpt.getIterations();
    result.converged   = tOpt.hasConverged();
catch ME
    result.error = ME.message;
end

end
