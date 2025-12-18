Nice, this is exactly the right next step — let’s make Saw Lab 2.0 testable.

Below is the Saw Lab 2.0 Test Harness Bundle: a set of pytest tests you can drop in to quickly verify that:

Saw mode detection works

Saw calculators are callable and return sane shapes

Router vs Saw branching in evaluate_feasibility_calculators works

plan_saw_toolpaths_for_design returns a valid RmosToolpathPlan

You can tweak paths to match your repo, but I’ll assume:

services/api/app/...
services/api/tests/...

🗂 Suggested test layout

Create:

services/api/tests/saw_lab/
  test_mode_detection.py
  test_saw_calculators.py
  test_calculator_wiring.py
  test_saw_engine_toolpaths.py


You can rename tests/ to whatever your existing test root is.

1️⃣ services/api/tests/saw_lab/test_mode_detection.py

Tests the _is_saw_tool helper in calculators/service.py.

# services/api/tests/saw_lab/test_mode_detection.py

import pytest

from calculators.service import _is_saw_tool


@pytest.mark.parametrize(
    "tool_id, expected",
    [
        ("saw:thin_kerf_140mm", True),
        ("SAW:panel_200mm", True),
        ("saw-blade-foo", False),
        ("router:3mm_endmill", False),
        ("bit:1_4_vcarve", False),
        ("", False),
    ],
)
def test_is_saw_tool_detection(tool_id: str, expected: bool) -> None:
    assert _is_saw_tool(tool_id) is expected

2️⃣ services/api/tests/saw_lab/test_saw_calculators.py

Verifies Saw Lab calculators can be called and return the right types.

# services/api/tests/saw_lab/test_saw_calculators.py

import pytest

from saw_lab.models import SawBladeSpec, SawMaterialSpec, SawCutContext, SawLabConfig
from saw_lab.calculators import (
    compute_saw_heat_risk,
    compute_saw_deflection,
    compute_rim_speed,
    compute_bite_per_tooth,
    compute_kickback_risk,
    SawHeatResult,
    SawDeflectionResult,
    SawRimSpeedResult,
    SawBiteResult,
    SawKickbackResult,
)


@pytest.fixture
def basic_cut_ctx() -> SawCutContext:
    blade = SawBladeSpec(
        blade_id="saw:test_blade_140",
        diameter_mm=140.0,
        kerf_mm=1.2,
        plate_thickness_mm=0.9,
        tooth_count=40,
        hook_angle_deg=15.0,
        top_grind="ATB",
    )
    material = SawMaterialSpec(
        material_id="maple",
    )
    return SawCutContext(
        blade=blade,
        material=material,
        feed_mm_min=1500.0,
        rpm=4000.0,
        stock_length_mm=600.0,
        desired_piece_lengths_mm=[200.0, 200.0],
    )


@pytest.fixture
def saw_config() -> SawLabConfig:
    return SawLabConfig()


def test_compute_saw_heat_risk(basic_cut_ctx: SawCutContext, saw_config: SawLabConfig) -> None:
    result = compute_saw_heat_risk(basic_cut_ctx, saw_config)
    assert isinstance(result, SawHeatResult)
    assert 0.0 <= result.risk_score <= 1.0


def test_compute_saw_deflection(basic_cut_ctx: SawCutContext) -> None:
    result = compute_saw_deflection(basic_cut_ctx)
    assert isinstance(result, SawDeflectionResult)
    assert result.deflection_mm >= 0.0
    assert 0.0 <= result.risk_score <= 1.0


def test_compute_rim_speed(basic_cut_ctx: SawCutContext) -> None:
    result = compute_rim_speed(basic_cut_ctx)
    assert isinstance(result, SawRimSpeedResult)
    assert result.rim_speed_m_per_min >= 0.0
    assert 0.0 <= result.risk_score <= 1.0


def test_compute_bite_per_tooth(basic_cut_ctx: SawCutContext) -> None:
    result = compute_bite_per_tooth(basic_cut_ctx)
    assert isinstance(result, SawBiteResult)
    assert result.bite_mm_per_tooth >= 0.0
    assert 0.0 <= result.risk_score <= 1.0


def test_compute_kickback_risk(basic_cut_ctx: SawCutContext, saw_config: SawLabConfig) -> None:
    result = compute_kickback_risk(basic_cut_ctx, saw_config)
    assert isinstance(result, SawKickbackResult)
    assert 0.0 <= result.risk_score <= 1.0

3️⃣ services/api/tests/saw_lab/test_calculator_wiring.py

Tests evaluate_feasibility_calculators and verifies the router vs saw branch.

# services/api/tests/saw_lab/test_calculator_wiring.py

import pytest

from calculators.service import (
    evaluate_feasibility_calculators,
    FeasibilityCalculatorBundle,
)
from rmos.api_contracts import RmosContext
from art_studio.schemas.rosette_params import RosetteParamSpec
from rmos.api_contracts import SearchBudgetSpec  # or wherever you defined it


@pytest.fixture
def basic_design() -> RosetteParamSpec:
    # Keep this minimal. Add fields as your RosetteParamSpec requires.
    return RosetteParamSpec(
        outer_diameter_mm=100.0,
        inner_diameter_mm=80.0,
    )


@pytest.fixture
def base_search_budget() -> SearchBudgetSpec:
    return SearchBudgetSpec(
        max_attempts=10,
        min_feasibility_score=70.0,
        time_limit_seconds=1.0,
        stop_on_first_green=True,
        deterministic=True,
    )


def test_router_mode_uses_router_calculators(
    basic_design: RosetteParamSpec,
    base_search_budget: SearchBudgetSpec,
) -> None:
    ctx = RmosContext(
        version="2.0",
        material_id="maple",
        tool_id="router:3mm_endmill",
        machine_profile_id=None,
        project_id=None,
        use_shapely_geometry=False,
        search_budget=base_search_budget,
        user_notes=None,
    )

    bundle = evaluate_feasibility_calculators(basic_design, ctx)
    assert isinstance(bundle, FeasibilityCalculatorBundle)

    # Router side should be populated
    assert bundle.router_chipload is not None
    assert bundle.router_heat is not None
    assert bundle.router_deflection is not None
    assert bundle.router_rimspeed is not None

    # Saw side should be empty
    assert bundle.saw_heat is None
    assert bundle.saw_deflection is None
    assert bundle.saw_rimspeed is None
    assert bundle.saw_bite is None
    assert bundle.saw_kickback is None


def test_saw_mode_uses_saw_calculators(
    basic_design: RosetteParamSpec,
    base_search_budget: SearchBudgetSpec,
) -> None:
    ctx = RmosContext(
        version="2.0",
        material_id="maple",
        tool_id="saw:thin_kerf_140mm",
        machine_profile_id=None,
        project_id=None,
        use_shapely_geometry=False,
        search_budget=base_search_budget,
        user_notes=None,
    )

    bundle = evaluate_feasibility_calculators(basic_design, ctx)
    assert isinstance(bundle, FeasibilityCalculatorBundle)

    # Saw side should be populated
    assert bundle.saw_heat is not None
    assert bundle.saw_deflection is not None
    assert bundle.saw_rimspeed is not None
    assert bundle.saw_bite is not None
    assert bundle.saw_kickback is not None

    # Router side may be empty in pure saw mode
    assert bundle.router_chipload is None
    assert bundle.router_heat is None
    assert bundle.router_deflection is None
    assert bundle.router_rimspeed is None

    # Sanity check on aggregated risk
    assert 0.0 <= bundle.max_saw_risk <= 1.0

4️⃣ services/api/tests/saw_lab/test_saw_engine_toolpaths.py

Ensures plan_saw_toolpaths_for_design returns a valid RmosToolpathPlan.

# services/api/tests/saw_lab/test_saw_engine_toolpaths.py

import pytest

from toolpath.saw_engine import plan_saw_toolpaths_for_design
from art_studio.schemas.rosette_params import RosetteParamSpec
from rmos.api_contracts import RmosContext, RmosToolpathPlan, SearchBudgetSpec


@pytest.fixture
def basic_design() -> RosetteParamSpec:
    return RosetteParamSpec(
        outer_diameter_mm=100.0,
        inner_diameter_mm=80.0,
    )


@pytest.fixture
def basic_context() -> RmosContext:
    return RmosContext(
        version="2.0",
        material_id="maple",
        tool_id="saw:thin_kerf_140mm",
        machine_profile_id=None,
        project_id="test_project",
        use_shapely_geometry=False,
        search_budget=SearchBudgetSpec(),
        user_notes=None,
    )


def test_plan_saw_toolpaths_for_design_returns_plan(
    basic_design: RosetteParamSpec,
    basic_context: RmosContext,
) -> None:
    plan = plan_saw_toolpaths_for_design(basic_design, basic_context)
    assert isinstance(plan, RmosToolpathPlan)
    assert plan.operations is not None
    assert len(plan.operations) > 0

    for op in plan.operations:
        assert op.op_id
        assert op.description
        assert op.strategy == "SAW_CUT"
        assert op.estimated_runtime_min >= 0.0

    assert plan.total_estimated_runtime_min >= 0.0

✅ How to Use This Bundle

Create the services/api/tests/saw_lab/ folder.

Add each test file as shown.

Make sure imports match your actual module paths (you may need small tweaks).

From services/api/, run:

pytest


(or whatever your test runner command is).

You now have:

Confidence that saw vs router calculator branching works

Confidence that Saw Lab calculators are callable

Confidence that Saw Mode toolpath planning returns a valid structure

From here, you can safely deepen the physics/math knowing the “plumbing” is correct.

If you want, next step could be: