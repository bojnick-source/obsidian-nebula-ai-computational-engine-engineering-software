function result = freeto_wrapper(problem)
% FREETO_WRAPPER  MCP-compatible MATLAB wrapper for FreeTO topology optimiser.
%
% Inputs
% ------
%   problem : struct with fields:
%     .voxel_size   - element size in mm (e.g. 2.0)
%     .volume_frac  - target volume fraction (e.g. 0.3)
%     .load_cases   - Nx6 matrix [Fx Fy Fz Mx My Mz] per load case
%     .fixed_nodes  - node indices with zero displacement
%     .material     - struct with .E (GPa), .nu, .density (kg/m^3)
%
% Outputs
% -------
%   result : struct with fields:
%     .density_field - element densities [0,1], size (Nx Ny Nz)
%     .compliance    - final compliance value
%     .iterations    - number of optimisation iterations
%     .converged     - logical: did the optimiser converge?
%     .error         - error message string (empty if success)
%
% Notes
% -----
%   FreeTO must be on the MATLAB path:
%     addpath('/opt/freeto');  % or wherever FreeTO is installed
%
%   Octave compatibility: FreeTO uses features available in Octave >= 7.3.
%   Set FORGE_USE_OCTAVE=1 env var to force Octave-safe code paths.
%
%   This wrapper is called by the Python MCP server via MATLAB Engine API:
%     import matlab.engine
%     eng = matlab.engine.start_matlab()
%     result = eng.freeto_wrapper(problem, nargout=1)
%
%   See: forge-tools/mcp-wrappers/matlab_engine_server.py

result = struct();
result.density_field = [];
result.compliance    = Inf;
result.iterations    = 0;
result.converged     = false;
result.error         = '';

% ── Input validation ─────────────────────────────────────────────────────────
required = {'voxel_size', 'volume_frac', 'load_cases', 'fixed_nodes', 'material'};
for i = 1:numel(required)
    if ~isfield(problem, required{i})
        result.error = ['Missing required field: ' required{i}];
        return
    end
end

if problem.volume_frac <= 0 || problem.volume_frac >= 1
    result.error = 'volume_frac must be in (0, 1)';
    return
end

% ── FreeTO call ───────────────────────────────────────────────────────────────
% Production: replace with actual FreeTO API call.
% FreeTO uses SIMP method (Solid Isotropic Material with Penalisation).
%
%   [rho, compliance, iter] = freeto_simp( ...
%       mesh, bcs, loads, problem.volume_frac, ...
%       'penalty', 3.0, ...
%       'filter_radius', 1.5 * problem.voxel_size, ...
%       'max_iter', 200, ...
%       'tol', 1e-4 ...
%   );

% Stub: return uniform density field at target volume fraction.
% Replace this block with the real FreeTO call when FreeTO is on the path.
if exist('freeto_simp', 'file') ~= 2
    result.error = ['FreeTO not found on MATLAB path. ' ...
                    'Install FreeTO and call addpath before using this wrapper.'];
    return
end

% Placeholder — unreachable until FreeTO is installed.
result.error = 'freeto_simp not yet called — stub only';

end
