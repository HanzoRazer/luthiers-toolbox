"""Simple router-bit deflection estimator using Euler–Bernoulli beam math."""

from math import pi


def estimate_deflection_mm(tool_diameter_mm: float, stickout_mm: float, force_n: float) -> float:
    if tool_diameter_mm <= 0 or stickout_mm <= 0:
        return 0.0

    I = pi * (tool_diameter_mm ** 4) / 64.0
    E = 90_000  # MPa, carbide approximation
    L = stickout_mm
    return (force_n * L**3) / (3 * E * I)
