function result = swan_wrapper(problem)
% SWAN_WRAPPER  MCP-compatible MATLAB wrapper for Swan topology optimiser.
%
% Swan (github.com/SwanLab/Swan) is a research-grade topology optimiser
% with level-set and density-based methods.  License: Academic (see
% docs/research/swan-license-paths.md before using in commercial context).
%
% Inputs
% ------
%   problem : struct with fields:
%     .input_file   - path to Swan .json input deck
%     .output_dir   - directory for Swan output files
%     .method       - 'density' | 'levelset'  (default: 'density')
%     .volume_frac  - target volume fraction (e.g. 0.4)
%     .max_iter     - max optimisation iterations (default: 100)
%
% Outputs
% -------
%   result : struct with fields:
%     .output_vtk   - path to output VTK file (for post-processing)
%     .compliance   - final compliance value
%     .iterations   - actual iterations run
%     .converged    - logical
%     .error        - error string (empty if success)
%
% Swan path setup
% ---------------
%   addpath(genpath('/opt/Swan'));  % Swan root
%
% This wrapper is called by the Python MCP server via MATLAB Engine API.
% See: docs/research/swan-license-paths.md

result = struct();
result.output_vtk  = '';
result.compliance  = Inf;
result.iterations  = 0;
result.converged   = false;
result.error       = '';

% ── Input validation ─────────────────────────────────────────────────────────
if ~isfield(problem, 'input_file') || isempty(problem.input_file)
    result.error = 'Missing required field: input_file';
    return
end

if ~isfield(problem, 'method')
    problem.method = 'density';
end

% ── Swan availability check ───────────────────────────────────────────────────
if exist('TopOpt', 'class') ~= 8
    result.error = ['Swan TopOpt class not found on MATLAB path. ' ...
                    'Add Swan to path: addpath(genpath(''/opt/Swan''))'];
    return
end

% ── Swan call (production) ────────────────────────────────────────────────────
% Replace stub with:
%
%   settings = SettingsTopOpt(problem.input_file);
%   settings.optimizer  = 'SLERP';
%   settings.volumeTarget = problem.volume_frac;
%   settings.maxIterations = problem.max_iter;
%   tOpt = TopOpt(settings);
%   tOpt.compute();
%   result.output_vtk  = tOpt.getOutputFile();
%   result.compliance  = tOpt.getCompliance();
%   result.iterations  = tOpt.getIterations();
%   result.converged   = tOpt.hasConverged();

result.error = 'Swan stub — install Swan and uncomment production call above';

end
