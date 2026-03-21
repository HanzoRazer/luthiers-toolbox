"""
Top deflection calculator — ACOUSTIC-003.

Orthotropic plate deflection under concentrated load at bridge position.

Uses simply-supported beam approximation:
    a = bridge_position_fraction × length
    b = (1 - bridge_position_fraction) × length
    δ = F × a² × b² / (3 × EI × (a + b))

Creep projection: wood relaxation adds ~35% over instrument lifetime.

Gate thresholds:
    GREEN:  total < 1.5 mm  (acceptable deflection)
    YELLOW: 1.5 <= total < 3.0 mm  (monitor, may need reinforcement)
    RED:    total >= 3.0 mm  (excessive, structural risk)

NOTE: saw/deflection_adapter.py is tool deflection — wrong model.
Do not use or import it.

See: docs/BACKLOG.md ACOUSTIC-003
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional


# Creep factor: wood relaxation over instrument lifetime (~35%)
CREEP_FACTOR = 0.35


@dataclass
class PlateProperties:
    """Material and geometric properties of the top plate."""

    E_L_GPa: float  # Longitudinal Young's modulus (along grain)
    E_C_GPa: float  # Cross-grain Young's modulus (across grain)
    thickness_mm: float
    length_mm: float  # Body length (bridge to tail block direction)
    width_mm: float  # Lower bout width
    density_kg_m3: float = 400.0  # Default spruce density


@dataclass
class BraceContribution:
    """Brace stiffness contribution to composite EI."""

    brace_EI_Nm2: float  # EI from bracing_calc.py
    brace_count: int = 1


@dataclass
class DeflectionResult:
    """Result of top deflection computation with gate and notes."""

    static_deflection_mm: float
    creep_projection_mm: float  # +35% lifetime estimate
    total_projected_mm: float  # static + creep
    gate: Literal["GREEN", "YELLOW", "RED"]
    composite_EI_Nm2: float
    notes: List[str] = field(default_factory=list)


def compute_plate_EI(plate: PlateProperties) -> float:
    """
    Longitudinal bending stiffness of bare plate.

    EI = E_L × (width × thickness³) / 12

    Args:
        plate: Plate material and geometric properties.

    Returns:
        Bending stiffness EI in N·m².
    """
    # Convert units: GPa to Pa, mm to m
    E_L_Pa = plate.E_L_GPa * 1e9
    width_m = plate.width_mm / 1000.0
    thickness_m = plate.thickness_mm / 1000.0

    # Second moment of area for rectangular cross-section
    # I = width × thickness³ / 12
    I_m4 = width_m * (thickness_m ** 3) / 12.0

    # EI in N·m²
    EI_Nm2 = E_L_Pa * I_m4

    return EI_Nm2


def compute_composite_EI(
    plate: PlateProperties,
    braces: Optional[BraceContribution] = None,
) -> float:
    """
    Composite EI = plate EI + brace EI contribution.

    Args:
        plate: Plate material and geometric properties.
        braces: Optional brace stiffness contribution.

    Returns:
        Composite bending stiffness EI in N·m².
    """
    plate_EI = compute_plate_EI(plate)

    if braces is None or braces.brace_count == 0:
        return plate_EI

    # Add brace contribution (assumes parallel axis theorem already applied in brace_EI)
    total_brace_EI = braces.brace_EI_Nm2 * braces.brace_count
    composite_EI = plate_EI + total_brace_EI

    return composite_EI


def compute_top_deflection(
    load_n: float,
    plate: PlateProperties,
    braces: Optional[BraceContribution] = None,
    bridge_position_fraction: float = 0.63,
) -> DeflectionResult:
    """
    Compute top plate deflection under concentrated load at bridge.

    Uses simply-supported beam approximation:
        a = bridge_position_fraction × length
        b = (1 - bridge_position_fraction) × length
        δ = F × a² × b² / (3 × EI × (a + b))

    Creep: wood relaxation adds ~35% over lifetime.

    Args:
        load_n: Vertical load at bridge (from saddle_force_calc.py).
        plate: Plate material and geometric properties.
        braces: Optional brace stiffness contribution.
        bridge_position_fraction: Bridge position as fraction of length
            (0 = tail block, 1 = neck joint). Default 0.63 typical.

    Returns:
        DeflectionResult with static, creep, total deflection and gate.
    """
    notes: List[str] = []

    # Validate inputs
    if load_n <= 0:
        return DeflectionResult(
            static_deflection_mm=0.0,
            creep_projection_mm=0.0,
            total_projected_mm=0.0,
            gate="GREEN",
            composite_EI_Nm2=0.0,
            notes=["No load applied"],
        )

    if plate.thickness_mm <= 0 or plate.length_mm <= 0 or plate.width_mm <= 0:
        return DeflectionResult(
            static_deflection_mm=0.0,
            creep_projection_mm=0.0,
            total_projected_mm=0.0,
            gate="RED",
            composite_EI_Nm2=0.0,
            notes=["Invalid plate geometry"],
        )

    if plate.E_L_GPa <= 0:
        return DeflectionResult(
            static_deflection_mm=0.0,
            creep_projection_mm=0.0,
            total_projected_mm=0.0,
            gate="RED",
            composite_EI_Nm2=0.0,
            notes=["Invalid material properties (E_L must be positive)"],
        )

    # Compute composite EI
    composite_EI = compute_composite_EI(plate, braces)

    if composite_EI <= 0:
        return DeflectionResult(
            static_deflection_mm=0.0,
            creep_projection_mm=0.0,
            total_projected_mm=0.0,
            gate="RED",
            composite_EI_Nm2=0.0,
            notes=["Composite EI is zero or negative"],
        )

    # Convert length to meters
    length_m = plate.length_mm / 1000.0

    # Bridge position distances
    # a = distance from neck joint to bridge
    # b = distance from bridge to tail block
    a = bridge_position_fraction * length_m
    b = (1.0 - bridge_position_fraction) * length_m

    # Simply-supported beam deflection under point load
    # δ = F × a² × b² / (3 × EI × L)
    # where L = a + b
    L = a + b
    if L <= 0:
        return DeflectionResult(
            static_deflection_mm=0.0,
            creep_projection_mm=0.0,
            total_projected_mm=0.0,
            gate="RED",
            composite_EI_Nm2=composite_EI,
            notes=["Invalid beam length"],
        )

    static_deflection_m = (load_n * (a ** 2) * (b ** 2)) / (3.0 * composite_EI * L)
    static_deflection_mm = static_deflection_m * 1000.0

    # Creep projection (+35% over lifetime)
    creep_projection_mm = static_deflection_mm * CREEP_FACTOR
    total_projected_mm = static_deflection_mm + creep_projection_mm

    # Gate determination
    if total_projected_mm < 1.5:
        gate: Literal["GREEN", "YELLOW", "RED"] = "GREEN"
        notes.append("Deflection within acceptable range.")
    elif total_projected_mm < 3.0:
        gate = "YELLOW"
        notes.append(
            "Moderate deflection — monitor over time. "
            "Consider stiffer bracing or thicker top."
        )
    else:
        gate = "RED"
        notes.append(
            "Excessive deflection (>3mm projected). "
            "Structural risk — reinforce bracing or increase top thickness."
        )

    # Add context notes
    if braces is not None and braces.brace_count > 0:
        notes.append(
            f"Composite EI includes {braces.brace_count} brace(s) "
            f"contributing {braces.brace_EI_Nm2:.2f} N·m² each."
        )
    else:
        notes.append("Bare plate EI (no bracing contribution).")

    return DeflectionResult(
        static_deflection_mm=round(static_deflection_mm, 4),
        creep_projection_mm=round(creep_projection_mm, 4),
        total_projected_mm=round(total_projected_mm, 4),
        gate=gate,
        composite_EI_Nm2=round(composite_EI, 4),
        notes=notes,
    )


# =============================================================================
# WOOD SPECIES DEFAULTS
# =============================================================================

# Typical values for common tonewoods (from wood database)
SPRUCE_SITKA = PlateProperties(
    E_L_GPa=11.0,  # Sitka spruce longitudinal
    E_C_GPa=0.8,  # Sitka spruce cross-grain
    thickness_mm=2.8,  # Typical top thickness
    length_mm=500.0,  # Typical dreadnought body length
    width_mm=400.0,  # Typical lower bout width
    density_kg_m3=400.0,
)

SPRUCE_ENGLEMANN = PlateProperties(
    E_L_GPa=9.5,  # Engelmann slightly softer
    E_C_GPa=0.7,
    thickness_mm=2.8,
    length_mm=500.0,
    width_mm=400.0,
    density_kg_m3=360.0,
)

CEDAR_WESTERN_RED = PlateProperties(
    E_L_GPa=7.5,  # Cedar softer than spruce
    E_C_GPa=0.5,
    thickness_mm=3.0,  # Often slightly thicker for cedar
    length_mm=500.0,
    width_mm=400.0,
    density_kg_m3=350.0,
)
