"""
test_spiral_q_fh_solver.py
"""

from spiral_q_fh_solver import (
    BodySpec,
    SpiralSpec,
    TargetSpec,
    carlos_initial_specs,
    helmholtz_frequency,
    predict_system,
    required_leff_for_target,
    solve_spiral_parameters,
    sweep_parameter,
)


def test_helmholtz_roundtrip():
    body = BodySpec(volume_liters=21.0)
    area = 0.005
    target = 98.0
    leff = required_leff_for_target(body, area, target)
    assert abs(helmholtz_frequency(body, area, leff) - target) < 1e-9


def test_predict_system_positive():
    body = BodySpec()
    result = predict_system(body, carlos_initial_specs())
    assert result.helmholtz_frequency_hz > 0
    assert result.q > 0
    assert result.total_area_m2 > 0
    assert result.equivalent_effective_length_m > 0


def test_sweep_parameter():
    body = BodySpec()
    specs = carlos_initial_specs()
    rows = sweep_parameter(body, specs, 2, "slot_width_mm", [8, 10, 12])
    assert len(rows) == 3
    assert all(row["f_H_hz"] > 0 for row in rows)


def test_solver_local_runs():
    body = BodySpec()
    specs = carlos_initial_specs()
    target = TargetSpec(target_f_hz=98, target_q=8, weight_f=1.0, weight_q=0.2)
    fitted, result, info = solve_spiral_parameters(
        body,
        specs,
        target,
        optimize_mask=[False, False, True],
        global_search=False,
        maxiter=10,
    )
    assert len(fitted) == 3
    assert result.helmholtz_frequency_hz > 0
    assert "objective" in info
