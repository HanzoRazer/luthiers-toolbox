"""
spiral_acoustic_model.py

Simulation-ready acoustic model for logarithmic spiral soundholes,
including effective length, Helmholtz frequency, port impedance, and
first-pass Q/loss estimates.

Design intent:
    - Compare spiral-only ports to conventional tornavoz behavior.
    - Evaluate multi-port spiral systems for Carlos Jumbo-style designs.
    - Provide a lightweight numerical layer above the existing geometry engine.

Limitations:
    This is a reduced-order engineering model. It is not a full FEM/BEM solver.
    Constants for slot end correction and damping must be calibrated against
    measured bodies.

Author: Generated from Carlos Jumbo / Spiral Soundhole acoustic spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, pi, sqrt
from typing import Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AIR_DENSITY_KG_M3 = 1.21
SPEED_OF_SOUND_M_S = 343.0
AIR_VISCOSITY_PA_S = 1.81e-5


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpiralPortSpec:
    """Geometry and acoustic parameters for one constant-width logarithmic spiral slot.

    Units:
        center_x_mm, center_y_mm: mm
        start_radius_mm: mm
        growth_rate_k: dimensionless, per radian
        turns: number of full rotations
        slot_width_mm: mm
        top_thickness_mm: mm
        acoustic_loss_factor: dimensionless calibration factor, default 1.0
    """

    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
    start_radius_mm: float = 10.0
    growth_rate_k: float = 0.18
    turns: float = 1.1
    slot_width_mm: float = 14.0
    rotation_deg: float = 0.0
    top_thickness_mm: float = 2.5
    label: str = ""

    # Calibrations
    slot_end_correction_alpha: float = 0.85
    acoustic_loss_factor: float = 1.0

    def theta_max(self) -> float:
        return 2.0 * pi * self.turns

    def outer_radius_mm(self) -> float:
        return self.start_radius_mm * exp(self.growth_rate_k * self.theta_max())


@dataclass(frozen=True)
class TornavozSpec:
    """Simple cylindrical or flared tornavoz equivalent.

    Units:
        area_m2: acoustic cross-sectional area
        tube_length_mm: physical tube depth
        end_correction_m: additional effective length correction
        loss_factor: empirical multiplier on damping
    """

    area_m2: float
    tube_length_mm: float
    end_correction_m: float = 0.0
    loss_factor: float = 0.35  # lower than spiral by default


@dataclass(frozen=True)
class BodyAcousticSpec:
    """Body/cavity acoustic properties."""

    volume_liters: float = 21.0
    air_density_kg_m3: float = AIR_DENSITY_KG_M3
    speed_of_sound_m_s: float = SPEED_OF_SOUND_M_S
    air_viscosity_pa_s: float = AIR_VISCOSITY_PA_S

    @property
    def volume_m3(self) -> float:
        return self.volume_liters / 1000.0


@dataclass
class PortAcousticResult:
    """Computed acoustic properties for one port."""

    label: str
    area_m2: float
    perimeter_m: float
    path_length_m: float
    effective_length_m: float
    acoustic_mass: float
    estimated_loss_r: float
    estimated_q_at_fh: Optional[float] = None


@dataclass
class MultiPortResult:
    """Computed acoustic properties for a set of parallel ports."""

    total_area_m2: float
    equivalent_effective_length_m: float
    helmholtz_frequency_hz: float
    equivalent_acoustic_mass: float
    total_loss_r: float
    estimated_q: float
    port_results: List[PortAcousticResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Spiral geometry functions
# ---------------------------------------------------------------------------

def spiral_path_length_m(spec: SpiralPortSpec) -> float:
    """Closed-form path length of r(theta) = r0 exp(k theta).

    For logarithmic spiral:
        ds = sqrt(r^2 + (dr/dtheta)^2) dtheta
           = r sqrt(1+k^2) dtheta

    Integral:
        L = sqrt(1+k^2) * (r1 - r0) / k, for k != 0

    If k approaches 0, fallback to circular arc approximation.
    """

    r0 = spec.start_radius_mm / 1000.0
    k = spec.growth_rate_k
    theta = spec.theta_max()

    if abs(k) < 1e-9:
        return r0 * theta

    r1 = r0 * exp(k * theta)
    return sqrt(1.0 + k * k) * (r1 - r0) / k


def spiral_area_m2(spec: SpiralPortSpec) -> float:
    """Approximate open slot area for a constant-width spiral."""

    return (spec.slot_width_mm / 1000.0) * spiral_path_length_m(spec)


def spiral_perimeter_m(spec: SpiralPortSpec) -> float:
    """Approximate slot perimeter.

    For a long slot:
        P ≈ 2 L_path + 2 w

    The +2w term matters only for short slots.
    """

    w = spec.slot_width_mm / 1000.0
    return 2.0 * spiral_path_length_m(spec) + 2.0 * w


def perimeter_area_ratio_per_m(spec: SpiralPortSpec) -> float:
    """P/A ratio in inverse meters."""

    area = spiral_area_m2(spec)
    if area <= 0:
        raise ValueError("Spiral area must be positive.")
    return spiral_perimeter_m(spec) / area


# ---------------------------------------------------------------------------
# Effective length and impedance
# ---------------------------------------------------------------------------

def effective_length_spiral_m(spec: SpiralPortSpec) -> float:
    """First-pass effective length for a spiral slot.

    Model:
        L_eff = top_thickness + alpha * slot_width + distributed_path_term

    The slot end correction is not the same as a round hole. The default
    alpha=0.85 is intentionally conservative and should be calibrated.

    The distributed_path_term captures the tornavoz-like inertive effect of
    a long curved slot. The coefficient below is deliberately small because
    the entire path does not behave as a coherent 1D tube.

    Calibration target:
        Carlos Jumbo main spirals should land in roughly 60-95 mm equivalent
        effective length total, depending on total area and body volume.
    """

    t = spec.top_thickness_mm / 1000.0
    w = spec.slot_width_mm / 1000.0
    path = spiral_path_length_m(spec)

    # Empirical reduced contribution of distributed path to acoustic inertance.
    # This should be fitted from measurement. 0.08 means 8% of geometric path
    # contributes as coherent effective neck length.
    distributed_path_factor = 0.08

    return t + spec.slot_end_correction_alpha * w + distributed_path_factor * path


def acoustic_mass(air_density_kg_m3: float, effective_length_m: float, area_m2: float) -> float:
    """Acoustic mass / inertance M_a = rho * L_eff / A."""

    if area_m2 <= 0:
        raise ValueError("Area must be positive.")
    return air_density_kg_m3 * effective_length_m / area_m2


def estimate_loss_resistance_spiral(
    spec: SpiralPortSpec,
    body: BodyAcousticSpec,
    frequency_hz: float,
) -> float:
    """Estimate lumped acoustic loss resistance for a spiral.

    This is intentionally a calibration-friendly engineering estimate:

        R_loss = loss_factor * (viscous_proxy + radiation_proxy + curvature_proxy)

    The absolute value should be calibrated, but relative comparisons between
    spiral geometries are useful.

    Higher perimeter, narrower slot, and tighter curvature increase loss.
    """

    area = spiral_area_m2(spec)
    perimeter = spiral_perimeter_m(spec)
    path = spiral_path_length_m(spec)
    w = spec.slot_width_mm / 1000.0
    r_inner = spec.start_radius_mm / 1000.0

    if area <= 0 or w <= 0:
        raise ValueError("Invalid spiral geometry.")

    omega = 2.0 * pi * frequency_hz

    viscous_proxy = body.air_viscosity_pa_s * perimeter / max(area * area, 1e-18)
    radiation_proxy = body.air_density_kg_m3 * body.speed_of_sound_m_s * (area ** 0.5)
    curvature_proxy = body.air_density_kg_m3 * omega * path * (1.0 / max(r_inner, 1e-6)) ** 0.5 * 1e-4

    return spec.acoustic_loss_factor * (viscous_proxy + radiation_proxy + curvature_proxy)


def port_impedance(
    frequency_hz: float,
    acoustic_mass_value: float,
    loss_resistance: float,
) -> complex:
    """Complex acoustic impedance Z = R + j omega M."""

    omega = 2.0 * pi * frequency_hz
    return complex(loss_resistance, omega * acoustic_mass_value)


# ---------------------------------------------------------------------------
# Helmholtz and multi-port calculations
# ---------------------------------------------------------------------------

def helmholtz_frequency_hz(
    body: BodyAcousticSpec,
    total_area_m2: float,
    effective_length_m: float,
) -> float:
    """Helmholtz frequency f = c/(2pi) sqrt(A/(V L_eff))."""

    if body.volume_m3 <= 0:
        raise ValueError("Body volume must be positive.")
    if total_area_m2 <= 0:
        raise ValueError("Port area must be positive.")
    if effective_length_m <= 0:
        raise ValueError("Effective length must be positive.")

    return (
        body.speed_of_sound_m_s
        / (2.0 * pi)
        * sqrt(total_area_m2 / (body.volume_m3 * effective_length_m))
    )


def required_effective_length_m(
    body: BodyAcousticSpec,
    total_area_m2: float,
    target_f_hz: float,
) -> float:
    """Invert Helmholtz equation to solve required L_eff."""

    if target_f_hz <= 0:
        raise ValueError("Target frequency must be positive.")

    factor = (2.0 * pi * target_f_hz / body.speed_of_sound_m_s) ** 2
    return total_area_m2 / (body.volume_m3 * factor)


def equivalent_parallel_effective_length(port_results: Sequence[PortAcousticResult]) -> float:
    """Equivalent L_eff for parallel acoustic ports.

    For parallel ports, acoustic inertance equivalent follows:
        M_eq = rho / sum(A_i / L_i)

    Since M_eq = rho L_eq / A_total:
        L_eq = A_total / sum(A_i / L_i)
    """

    total_area = sum(p.area_m2 for p in port_results)
    denom = sum(p.area_m2 / p.effective_length_m for p in port_results)

    if total_area <= 0 or denom <= 0:
        raise ValueError("Invalid port set.")

    return total_area / denom


def compute_spiral_port(
    spec: SpiralPortSpec,
    body: BodyAcousticSpec,
    frequency_for_loss_hz: float = 100.0,
) -> PortAcousticResult:
    """Compute acoustic properties for one spiral port."""

    area = spiral_area_m2(spec)
    perimeter = spiral_perimeter_m(spec)
    path = spiral_path_length_m(spec)
    leff = effective_length_spiral_m(spec)
    mass = acoustic_mass(body.air_density_kg_m3, leff, area)
    loss = estimate_loss_resistance_spiral(spec, body, frequency_for_loss_hz)

    q = (2.0 * pi * frequency_for_loss_hz * mass / loss) if loss > 0 else None

    return PortAcousticResult(
        label=spec.label or "spiral",
        area_m2=area,
        perimeter_m=perimeter,
        path_length_m=path,
        effective_length_m=leff,
        acoustic_mass=mass,
        estimated_loss_r=loss,
        estimated_q_at_fh=q,
    )


def compute_tornavoz_port(
    spec: TornavozSpec,
    body: BodyAcousticSpec,
    frequency_for_loss_hz: float = 100.0,
    label: str = "tornavoz",
) -> PortAcousticResult:
    """Compute acoustic properties for a conventional tornavoz reference."""

    leff = spec.tube_length_mm / 1000.0 + spec.end_correction_m
    mass = acoustic_mass(body.air_density_kg_m3, leff, spec.area_m2)

    # Lower loss proxy than spiral; calibrated by loss_factor.
    loss = spec.loss_factor * body.air_density_kg_m3 * body.speed_of_sound_m_s * sqrt(spec.area_m2)
    q = (2.0 * pi * frequency_for_loss_hz * mass / loss) if loss > 0 else None

    return PortAcousticResult(
        label=label,
        area_m2=spec.area_m2,
        perimeter_m=0.0,
        path_length_m=spec.tube_length_mm / 1000.0,
        effective_length_m=leff,
        acoustic_mass=mass,
        estimated_loss_r=loss,
        estimated_q_at_fh=q,
    )


def compute_multiport_system(
    body: BodyAcousticSpec,
    port_results: Sequence[PortAcousticResult],
) -> MultiPortResult:
    """Compute equivalent multi-port Helmholtz behavior."""

    if not port_results:
        raise ValueError("At least one port is required.")

    total_area = sum(p.area_m2 for p in port_results)
    leq = equivalent_parallel_effective_length(port_results)
    f_h = helmholtz_frequency_hz(body, total_area, leq)
    mass_eq = acoustic_mass(body.air_density_kg_m3, leq, total_area)

    # Parallel losses: conductances add. For a first-pass lumped proxy, use
    # area-weighted loss resistance.
    total_loss = sum((p.area_m2 / total_area) * p.estimated_loss_r for p in port_results)
    q = (2.0 * pi * f_h * mass_eq / total_loss) if total_loss > 0 else float("inf")

    return MultiPortResult(
        total_area_m2=total_area,
        equivalent_effective_length_m=leq,
        helmholtz_frequency_hz=f_h,
        equivalent_acoustic_mass=mass_eq,
        total_loss_r=total_loss,
        estimated_q=q,
        port_results=list(port_results),
    )


# ---------------------------------------------------------------------------
# Utility/reporting functions
# ---------------------------------------------------------------------------

def cm2(m2: float) -> float:
    return m2 * 10_000.0


def mm(m: float) -> float:
    return m * 1000.0


def summarize_result(result: MultiPortResult) -> str:
    """Human-readable engineering summary."""

    lines = []
    lines.append("Multi-Port Acoustic Summary")
    lines.append("-" * 32)
    lines.append(f"Total area: {cm2(result.total_area_m2):.2f} cm^2")
    lines.append(f"Equivalent L_eff: {mm(result.equivalent_effective_length_m):.1f} mm")
    lines.append(f"Helmholtz frequency: {result.helmholtz_frequency_hz:.1f} Hz")
    lines.append(f"Estimated Q: {result.estimated_q:.2f}")
    lines.append("")
    lines.append("Ports:")
    for p in result.port_results:
        lines.append(
            f"  - {p.label}: area={cm2(p.area_m2):.2f} cm^2, "
            f"L_eff={mm(p.effective_length_m):.1f} mm, "
            f"path={mm(p.path_length_m):.1f} mm, "
            f"Q@loss-freq={p.estimated_q_at_fh:.2f}"
        )
    return "\n".join(lines)


def compare_to_target(
    result: MultiPortResult,
    f_min_hz: float = 90.0,
    f_max_hz: float = 105.0,
    q_min: float = 6.0,
    q_max: float = 10.0,
) -> dict:
    """Return pass/fail style checks against Carlos target ranges."""

    return {
        "f_H_hz": result.helmholtz_frequency_hz,
        "Q": result.estimated_q,
        "frequency_in_target": f_min_hz <= result.helmholtz_frequency_hz <= f_max_hz,
        "q_in_target": q_min <= result.estimated_q <= q_max,
        "needs_more_effective_length": result.helmholtz_frequency_hz > f_max_hz,
        "likely_overdamped": result.estimated_q < q_min,
        "likely_too_peaky": result.estimated_q > q_max,
    }


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

def demo_carlos_dual_plus_third() -> MultiPortResult:
    """Example Carlos-style dual main spirals plus small third treble port."""

    body = BodyAcousticSpec(volume_liters=21.0)

    lower = SpiralPortSpec(
        start_radius_mm=10.0,
        growth_rate_k=0.18,
        turns=1.15,
        slot_width_mm=14.0,
        top_thickness_mm=2.6,
        label="lower_treble_main",
    )

    upper = SpiralPortSpec(
        start_radius_mm=9.0,
        growth_rate_k=0.17,
        turns=1.05,
        slot_width_mm=14.0,
        top_thickness_mm=2.6,
        label="upper_bass_main",
    )

    third = SpiralPortSpec(
        start_radius_mm=6.5,
        growth_rate_k=0.15,
        turns=0.65,
        slot_width_mm=10.0,
        top_thickness_mm=2.5,
        label="small_treble_trim",
        acoustic_loss_factor=0.85,
    )

    ports = [
        compute_spiral_port(lower, body),
        compute_spiral_port(upper, body),
        compute_spiral_port(third, body),
    ]

    return compute_multiport_system(body, ports)


if __name__ == "__main__":
    result = demo_carlos_dual_plus_third()
    print(summarize_result(result))
    print()
    print(compare_to_target(result))
