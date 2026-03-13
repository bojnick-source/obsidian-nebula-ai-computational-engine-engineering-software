"""Parametric smart fuselage model.

Models a non-weaponised smart airframe across five maturity blocks:
  BLOCK_0 — monocoque/semi-monocoque composite structure
  BLOCK_1 — embedded structural health monitoring (SHM) fibres
  BLOCK_2 — embedded power distribution rails
  BLOCK_3 — distributed sensor/comms node tiles
  BLOCK_4 — conformal energy modules

Integrates with:
  forge_solver.atmosphere  — ISA air density at altitude
  forge_solver.fea         — FEA result type for downstream structural coupling
  forge_manufacturing.model — BlockLevel enum and block_gte() helper

C++ accuracy layer:
  forge-core/src/solver/fuselage_aero.cpp implements the Hoerner body drag
  integrals in float64 C++20 for deterministic, high-volume aerodynamic queries.

This module is intentionally standalone so it can be imported without
forge-manufacturing installed (BlockLevel is gracefully degraded to strings).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ── Aerodynamic constants ─────────────────────────────────────────────────────
_FLAT_PLATE_CF_REF_RE: float = 1.0e6  # Reference Reynolds number for Cf estimate
_HOERNER_K_FORM: float = 2.3          # Hoerner fuselage form factor (d/l ≈ 0.1–0.2)
_AIR_KINEMATIC_VISCOSITY_M2S: float = 1.5e-5  # ISA sea level [m²/s]

# ── Structural constants ──────────────────────────────────────────────────────
_EULER_BUCKLING_COEFF: float = 1.0   # Pin-pin column: C=1 (conservative)
_HOOP_STRESS_MARGIN: float = 0.1     # 10% pressure margin for internal pressure

# ── Smart layer capacity per block ────────────────────────────────────────────
# Capacities are parametric: scale with fuselage surface area and block level
_SHM_FIBRE_DENSITY_PER_M2: float = 20.0   # optical fibres per m² of wetted area
_POWER_RAIL_W_PER_M: float = 150.0        # W per metre of rail length
_COMMS_NODE_DENSITY_PER_M2: float = 1.5   # nodes per m²
_ENERGY_MODULE_J_PER_M3: float = 500_000.0  # conformal module energy density [J/m³]

# ── Material defaults (CFRP quasi-isotropic laminate) ─────────────────────────
_DEFAULT_ELASTIC_MODULUS_PA: float = 70e9   # Representative CFRP modulus
_DEFAULT_YIELD_STRENGTH_PA: float = 400e6   # Representative CFRP strength
_DEFAULT_DENSITY_KG_M3: float = 1600.0      # CFRP density


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FuselageGeometry:
    """Parametric fuselage geometry (circular cross-section body of revolution).

    Attributes:
        length_m:            Total fuselage length [m].
        max_diameter_m:      Maximum diameter (typically at ~40% chord) [m].
        nose_fineness:       Nose section length / max_diameter (dimensionless).
        tail_fineness:       Tail section length / max_diameter (dimensionless).
        skin_thickness_m:    Structural skin thickness [m].
        shell_type:          ``"monocoque"`` or ``"semi_monocoque"``.
    """

    length_m: float
    max_diameter_m: float
    nose_fineness: float = 2.0
    tail_fineness: float = 3.0
    skin_thickness_m: float = 0.003
    shell_type: str = "semi_monocoque"

    def __post_init__(self) -> None:
        if self.length_m <= 0:
            raise ValueError(f"length_m must be positive, got {self.length_m}")
        if self.max_diameter_m <= 0:
            raise ValueError(f"max_diameter_m must be positive, got {self.max_diameter_m}")
        if self.skin_thickness_m <= 0:
            raise ValueError(f"skin_thickness_m must be positive, got {self.skin_thickness_m}")
        if self.skin_thickness_m >= self.max_diameter_m / 2.0:
            raise ValueError("skin_thickness_m must be < max_diameter_m/2")
        if self.shell_type not in {"monocoque", "semi_monocoque"}:
            raise ValueError(
                f"shell_type must be 'monocoque' or 'semi_monocoque', got {self.shell_type!r}"
            )

    @property
    def fineness_ratio(self) -> float:
        """Overall fineness ratio l/d (dimensionless)."""
        return self.length_m / self.max_diameter_m

    @property
    def cross_section_area_m2(self) -> float:
        """Maximum cross-sectional area [m²]."""
        return math.pi * (self.max_diameter_m / 2.0) ** 2

    @property
    def wetted_area_m2(self) -> float:
        """Approximate wetted area using Sears-Haack-inspired estimate [m²].

        Uses Torenbeek's simplified formula: A_wet ≈ π·d·l·(1 - 2/3·(d/l)^...)
        Here simplified to a cylinder with hemispherical ends.
        """
        r = self.max_diameter_m / 2.0
        # Cylinder mid-section length (subtract nose + tail cones)
        l_cyl = max(0.0, self.length_m - (self.nose_fineness + self.tail_fineness) * self.max_diameter_m)
        a_cyl = 2.0 * math.pi * r * l_cyl
        # Nose cone lateral area: π·r·slant
        l_nose = self.nose_fineness * self.max_diameter_m
        a_nose = math.pi * r * math.sqrt(r ** 2 + l_nose ** 2)
        # Tail cone
        l_tail = self.tail_fineness * self.max_diameter_m
        a_tail = math.pi * r * math.sqrt(r ** 2 + l_tail ** 2)
        return a_cyl + a_nose + a_tail

    @property
    def structural_volume_m3(self) -> float:
        """Shell volume (material only, not interior) [m³]."""
        return self.wetted_area_m2 * self.skin_thickness_m

    @property
    def interior_volume_m3(self) -> float:
        """Approximate interior volume [m³] (cylinder + cones)."""
        r = self.max_diameter_m / 2.0
        l_cyl = max(0.0, self.length_m - (self.nose_fineness + self.tail_fineness) * self.max_diameter_m)
        v_cyl = math.pi * r ** 2 * l_cyl
        l_nose = self.nose_fineness * self.max_diameter_m
        l_tail = self.tail_fineness * self.max_diameter_m
        v_nose = math.pi * r ** 2 * l_nose / 3.0
        v_tail = math.pi * r ** 2 * l_tail / 3.0
        return v_cyl + v_nose + v_tail


@dataclass(frozen=True)
class FuselageAero:
    """Aerodynamic drag breakdown for the fuselage."""

    speed_ms: float
    altitude_m: float
    friction_drag_n: float       # Skin friction drag [N]
    form_drag_n: float           # Pressure/form drag [N]
    interference_drag_n: float   # Interference allowance [N]
    total_drag_n: float          # Total fuselage drag [N]
    cd_body: float               # Body drag coefficient (ref: max cross-section)
    reynolds_number: float


@dataclass(frozen=True)
class FuselageStructure:
    """Structural analysis summary for the fuselage shell."""

    bending_stress_pa: float        # Max bending stress under applied load [Pa]
    hoop_stress_pa: float           # Hoop stress under internal pressure [Pa]
    axial_buckling_load_n: float    # Euler critical buckling load [N]
    safety_factor_bending: float    # Yield margin for bending
    safety_factor_buckling: float   # Load / buckling load margin
    mass_kg: float                  # Structural shell mass [kg]


@dataclass
class SmartLayerConfig:
    """Embedded smart-layer capabilities for a given block level."""

    block_level: str                 # BLOCK_0 … BLOCK_4 as string
    shm_fibre_count: int = 0         # Structural health monitoring fibres
    power_rail_capacity_w: float = 0.0  # Embedded power rail capacity [W]
    comms_node_count: int = 0        # Sensor/comms nodes embedded
    energy_module_capacity_j: float = 0.0  # Conformal energy module capacity [J]
    notes: list[str] = field(default_factory=list)


@dataclass
class FuselageResult:
    """Complete smart fuselage analysis result."""

    geometry: FuselageGeometry
    aero: FuselageAero | None
    structure: FuselageStructure
    smart_layer: SmartLayerConfig
    cg_x_m: float                   # CG position along longitudinal axis [m]
    warnings: list[str] = field(default_factory=list)


# ── Aerodynamic analysis ──────────────────────────────────────────────────────


def _flat_plate_cf(reynolds: float) -> float:
    """Turbulent flat-plate skin friction coefficient (Prandtl-Schlichting).

    Cf = 0.455 / (log10(Re))^2.58  (valid for Re > 1e5)
    """
    if reynolds < 1e5:
        # Laminar Blasius: Cf = 1.328 / sqrt(Re)
        return 1.328 / math.sqrt(max(reynolds, 1.0))
    return 0.455 / (math.log10(max(reynolds, 1.0)) ** 2.58)


def compute_fuselage_aero(
    geom: FuselageGeometry,
    speed_ms: float,
    altitude_m: float = 0.0,
    air_density_kg_m3: float | None = None,
) -> FuselageAero:
    """Compute fuselage aerodynamic drag using Hoerner body drag method.

    Reference: Hoerner S.F., "Fluid Dynamic Drag", 1965, Chapter 6.

    Args:
        geom:               Fuselage geometry.
        speed_ms:           True airspeed [m/s].
        altitude_m:         Altitude for ISA density (overridden by air_density_kg_m3).
        air_density_kg_m3:  Air density override [kg/m³] (if None, uses ISA).

    Returns:
        :class:`FuselageAero` with drag breakdown.

    Raises:
        ValueError: If speed is non-positive.
    """
    if speed_ms <= 0:
        raise ValueError(f"speed_ms must be positive, got {speed_ms}")

    # Use provided density or compute from ISA
    if air_density_kg_m3 is None:
        from forge_solver.atmosphere import isa_atmosphere
        atm = isa_atmosphere(altitude_m)
        rho = atm.density_kg_m3
    else:
        rho = air_density_kg_m3

    q = 0.5 * rho * speed_ms ** 2  # dynamic pressure [Pa]

    # Reynolds number based on fuselage length
    re = speed_ms * geom.length_m / _AIR_KINEMATIC_VISCOSITY_M2S
    cf = _flat_plate_cf(re)

    # Skin friction drag
    d_fr = cf * geom.wetted_area_m2 * q

    # Form drag (Hoerner): Cd_form = k * (d/l)^3 * q * A_ref
    d_over_l = 1.0 / geom.fineness_ratio
    cd_form = _HOERNER_K_FORM * (d_over_l ** 3)
    d_form = cd_form * geom.cross_section_area_m2 * q

    # Interference drag (10% allowance for wing-body junction etc.)
    d_int = 0.10 * (d_fr + d_form)

    total_drag = d_fr + d_form + d_int

    # Body drag coefficient (referenced to max cross-section)
    cd_body = total_drag / (q * geom.cross_section_area_m2) if q > 0 else 0.0

    return FuselageAero(
        speed_ms=speed_ms,
        altitude_m=altitude_m,
        friction_drag_n=d_fr,
        form_drag_n=d_form,
        interference_drag_n=d_int,
        total_drag_n=total_drag,
        cd_body=cd_body,
        reynolds_number=re,
    )


# ── Structural analysis ───────────────────────────────────────────────────────


def compute_fuselage_structure(
    geom: FuselageGeometry,
    bending_moment_nm: float,
    internal_pressure_pa: float = 0.0,
    applied_axial_load_n: float = 0.0,
    elastic_modulus_pa: float = _DEFAULT_ELASTIC_MODULUS_PA,
    yield_strength_pa: float = _DEFAULT_YIELD_STRENGTH_PA,
    density_kg_m3: float = _DEFAULT_DENSITY_KG_M3,
) -> FuselageStructure:
    """Compute structural integrity of the fuselage shell.

    Analyses:
      - Bending stress (Navier formula) under applied moment
      - Hoop stress under internal pressure
      - Euler critical buckling load for the cylindrical shell as a column

    Args:
        geom:                  Fuselage geometry.
        bending_moment_nm:     Applied bending moment [N·m].
        internal_pressure_pa:  Internal gauge pressure [Pa] (0 = unpressurised).
        applied_axial_load_n:  Compressive axial load [N] (positive = compression).
        elastic_modulus_pa:    Young's modulus [Pa].
        yield_strength_pa:     Material yield strength [Pa].
        density_kg_m3:         Material density [kg/m³].

    Returns:
        :class:`FuselageStructure`.
    """
    r = geom.max_diameter_m / 2.0
    t = geom.skin_thickness_m
    L = geom.length_m

    # Cross-section second moment of area (hollow circle)
    r_i = r - t
    moi = math.pi * (r ** 4 - r_i ** 4) / 4.0
    # Bending stress (extreme fibre)
    sigma_bend = abs(bending_moment_nm) * r / moi if moi > 0 else 0.0

    # Hoop stress (thin-walled pressure vessel)
    sigma_hoop = internal_pressure_pa * r / t if t > 0 else 0.0

    # Euler critical buckling load (column, pin-pin: F_cr = π²EI/L²)
    f_buckling = _EULER_BUCKLING_COEFF * math.pi ** 2 * elastic_modulus_pa * moi / (L ** 2)

    # Safety factors
    sf_bending = yield_strength_pa / sigma_bend if sigma_bend > 1e-6 else float("inf")

    # Buckling safety: ratio of critical load to applied load
    sf_buckling = f_buckling / applied_axial_load_n if applied_axial_load_n > 1e-6 else float("inf")

    # Shell mass
    mass_kg = geom.structural_volume_m3 * density_kg_m3

    return FuselageStructure(
        bending_stress_pa=sigma_bend,
        hoop_stress_pa=sigma_hoop,
        axial_buckling_load_n=f_buckling,
        safety_factor_bending=sf_bending,
        safety_factor_buckling=sf_buckling,
        mass_kg=mass_kg,
    )


# ── Smart layer configuration ─────────────────────────────────────────────────


def configure_smart_layer(
    geom: FuselageGeometry,
    block_level: Any,  # BlockLevel or string
) -> SmartLayerConfig:
    """Return the smart-layer capability configuration for *block_level*.

    Capacities scale with fuselage geometry (wetted area, length, volume).
    Accepts either a :class:`forge_manufacturing.model.BlockLevel` enum value
    or a plain string (e.g. ``"BLOCK_2"``).

    Args:
        geom:        Fuselage geometry.
        block_level: Maturity block (BLOCK_0 through BLOCK_4).

    Returns:
        :class:`SmartLayerConfig` describing embedded system capacities.
    """
    # Normalise to string
    level_str: str = block_level.value if hasattr(block_level, "value") else str(block_level)

    # Block numeric level (0–4)
    try:
        level_idx = int(level_str.split("_")[1])
    except (IndexError, ValueError):
        level_idx = 0

    a_wet = geom.wetted_area_m2

    # BLOCK_0: bare structure only
    config = SmartLayerConfig(block_level=level_str)
    config.notes.append(f"BLOCK_0: composite structure ({a_wet:.2f} m² wetted area)")

    if level_idx >= 1:
        # BLOCK_1: SHM optical fibre network
        config.shm_fibre_count = max(1, int(a_wet * _SHM_FIBRE_DENSITY_PER_M2))
        config.notes.append(
            f"BLOCK_1: SHM — {config.shm_fibre_count} optical fibres embedded"
        )

    if level_idx >= 2:
        # BLOCK_2: embedded power distribution
        config.power_rail_capacity_w = geom.length_m * _POWER_RAIL_W_PER_M
        config.notes.append(
            f"BLOCK_2: power rails — {config.power_rail_capacity_w:.0f} W capacity"
        )

    if level_idx >= 3:
        # BLOCK_3: distributed sensor/comms nodes
        config.comms_node_count = max(1, int(a_wet * _COMMS_NODE_DENSITY_PER_M2))
        config.notes.append(
            f"BLOCK_3: {config.comms_node_count} sensor/comms nodes embedded"
        )

    if level_idx >= 4:
        # BLOCK_4: conformal energy modules
        config.energy_module_capacity_j = geom.interior_volume_m3 * 0.05 * _ENERGY_MODULE_J_PER_M3
        config.notes.append(
            f"BLOCK_4: conformal energy modules — {config.energy_module_capacity_j / 3600:.1f} Wh"
        )

    return config


# ── CG estimation ─────────────────────────────────────────────────────────────


def _estimate_cg_x(geom: FuselageGeometry) -> float:
    """Estimate longitudinal CG position [m] from nose.

    Assumes uniform mass distribution along the structural shell.
    For a body of revolution with forward-tapering nose and aft tail:
    CG ≈ 40–45% of fuselage length (use 42% for symmetric taper).
    """
    return 0.42 * geom.length_m


# ── Top-level API ─────────────────────────────────────────────────────────────


def analyse_smart_fuselage(
    geom: FuselageGeometry,
    block_level: Any = "BLOCK_0",
    speed_ms: float | None = None,
    altitude_m: float = 0.0,
    bending_moment_nm: float = 0.0,
    internal_pressure_pa: float = 0.0,
    applied_axial_load_n: float = 0.0,
    elastic_modulus_pa: float = _DEFAULT_ELASTIC_MODULUS_PA,
    yield_strength_pa: float = _DEFAULT_YIELD_STRENGTH_PA,
    density_kg_m3: float = _DEFAULT_DENSITY_KG_M3,
) -> FuselageResult:
    """Full smart fuselage analysis: aerodynamics, structure, and smart-layer config.

    Args:
        geom:                  Fuselage geometry (see :class:`FuselageGeometry`).
        block_level:           Maturity block (BLOCK_0–BLOCK_4, as string or enum).
        speed_ms:              Airspeed for drag calculation [m/s]. If ``None``,
                               aerodynamic analysis is skipped.
        altitude_m:            Altitude for ISA density [m].
        bending_moment_nm:     Applied bending moment [N·m].
        internal_pressure_pa:  Gauge internal pressure [Pa].
        applied_axial_load_n:  Compressive axial load [N].
        elastic_modulus_pa:    Young's modulus [Pa].
        yield_strength_pa:     Yield strength [Pa].
        density_kg_m3:         Shell material density [kg/m³].

    Returns:
        :class:`FuselageResult` with aero, structural, and smart-layer data.
    """
    warnings: list[str] = []

    # Aerodynamic analysis
    aero: FuselageAero | None = None
    if speed_ms is not None:
        aero = compute_fuselage_aero(geom, speed_ms=speed_ms, altitude_m=altitude_m)

    # Structural analysis
    structure = compute_fuselage_structure(
        geom,
        bending_moment_nm=bending_moment_nm,
        internal_pressure_pa=internal_pressure_pa,
        applied_axial_load_n=applied_axial_load_n,
        elastic_modulus_pa=elastic_modulus_pa,
        yield_strength_pa=yield_strength_pa,
        density_kg_m3=density_kg_m3,
    )

    if structure.safety_factor_bending < 1.5:
        warnings.append(
            f"Low bending safety factor: {structure.safety_factor_bending:.2f} "
            "(recommend >= 1.5 for primary structure)"
        )
    if structure.safety_factor_buckling < 2.0:
        warnings.append(
            f"Low buckling safety factor: {structure.safety_factor_buckling:.2f} "
            "(recommend >= 2.0 for composite shells)"
        )

    # Smart layer
    smart_layer = configure_smart_layer(geom, block_level)

    # CG
    cg_x = _estimate_cg_x(geom)

    return FuselageResult(
        geometry=geom,
        aero=aero,
        structure=structure,
        smart_layer=smart_layer,
        cg_x_m=cg_x,
        warnings=warnings,
    )
