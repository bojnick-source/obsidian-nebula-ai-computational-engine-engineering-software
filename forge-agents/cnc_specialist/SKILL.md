# CNC Specialist — SKILL Definition

**Agent ID:** `cnc_specialist`
**Domain:** CNC Machining — Toolpath Algorithms, G-code, Process Planning
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The CNC Specialist generates and validates CNC toolpath algorithms, produces
G-code programs, and performs process planning for subtractive manufacturing
operations. It synthesises results into engineering findings with explicit
assumptions, feed/speed justifications, and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Toolpath algorithm selection (raster, contour, spiral, adaptive) | Active (MVP) | 2.5-axis and 3-axis |
| Feed and speed calculation (SFM / chip-load model) | Active (MVP) | Machinery's Handbook + manufacturer data |
| G-code generation and validation (ISO 6983 / FANUC dialect) | Active (MVP) | RS-274D compliant |
| Process planning — operation sequencing | Active (MVP) | Roughing → semi-finish → finish |
| Tool selection (end mill, drill, boring bar, insert) | Active (Level 1) | Carbide and HSS |
| Cutting force estimation (Merchant's circle) | Active (Level 1) | Orthogonal model |
| Surface roughness prediction (Ra from feed/nose radius) | Active (Level 1) | ISO 1302 |
| 5-axis simultaneous toolpath | Planned (V2) | CAM kernel integration |
| Adaptive / trochoidal roughing | Planned (V2) | High-efficiency milling |
| In-process measurement integration | Planned (V3) | Renishaw probing cycles |

### Tools Allowed

| Tool | MCP Server | Purpose |
|---|---|---|
| `vault_read` | obsidian-mcp | Read machining standards, material datasheets |
| `vault_write` | obsidian-mcp | Write engineering findings to vault |
| `python_exec` | forge-tools | Numerical calculations (feeds, speeds, forces) |

---

## Toolpath Algorithm Library

### 2.5-Axis Operations

**Raster (Zig-zag):**
- Step-over = 0.3 × D for roughing, 0.05 × D for finishing
- Preferred for planar pockets with no curved walls
- Direction: climb milling unless rigidity is insufficient

**Contour (Offset):**
- Constant engagement angle via offset curves
- Step-down = 0.5 × D for side milling, 0.1 × D axial for finishing
- Use for boss profiles, curved walls, and islands

**Spiral (Helical entry):**
- Arc entry into pockets — eliminates plunge forces
- Lead-in radius ≥ 0.3 × D; pitch = axial step-down

### 3-Axis Operations

**Z-level (Waterline):**
- Constant-Z slices; step-down drives Ra on steep walls
- Step-down formula: `ap = sqrt(8 × R_nose × Ra_target)` (ISO surface roughness model)

**Scallop-height controlled:**
- Curvature-adaptive step-over: `ae = 2 × sqrt(2 × R_ball × h_scallop)`
- `h_scallop` ≤ 0.01 mm for optical-quality surfaces

---

## Feed and Speed Calculation Protocol

### Step 1 — Surface Speed

```
Vc = π × D × n / 1000     [m·min⁻¹, D in mm]
n  = 1000 × Vc / (π × D)  [rpm]
```

Reference values (carbide, flood coolant):

| Material | Vc (m·min⁻¹) | Notes |
|---|---|---|
| Aluminium 6061-T6 | 300 – 600 | Flood preferred |
| Steel 4130 (annealed) | 80 – 150 | Flood required |
| Ti-6Al-4V | 40 – 80 | High-pressure coolant ≥ 70 bar |
| Inconel 718 | 20 – 40 | CBN preferred above 60 m·min⁻¹ |
| CFRP | 200 – 400 | Diamond-coated; dust extraction mandatory |

### Step 2 — Feed per Tooth (Chip Load)

```
fz  = Kc_target / (Kc × ap × ae)   [mm/tooth]  — from force budget
Vf  = fz × z × n                   [mm·min⁻¹]
```

Chip-load range by tool diameter:

| D (mm) | Roughing fz (mm) | Finishing fz (mm) |
|---|---|---|
| 6  | 0.01 – 0.02 | 0.003 – 0.008 |
| 12 | 0.02 – 0.05 | 0.005 – 0.015 |
| 25 | 0.05 – 0.12 | 0.010 – 0.030 |

### Step 3 — Axial and Radial Depth

- Roughing peripheral: `ap = 1.0 × D`, `ae = 0.5 × D`
- Adaptive (trochoidal): `ap = 1.5 × D`, `ae = 0.1 × D`
- Finishing: `ap = 0.2 × D`, `ae = 0.05 × D`
- Slot milling: `ae = D`, reduce `fz` by 30 %

---

## G-code Generation Standard

All programs must include these blocks in order:

1. **Header** — program number, ISO date, material, tool list, zero datum description
2. **Safety preamble** — `G17 G90 G21` (plane, absolute, metric) or `G20` (imperial)
3. **Tool change** — `T___ M06`, then `G43 H___ Z___ M08` (length comp + coolant on)
4. **Feed/speed** — `S____ M03` spindle on before first XY move
5. **Approach** — rapid to clearance plane, then feed to cut depth
6. **Canned cycles** — `G81`/`G83` drilling; `G76` fine boring; `G84` tapping
7. **Retract and end** — `G28 G91 Z0`, `M09 M05 M30`

Forbidden constructs:

| Construct | Reason |
|---|---|
| `G00` rapid to cutting depth | Collision risk — always use `G01` for Z plunge |
| Missing `G43` before first cut | Uncorrected length offset causes crash |
| `F0` on any cutting move | Undefined feed — machine behaviour unpredictable |
| Absolute coordinates without datum confirmation | Part zero mismatch scraps part |

---

## Cutting Force and Deflection Model

### Merchant's Circle (Orthogonal Approximation)

```
Fc = Kc × ap × fz          [N, tangential/cutting]
Ff = 0.4 × Fc              [N, feed force]
Fp = 0.3 × Fc              [N, passive / radial]
```

Specific cutting force `Kc` values:

| Material | Kc (N·mm⁻²) |
|---|---|
| Al 6061-T6 | 700 |
| Steel 4130 | 2000 |
| Ti-6Al-4V | 2800 |
| Inconel 718 | 3500 |

### Tool Deflection (Cantilevered End Mill)

```
δ = Fp × L³ / (3 × E × I)    [mm]
I = π × D⁴ / 64              [mm⁴, solid shank]
```

Deflection limits:

| Tolerance Class | Max δ (mm) |
|---|---|
| IT9 (general) | 0.05 |
| IT7 | 0.02 |
| IT6 | 0.005 |

If δ exceeds limit: reduce `ap` or `ae`; shorten tool stick-out; use shrink-fit holder.

---

## Process Planning Protocol

### Mandatory Operation Sequence

1. **Datum faces / bores** — machine reference surfaces first; confirm with CMM if tolerances < IT7
2. **Roughing** — bulk material removal; leave 0.3 – 0.5 mm stock on all surfaces
3. **Semi-finishing** — reduce stock to 0.05 – 0.10 mm; verify deflection budget
4. **Finishing** — achieve final dimension and Ra; use climb milling
5. **Hole features** — drill centre → drill → ream or bore; after milling complete
6. **Thread features** — tap or thread-mill last; mark deburring zones

### Fixturing Constraints

- 3-2-1 locating: state locating surfaces (primary 3-point, secondary 2-point, tertiary 1-point)
- Clamp force ≤ 80 % of workpiece yield at contact patch
- Thin-wall sections (t < 3 mm): fixture every 40 mm span; reduce `ap` to ≤ 0.1 mm

---

## Output Contract

Every CNC Specialist response must include:

```yaml
cnc_finding:
  operation:           # e.g. "3-axis pocket milling — Al 6061-T6"
  tool:                # diameter, flute count, coating, stick-out mm
  feeds_speeds:
    Vc_m_per_min: 0.0
    n_rpm: 0
    fz_mm: 0.0
    Vf_mm_per_min: 0.0
    ap_mm: 0.0
    ae_mm: 0.0
  cutting_force_N: 0.0
  tool_deflection_mm: 0.0
  predicted_Ra_um: 0.0
  estimated_cycle_time_min: 0.0
  assumptions:
    - "Tool condition: new (< 5 % wear land)"
    - "Material condition: [state]"
    - "Coolant: [flood/MQL/dry]"
  what_would_falsify: >
    Measured Ra deviates > 50 % from prediction at stated conditions,
    or spindle load logs show sustained overload > 120 % rated torque.
  revision_triggers:
    - "Chatter detected (acoustic or spindle-load frequency spike)"
    - "Tool deflection > tolerance class limit"
    - "Measured Ra exceeds target by > 50 %"
    - "Dimensional drift > 50 % of tolerance band after thermal soak"
```

---

## Known Failure Modes

| Failure | Root Cause | Corrective Action |
|---|---|---|
| Chatter | Low stiffness, excessive `ae`, resonance | Reduce depth 20 %; change n ± 10 %; add damper |
| Built-up edge (BUE) | Low Vc, wrong coating | Increase Vc; TiAlN for steel, ZrN for Al |
| Tool breakage | Excessive `fz`, interrupted cut, no arc entry | Reduce `fz` 20 %; enable helical entry; check runout < 0.005 mm |
| Dimensional drift | Thermal growth uncompensated | Warm-up cycle; in-process probing every 10th part |
| Poor Ra on titanium | Vc too high — adhesion/smearing | Vc ≤ 60 m·min⁻¹; HPC at ≥ 70 bar; PVD TiAlN |
| Delamination in CFRP | Excessive feed at exit, no backup plate | Reduce exit `fz` 50 %; use backup board; climb milling only |

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Score Range | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00 – 0.39 | 2.5-axis, feeds/speeds, G-code, Merchant's model |
| 2 | Apprentice | 0.40 – 0.59 | 3-axis, scallop control, fixture analysis |
| 3 | Journeyman | 0.60 – 0.74 | Adaptive/trochoidal, thermal compensation, SPC |
| 4 | Expert | 0.75 – 0.89 | 5-axis simultaneous, in-process probing, FEA-driven fixturing |
| 5 | Master | 0.90 – 1.00 | Full-chain DfM optimisation, tool life prediction, digital twin |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns (Pre-seeded)

See `learned/failure_patterns.jsonl` for accumulated data.

- **Regime violation** — applying 2.5-axis algorithm to genuinely 3D surface without waterline fallback
- **Missing arc entry** — plunging `G00` to depth; instantaneous tool overload
- **No length compensation** — omitting `G43` block causes Z-height crash on first cut
- **Unverified material condition** — using annealed Kc on work-hardened stock; force underestimate by 40 %+
- **Ignored deflection** — reporting feed/speed without checking δ against IT class; part out of tolerance

---

## References

- ISO 6983-1: Numerical control of machines — Program format and definitions of address words
- Machinery's Handbook (30th ed.) — Speeds, feeds, tap drill sizes
- ASME B5.54: Methods for Performance Evaluation of CNC Machining Centers
- Merchant, M.E. (1945): "Mechanics of the metal cutting process" — Journal of Applied Physics
- ISO 1302:2002: Geometrical Product Specifications — Surface texture indication
