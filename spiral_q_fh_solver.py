"""
spiral_q_fh_solver.py

Numerical solver for predicting and fitting Helmholtz frequency (f_H)
and quality factor (Q) from logarithmic spiral soundhole parameters.

Purpose
-------
This module extends the reduced-order spiral acoustic model into a
calibration/optimization solver.

It supports:
    1. Forward prediction of f_H and Q from spiral parameters.
    2. Multi-port systems: two main spirals + optional third trim spiral.
    3. Inverse fitting of spiral parameters to target f_H and Q.
    4. Tornavoz-equivalent comparison by solving required L_eff.
    5. Sensitivity sweeps for slot width, turns, growth rate, and third-port area.

Important limits
----------------
This is a lumped-parameter engineering model, not FEM/BEM. It is intended
to guide prototypes and lab testing. Loss constants must be calibrated from
measured bodies.

Core equations
--------------
    f_H = c/(2π) * sqrt(A_total / (V * L_eff_eq))

    M_a = ρ0 * L_eff / A

    Z = R_loss + jωM_a

    Q ≈ ω_H * M_eq / R_eq

For logarithmic spiral:
    r(θ) = r0 * exp(kθ)

    L_path = sqrt(1+k²) * (r1-r0)/k

    A ≈ slot_width * L_path
    P ≈ 2L_path + 2slot_width
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import exp, pi, sqrt, isfinite
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    raise ImportError("This solver requires numpy.") from exc

try:
    from scipy.optimize import differential_evolution, minimize
except Exception:  # pragma: no cover
    differential_evolution = None
    minimize = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AIR_DENSITY_KG_M3 = 1.21
SPEED_OF_SOUND_M_S = 343.0
AIR_VISCOSITY_PA_S = 1.81e-5


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpiralSpec:
    """One logarithmic spiral slot.

    Units:
        start_radius_mm: mm
        growth_rate_k: dimensionless per radian
        turns: number of full turns
        slot_width_mm: mm
        top_thickness_mm: mm
    """

    start_radius_mm: float = 10.0
    growth_rate_k: float = 0.18
    turns: float = 1.10
    slot_width_mm: float = 14.0
    top_thickness_mm: float = 2.6
    label: str = "spiral"

    # acoustic calibration knobs
    slot_end_correction_alpha: float = 0.85
    distributed_path_factor: float = 0.08
    loss_scale: float = 1.0


@dataclass(frozen=True)
class BodySpec:
    """Cavity and air properties."""

    volume_liters: float = 21.0
    air_density_kg_m3: float = AIR_DENSITY_KG_M3
    speed_of_sound_m_s: float = SPEED_OF_SOUND_M_S
    air_viscosity_pa_s: float = AIR_VISCOSITY_PA_S

    @property
    def volume_m3(self) -> float:
        return self.volume_liters / 1000.0


@dataclass(frozen=True)
class PortResult:
    label: str
    area_m2: float
    perimeter_m: float
    path_length_m: float
    effective_length_m: float
    acoustic_mass: float
    loss_resistance: float
    q_local_at_fh: float


@dataclass(frozen=True)
class SystemResult:
    ports: Tuple[PortResult, ...]
    total_area_m2: float
    equivalent_effective_length_m: float
    helmholtz_frequency_hz: float
    equivalent_acoustic_mass: float
    equivalent_loss_resistance: float
    q: float
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class TargetSpec:
    target_f_hz: float = 98.0
    target_q: float = 8.0
    weight_f: float = 1.0
    weight_q: float = 0.5
    weight_area: float = 0.05
    target_total_area_cm2: Optional[float] = None


@dataclass(frozen=True)
class SolverBounds:
    """Bounds for optimizing one or more spirals.

    The vector per optimized spiral is:
        [start_radius_mm, growth_rate_k, turns, slot_width_mm]
    """

    start_radius_mm: Tuple[float, float] = (6.0, 18.0)
    growth_rate_k: Tuple[float, float] = (0.08, 0.32)
    turns: Tuple[float, float] = (0.55, 1.80)
    slot_width_mm: Tuple[float, float] = (8.0, 18.0)

    def per_spiral_bounds(self) -> List[Tuple[float, float]]:
        return [
            self.start_radius_mm,
            self.growth_rate_k,
            self.turns,
            self.slot_width_mm,
        ]


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def theta_max(spec: SpiralSpec) -> float:
    return 2.0 * pi * spec.turns


def outer_radius_mm(spec: SpiralSpec) -> float:
    return spec.start_radius_mm * exp(spec.growth_rate_k * theta_max(spec))


def spiral_path_length_m(spec: SpiralSpec) -> float:
    r0 = spec.start_radius_mm / 1000.0
    k = spec.growth_rate_k
    th = theta_max(spec)
    if abs(k) < 1e-12:
        return r0 * th
    r1 = r0 * exp(k * th)
    return sqrt(1.0 + k * k) * (r1 - r0) / k


def spiral_area_m2(spec: SpiralSpec) -> float:
    return (spec.slot_width_mm / 1000.0) * spiral_path_length_m(spec)


def spiral_perimeter_m(spec: SpiralSpec) -> float:
    w = spec.slot_width_mm / 1000.0
    return 2.0 * spiral_path_length_m(spec) + 2.0 * w


def validate_spiral(spec: SpiralSpec) -> List[str]:
    warnings = []
    if spec.slot_width_mm < 8:
        warnings.append(f"{spec.label}: slot width below 8 mm may be fragile/hard to machine.")
    if spec.slot_width_mm > 22:
        warnings.append(f"{spec.label}: slot width high; lower perimeter-to-area acoustic benefit.")
    if outer_radius_mm(spec) > 90:
        warnings.append(f"{spec.label}: outer radius >90 mm; verify fit and brace keepout.")
    if spec.start_radius_mm < 6:
        warnings.append(f"{spec.label}: inner radius <6 mm; stress concentration risk.")
    if spec.turns > 1.6:
        warnings.append(f"{spec.label}: many turns; higher damping and finishing risk.")
    return warnings


# ---------------------------------------------------------------------------
# Acoustic model
# ---------------------------------------------------------------------------

def effective_length_m(spec: SpiralSpec) -> float:
    """Spiral effective acoustic length.

    L_eff = top_thickness + alpha*w + beta*L_path

    alpha*w captures slot end correction.
    beta*L_path captures distributed tornavoz-like inertance.

    beta should be calibrated; default 0.08 is deliberately conservative.
    """

    t = spec.top_thickness_mm / 1000.0
    w = spec.slot_width_mm / 1000.0
    return t + spec.slot_end_correction_alpha * w + spec.distributed_path_factor * spiral_path_length_m(spec)


def acoustic_mass(body: BodySpec, leff_m: float, area_m2: float) -> float:
    if area_m2 <= 0:
        raise ValueError("area_m2 must be positive")
    return body.air_density_kg_m3 * leff_m / area_m2


def loss_resistance(body: BodySpec, spec: SpiralSpec, frequency_hz: float) -> float:
    """Calibration-friendly lumped loss estimate.

    Components:
        viscous proxy: rises with perimeter and small area
        radiation proxy: rises with sqrt(area)
        curvature proxy: rises for tight inner curls and long path

    Absolute units are approximate; Q calibration should fit loss_scale and
    distributed_path_factor against measured f_H and bandwidth.
    """

    area = spiral_area_m2(spec)
    perimeter = spiral_perimeter_m(spec)
    path = spiral_path_length_m(spec)
    r_inner = max(spec.start_radius_mm / 1000.0, 1e-6)
    omega = 2.0 * pi * frequency_hz

    viscous = body.air_viscosity_pa_s * perimeter / max(area * area, 1e-18)
    radiation = 0.08 * body.air_density_kg_m3 * body.speed_of_sound_m_s * sqrt(area)
    curvature = 1e-4 * body.air_density_kg_m3 * omega * path / sqrt(r_inner)

    return spec.loss_scale * (viscous + radiation + curvature)


def port_result(body: BodySpec, spec: SpiralSpec, frequency_for_loss_hz: float) -> PortResult:
    area = spiral_area_m2(spec)
    perimeter = spiral_perimeter_m(spec)
    path = spiral_path_length_m(spec)
    leff = effective_length_m(spec)
    ma = acoustic_mass(body, leff, area)
    r = loss_resistance(body, spec, frequency_for_loss_hz)
    q_local = (2.0 * pi * frequency_for_loss_hz * ma / r) if r > 0 else float("inf")
    return PortResult(
        label=spec.label,
        area_m2=area,
        perimeter_m=perimeter,
        path_length_m=path,
        effective_length_m=leff,
        acoustic_mass=ma,
        loss_resistance=r,
        q_local_at_fh=q_local,
    )


def equivalent_leff_parallel(ports: Sequence[PortResult]) -> float:
    total_area = sum(p.area_m2 for p in ports)
    denom = sum(p.area_m2 / p.effective_length_m for p in ports)
    if total_area <= 0 or denom <= 0:
        raise ValueError("Invalid port set")
    return total_area / denom


def helmholtz_frequency(body: BodySpec, area_m2: float, leff_m: float) -> float:
    if area_m2 <= 0:
        raise ValueError("area_m2 must be positive")
    if leff_m <= 0:
        raise ValueError("leff_m must be positive")
    return body.speed_of_sound_m_s / (2.0 * pi) * sqrt(area_m2 / (body.volume_m3 * leff_m))


def required_leff_for_target(body: BodySpec, area_m2: float, target_f_hz: float) -> float:
    factor = (2.0 * pi * target_f_hz / body.speed_of_sound_m_s) ** 2
    return area_m2 / (body.volume_m3 * factor)


def predict_system(body: BodySpec, specs: Sequence[SpiralSpec]) -> SystemResult:
    """Predict f_H and Q for a multi-spiral system."""

    warnings: List[str] = []
    for s in specs:
        warnings.extend(validate_spiral(s))

    # First pass loss evaluated at nominal 100 Hz. Then recompute at predicted f_H.
    ports_100 = tuple(port_result(body, s, 100.0) for s in specs)
    total_area = sum(p.area_m2 for p in ports_100)
    leq = equivalent_leff_parallel(ports_100)
    fh = helmholtz_frequency(body, total_area, leq)

    ports = tuple(port_result(body, s, fh) for s in specs)
    total_area = sum(p.area_m2 for p in ports)
    leq = equivalent_leff_parallel(ports)
    fh = helmholtz_frequency(body, total_area, leq)
    m_eq = acoustic_mass(body, leq, total_area)

    # Area-weighted equivalent loss as a stable first-order approximation.
    r_eq = sum((p.area_m2 / total_area) * p.loss_resistance for p in ports)
    q = (2.0 * pi * fh * m_eq / r_eq) if r_eq > 0 else float("inf")

    if q < 5:
        warnings.append("System likely overdamped: Q < 5.")
    if q > 12:
        warnings.append("System may be too peaky/boomy: Q > 12.")
    if not (90 <= fh <= 105):
        warnings.append("f_H outside Carlos first-pass target window 90-105 Hz.")

    return SystemResult(
        ports=ports,
        total_area_m2=total_area,
        equivalent_effective_length_m=leq,
        helmholtz_frequency_hz=fh,
        equivalent_acoustic_mass=m_eq,
        equivalent_loss_resistance=r_eq,
        q=q,
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Objective and optimization
# ---------------------------------------------------------------------------

def _vector_to_specs(
    x: Sequence[float],
    base_specs: Sequence[SpiralSpec],
    optimize_mask: Sequence[bool],
) -> List[SpiralSpec]:
    """Apply optimized vector to selected spirals.

    For every True in optimize_mask, consume four values:
        start_radius_mm, growth_rate_k, turns, slot_width_mm
    """

    specs: List[SpiralSpec] = []
    idx = 0
    for base, opt in zip(base_specs, optimize_mask):
        if opt:
            specs.append(
                replace(
                    base,
                    start_radius_mm=float(x[idx]),
                    growth_rate_k=float(x[idx + 1]),
                    turns=float(x[idx + 2]),
                    slot_width_mm=float(x[idx + 3]),
                )
            )
            idx += 4
        else:
            specs.append(base)
    return specs


def _objective(
    x: Sequence[float],
    body: BodySpec,
    base_specs: Sequence[SpiralSpec],
    optimize_mask: Sequence[bool],
    target: TargetSpec,
) -> float:
    specs = _vector_to_specs(x, base_specs, optimize_mask)
    try:
        result = predict_system(body, specs)
    except Exception:
        return 1e9

    f_err = (result.helmholtz_frequency_hz - target.target_f_hz) / max(target.target_f_hz, 1e-9)
    q_err = (result.q - target.target_q) / max(target.target_q, 1e-9)

    cost = target.weight_f * f_err * f_err + target.weight_q * q_err * q_err

    if target.target_total_area_cm2 is not None:
        target_area_m2 = target.target_total_area_cm2 / 10_000.0
        area_err = (result.total_area_m2 - target_area_m2) / max(target_area_m2, 1e-9)
        cost += target.weight_area * area_err * area_err

    # Soft penalties for fragile/overlarge geometry.
    for s in specs:
        if s.slot_width_mm < 10:
            cost += 0.01 * (10 - s.slot_width_mm) ** 2
        if outer_radius_mm(s) > 95:
            cost += 0.001 * (outer_radius_mm(s) - 95) ** 2
        if s.turns > 1.6:
            cost += 0.02 * (s.turns - 1.6) ** 2

    if not isfinite(cost):
        return 1e9
    return float(cost)


def solve_spiral_parameters(
    body: BodySpec,
    base_specs: Sequence[SpiralSpec],
    target: TargetSpec,
    optimize_mask: Optional[Sequence[bool]] = None,
    bounds: SolverBounds = SolverBounds(),
    global_search: bool = True,
    maxiter: int = 120,
    seed: int = 7,
) -> Tuple[List[SpiralSpec], SystemResult, Dict[str, float]]:
    """Fit spiral parameters to target f_H and Q.

    Parameters
    ----------
    body:
        Cavity/air spec.
    base_specs:
        Initial spiral specs. Any non-optimized spec is held fixed.
    target:
        Target f_H and Q.
    optimize_mask:
        Sequence of bools. True means optimize that spiral. If None, optimize all.
    bounds:
        Parameter bounds per optimized spiral.
    global_search:
        If True, use differential_evolution followed by local minimize.
        If False, use local minimize from the base spec vector.
    """

    if minimize is None:
        raise ImportError("scipy is required for solve_spiral_parameters().")

    if optimize_mask is None:
        optimize_mask = [True] * len(base_specs)
    if len(optimize_mask) != len(base_specs):
        raise ValueError("optimize_mask length must match base_specs length")

    opt_bounds: List[Tuple[float, float]] = []
    x0: List[float] = []
    for spec, opt in zip(base_specs, optimize_mask):
        if opt:
            opt_bounds.extend(bounds.per_spiral_bounds())
            x0.extend([spec.start_radius_mm, spec.growth_rate_k, spec.turns, spec.slot_width_mm])

    if not x0:
        result = predict_system(body, base_specs)
        return list(base_specs), result, {"objective": 0.0}

    objective_args = (body, base_specs, optimize_mask, target)

    if global_search:
        if differential_evolution is None:
            raise ImportError("scipy differential_evolution unavailable.")
        de = differential_evolution(
            _objective,
            bounds=opt_bounds,
            args=objective_args,
            seed=seed,
            maxiter=maxiter,
            polish=False,
            updating="immediate",
        )
        start = de.x
    else:
        start = np.array(x0, dtype=float)

    local = minimize(
        _objective,
        x0=start,
        args=objective_args,
        method="Nelder-Mead",
        options={"maxiter": maxiter * 50, "xatol": 1e-5, "fatol": 1e-8},
    )

    fitted = _vector_to_specs(local.x, base_specs, optimize_mask)
    prediction = predict_system(body, fitted)
    info = {
        "objective": float(local.fun),
        "success": float(bool(local.success)),
        "nfev": float(local.nfev),
    }
    return fitted, prediction, info


# ---------------------------------------------------------------------------
# Sensitivity sweeps
# ---------------------------------------------------------------------------

def sweep_parameter(
    body: BodySpec,
    specs: Sequence[SpiralSpec],
    port_index: int,
    parameter: str,
    values: Iterable[float],
) -> List[Dict[str, float]]:
    """Sweep one parameter on one port and return f_H/Q results."""

    rows: List[Dict[str, float]] = []
    for v in values:
        updated = list(specs)
        updated[port_index] = replace(updated[port_index], **{parameter: float(v)})
        result = predict_system(body, updated)
        rows.append(
            {
                "parameter": parameter,
                "value": float(v),
                "f_H_hz": result.helmholtz_frequency_hz,
                "Q": result.q,
                "total_area_cm2": result.total_area_m2 * 10_000.0,
                "L_eff_eq_mm": result.equivalent_effective_length_m * 1000.0,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def cm2(m2: float) -> float:
    return m2 * 10_000.0


def mm(m: float) -> float:
    return m * 1000.0


def format_system_result(result: SystemResult) -> str:
    lines = [
        "Spiral Acoustic Solver Result",
        "-" * 36,
        f"f_H: {result.helmholtz_frequency_hz:.2f} Hz",
        f"Q: {result.q:.2f}",
        f"Total area: {cm2(result.total_area_m2):.2f} cm^2",
        f"Equivalent L_eff: {mm(result.equivalent_effective_length_m):.2f} mm",
        f"Equivalent acoustic mass: {result.equivalent_acoustic_mass:.6g}",
        f"Equivalent loss R: {result.equivalent_loss_resistance:.6g}",
        "",
        "Ports:",
    ]
    for p in result.ports:
        lines.append(
            f"  {p.label}: area={cm2(p.area_m2):.2f} cm^2, "
            f"path={mm(p.path_length_m):.1f} mm, "
            f"L_eff={mm(p.effective_length_m):.1f} mm, "
            f"Q_local={p.q_local_at_fh:.2f}"
        )
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in result.warnings:
            lines.append(f"  - {w}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def carlos_initial_specs() -> List[SpiralSpec]:
    return [
        SpiralSpec(
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.15,
            slot_width_mm=14.0,
            top_thickness_mm=2.6,
            label="lower_treble_main",
        ),
        SpiralSpec(
            start_radius_mm=9.0,
            growth_rate_k=0.17,
            turns=1.05,
            slot_width_mm=14.0,
            top_thickness_mm=2.6,
            label="upper_bass_main",
        ),
        SpiralSpec(
            start_radius_mm=6.5,
            growth_rate_k=0.15,
            turns=0.65,
            slot_width_mm=10.0,
            top_thickness_mm=2.5,
            label="small_treble_trim",
            loss_scale=0.85,
        ),
    ]


def demo() -> None:
    body = BodySpec(volume_liters=21.0)
    specs = carlos_initial_specs()
    initial = predict_system(body, specs)
    print(format_system_result(initial))
    print()

    target = TargetSpec(
        target_f_hz=98.0,
        target_q=8.0,
        weight_f=1.0,
        weight_q=0.35,
        target_total_area_cm2=50.0,
        weight_area=0.03,
    )

    fitted, result, info = solve_spiral_parameters(
        body=body,
        base_specs=specs,
        target=target,
        optimize_mask=[True, True, True],
        global_search=False,
        maxiter=80,
    )

    print("Fitted specs:")
    for s in fitted:
        print(
            f"  {s.label}: r0={s.start_radius_mm:.2f} mm, "
            f"k={s.growth_rate_k:.3f}, turns={s.turns:.3f}, "
            f"slot={s.slot_width_mm:.2f} mm, outer_r={outer_radius_mm(s):.1f} mm"
        )
    print()
    print(format_system_result(result))
    print()
    print(f"Solver info: {info}")


if __name__ == "__main__":
    demo()
