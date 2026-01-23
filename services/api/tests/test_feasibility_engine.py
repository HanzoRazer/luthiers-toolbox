from __future__ import annotations

import pytest


def _make_input(**overrides):
    """Factory for a minimal, deterministic FeasibilityInput."""
    from app.rmos.feasibility import FeasibilityInput
    from app.rmos.feasibility.schemas import MaterialHardness

    base = FeasibilityInput(
        # Identity / context
        pipeline_id="mvp_dxf_to_grbl_v1",
        post_id="GRBL",
        units="mm",
        # CAM params
        tool_d=6.0,
        stepover=0.45,
        stepdown=1.5,
        z_rough=-3.0,
        feed_xy=1200.0,
        feed_z=300.0,
        rapid=3000.0,
        safe_z=5.0,
        strategy="Spiral",
        layer_name="GEOMETRY",
        climb=True,
        smoothing=0.1,
        margin=0.0,
        # Pre-CAM geometry hints
        has_closed_paths=True,
        loop_count_hint=2,
        entity_count=5,
        bbox={"x_min": 0.0, "y_min": 0.0, "x_max": 100.0, "y_max": 50.0},
        smallest_feature_mm=None,
        # Material (required by F024 for adversarial detection)
        material_hardness=MaterialHardness.MEDIUM,
    )

    data = base.model_dump()
    data.update(overrides)
    return FeasibilityInput(**data)


def _norm_for_hash(feasibility_result):
    """Normalize feasibility result to a stable dict for hashing."""
    d = feasibility_result.model_dump()
    # Engine may include a timestamp; feasibility hashes must not.
    d.pop("computed_at_utc", None)
    return d


def test_feasibility_hash_is_deterministic():
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.runs_v2.hashing import compute_feasibility_hash

    fi = _make_input()
    r1 = compute_feasibility(fi)
    r2 = compute_feasibility(fi)

    h1 = compute_feasibility_hash(_norm_for_hash(r1))
    h2 = compute_feasibility_hash(_norm_for_hash(r2))

    assert h1 == h2
    assert isinstance(h1, str)
    assert len(h1) == 64


def test_red_when_tool_d_invalid():
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.feasibility.schemas import RiskLevel

    fi = _make_input(tool_d=0.0)
    r = compute_feasibility(fi)

    assert r.risk_level == RiskLevel.RED
    assert r.blocking is True
    assert any("tool_d" in s for s in r.blocking_reasons)


def test_red_when_stepover_out_of_range():
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.feasibility.schemas import RiskLevel

    fi = _make_input(stepover=1.0)
    r = compute_feasibility(fi)

    assert r.risk_level == RiskLevel.RED
    assert r.blocking is True
    assert any("stepover" in s for s in r.blocking_reasons)


def test_red_when_z_rough_non_negative():
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.feasibility.schemas import RiskLevel

    fi = _make_input(z_rough=0.0)
    r = compute_feasibility(fi)

    assert r.risk_level == RiskLevel.RED
    assert r.blocking is True
    assert any("z_rough" in s for s in r.blocking_reasons)


def test_red_when_no_closed_paths_hint():
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.feasibility.schemas import RiskLevel

    fi = _make_input(has_closed_paths=False)
    r = compute_feasibility(fi)

    assert r.risk_level == RiskLevel.RED
    assert r.blocking is True
    assert any("closed" in s.lower() for s in r.blocking_reasons)


def test_yellow_when_feed_z_greater_than_feed_xy():
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.feasibility.schemas import RiskLevel

    fi = _make_input(feed_xy=300.0, feed_z=500.0)
    r = compute_feasibility(fi)

    assert r.risk_level == RiskLevel.YELLOW
    assert r.blocking is False
    assert any("feed" in s.lower() for s in r.warnings)


def test_green_when_valid_minimal():
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.feasibility.schemas import RiskLevel

    fi = _make_input()
    r = compute_feasibility(fi)

    assert r.risk_level == RiskLevel.GREEN
    assert r.blocking is False
    assert r.blocking_reasons == []


def test_reason_order_is_stable_for_hashing():
    """
    Multiple issues should yield deterministic ordering so the
    feasibility hash doesn't jitter.
    """
    from app.rmos.feasibility import compute_feasibility
    from app.rmos.runs_v2.hashing import compute_feasibility_hash

    fi = _make_input(tool_d=0.0, z_rough=0.0, safe_z=0.0)
    r1 = compute_feasibility(fi)

    fi2 = _make_input(tool_d=0.0, z_rough=0.0, safe_z=0.0)
    r2 = compute_feasibility(fi2)

    assert r1.blocking_reasons == r2.blocking_reasons
    assert r1.warnings == r2.warnings
    assert compute_feasibility_hash(_norm_for_hash(r1)) == compute_feasibility_hash(_norm_for_hash(r2))
