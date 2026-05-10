"""
test_spiral_acoustic_model.py

Minimal tests for spiral_acoustic_model.py
"""

from spiral_acoustic_model import (
    BodyAcousticSpec,
    SpiralPortSpec,
    compute_spiral_port,
    compute_multiport_system,
    demo_carlos_dual_plus_third,
    helmholtz_frequency_hz,
    required_effective_length_m,
)


def test_required_effective_length_roundtrip():
    body = BodyAcousticSpec(volume_liters=21.0)
    area = 0.005
    target = 100.0
    leff = required_effective_length_m(body, area, target)
    f = helmholtz_frequency_hz(body, area, leff)
    assert abs(f - target) < 1e-9


def test_spiral_port_positive_values():
    body = BodyAcousticSpec()
    spec = SpiralPortSpec()
    port = compute_spiral_port(spec, body)
    assert port.area_m2 > 0
    assert port.perimeter_m > 0
    assert port.path_length_m > 0
    assert port.effective_length_m > 0
    assert port.acoustic_mass > 0


def test_multiport_system_positive_values():
    result = demo_carlos_dual_plus_third()
    assert result.total_area_m2 > 0
    assert result.equivalent_effective_length_m > 0
    assert result.helmholtz_frequency_hz > 0
    assert result.estimated_q > 0
