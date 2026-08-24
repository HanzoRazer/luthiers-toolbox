"""Smoke tests for Retract Pattern Optimization endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# Sample feature data for testing
SIMPLE_FEATURES = [
    [[0, 0, -10], [10, 0, -10], [10, 10, -10], [0, 10, -10]],
    [[20, 0, -10], [30, 0, -10], [30, 10, -10], [20, 10, -10]]
]

SINGLE_FEATURE = [
    [[0, 0, -5], [10, 0, -5], [10, 10, -5]]
]


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_strategies_endpoint_exists(client):
    """GET /api/cam/retract/strategies endpoint exists."""
    response = client.get("/api/cam/retract/strategies")
    assert response.status_code != 404


def test_apply_endpoint_exists(client):
    """POST /api/cam/retract/apply endpoint exists."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SINGLE_FEATURE,
        "strategy": "safe"
    })
    assert response.status_code != 404


def test_lead_in_endpoint_exists(client):
    """POST /api/cam/retract/lead_in endpoint exists."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10
    })
    assert response.status_code != 404


def test_estimate_endpoint_exists(client):
    """POST /api/cam/retract/estimate endpoint exists."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe",
        "features_count": 5
    })
    assert response.status_code != 404


def test_gcode_endpoint_exists(client):
    """POST /api/cam/retract/gcode endpoint exists."""
    response = client.post("/api/cam/retract/gcode")
    assert response.status_code != 404


def test_gcode_download_endpoint_exists(client):
    """POST /api/cam/retract/gcode/download endpoint exists."""
    response = client.post("/api/cam/retract/gcode/download", json={
        "features": SINGLE_FEATURE,
        "strategy": "safe"
    })
    assert response.status_code != 404


# =============================================================================
# Strategies Endpoint
# =============================================================================

def test_strategies_returns_200(client):
    """GET /api/cam/retract/strategies returns 200."""
    response = client.get("/api/cam/retract/strategies")
    assert response.status_code == 200


def test_strategies_has_strategies_list(client):
    """Response has strategies list."""
    response = client.get("/api/cam/retract/strategies")
    data = response.json()

    assert "strategies" in data
    assert isinstance(data["strategies"], list)


def test_strategies_has_minimal(client):
    """Strategies include 'minimal'."""
    response = client.get("/api/cam/retract/strategies")
    data = response.json()

    names = [s["name"] for s in data["strategies"]]
    assert "minimal" in names


def test_strategies_has_safe(client):
    """Strategies include 'safe'."""
    response = client.get("/api/cam/retract/strategies")
    data = response.json()

    names = [s["name"] for s in data["strategies"]]
    assert "safe" in names


def test_strategies_has_incremental(client):
    """Strategies include 'incremental'."""
    response = client.get("/api/cam/retract/strategies")
    data = response.json()

    names = [s["name"] for s in data["strategies"]]
    assert "incremental" in names


def test_strategy_has_description(client):
    """Each strategy has description."""
    response = client.get("/api/cam/retract/strategies")
    data = response.json()

    for strategy in data["strategies"]:
        assert "description" in strategy
        assert isinstance(strategy["description"], str)


def test_strategy_has_pros_cons(client):
    """Each strategy has pros and cons."""
    response = client.get("/api/cam/retract/strategies")
    data = response.json()

    for strategy in data["strategies"]:
        assert "pros" in strategy
        assert "cons" in strategy


def test_strategy_has_use_cases(client):
    """Each strategy has use_cases."""
    response = client.get("/api/cam/retract/strategies")
    data = response.json()

    for strategy in data["strategies"]:
        assert "use_cases" in strategy
        assert isinstance(strategy["use_cases"], list)


# =============================================================================
# Apply Endpoint
# =============================================================================

def test_apply_returns_200(client):
    """POST /api/cam/retract/apply returns 200."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert response.status_code == 200


def test_apply_has_gcode(client):
    """Apply response has gcode list."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    data = response.json()

    assert "gcode" in data
    assert isinstance(data["gcode"], list)


def test_apply_has_stats(client):
    """Apply response has stats dict."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    data = response.json()

    assert "stats" in data
    assert isinstance(data["stats"], dict)


def test_apply_minimal_strategy(client):
    """Apply with minimal strategy."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "minimal"
    })
    assert response.status_code == 200


def test_apply_incremental_strategy(client):
    """Apply with incremental strategy."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "incremental"
    })
    assert response.status_code == 200


def test_apply_invalid_strategy_400(client):
    """Apply with invalid strategy returns 400."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "invalid_strategy"
    })
    assert response.status_code == 400


def test_apply_empty_features_400(client):
    """Apply with empty features returns 400."""
    response = client.post("/api/cam/retract/apply", json={
        "features": [],
        "strategy": "safe"
    })
    assert response.status_code == 400


def test_apply_custom_safe_z(client):
    """Apply with custom safe_z."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe",
        "safe_z": 25.0
    })
    assert response.status_code == 200


def test_apply_custom_feed_rate(client):
    """Apply with custom feed_rate."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe",
        "feed_rate": 500.0
    })
    assert response.status_code == 200


def test_apply_path_optimization_none(client):
    """Apply with no path optimization."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe",
        "optimize_path": "none"
    })
    assert response.status_code == 200


def test_apply_path_optimization_nearest(client):
    """Apply with nearest neighbor optimization."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe",
        "optimize_path": "nearest_neighbor"
    })
    assert response.status_code == 200


def test_apply_requires_features(client):
    """Apply requires features field."""
    response = client.post("/api/cam/retract/apply", json={
        "strategy": "safe"
    })
    assert response.status_code == 422


def test_apply_gcode_contains_g_commands(client):
    """Apply G-code contains G commands."""
    response = client.post("/api/cam/retract/apply", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    data = response.json()

    gcode_text = "\n".join(data["gcode"])
    assert "G" in gcode_text


# =============================================================================
# Lead-In Endpoint
# =============================================================================

def test_lead_in_returns_200(client):
    """POST /api/cam/retract/lead_in returns 200."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10
    })
    assert response.status_code == 200


def test_lead_in_has_gcode(client):
    """Lead-in response has gcode list."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10
    })
    data = response.json()

    assert "gcode" in data
    assert isinstance(data["gcode"], list)


def test_lead_in_linear_pattern(client):
    """Lead-in with linear pattern."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10,
        "pattern": "linear"
    })
    assert response.status_code == 200


def test_lead_in_arc_pattern(client):
    """Lead-in with arc pattern."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10,
        "pattern": "arc"
    })
    assert response.status_code == 200


def test_lead_in_invalid_pattern_400(client):
    """Lead-in with invalid pattern returns 400."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10,
        "pattern": "invalid"
    })
    assert response.status_code == 400


def test_lead_in_custom_distance(client):
    """Lead-in with custom distance."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10,
        "distance": 5.0
    })
    assert response.status_code == 200


def test_lead_in_custom_angle(client):
    """Lead-in with custom angle."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10,
        "angle": 30.0
    })
    assert response.status_code == 200


def test_lead_in_custom_feed_reduction(client):
    """Lead-in with custom feed reduction."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10,
        "feed_reduction": 0.3
    })
    assert response.status_code == 200


def test_lead_in_requires_start_x(client):
    """Lead-in requires start_x."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_y": 0,
        "start_z": 5,
        "entry_x": 10,
        "entry_y": 10
    })
    assert response.status_code == 422


def test_lead_in_requires_entry_x(client):
    """Lead-in requires entry_x."""
    response = client.post("/api/cam/retract/lead_in", json={
        "start_x": 0,
        "start_y": 0,
        "start_z": 5,
        "entry_y": 10
    })
    assert response.status_code == 422


# =============================================================================
# Estimate Endpoint
# =============================================================================

def test_estimate_returns_200(client):
    """POST /api/cam/retract/estimate returns 200."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe",
        "features_count": 10
    })
    assert response.status_code == 200


def test_estimate_has_total_time(client):
    """Estimate response has total_time_s."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe",
        "features_count": 10
    })
    data = response.json()

    assert "total_time_s" in data
    assert isinstance(data["total_time_s"], (int, float))


def test_estimate_has_z_time(client):
    """Estimate response has z_time_s."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe",
        "features_count": 10
    })
    data = response.json()

    assert "z_time_s" in data


def test_estimate_has_xy_time(client):
    """Estimate response has xy_time_s."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe",
        "features_count": 10
    })
    data = response.json()

    assert "xy_time_s" in data


def test_estimate_has_savings_pct(client):
    """Estimate response has savings_pct."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "minimal",
        "features_count": 10
    })
    data = response.json()

    assert "savings_pct" in data


def test_estimate_minimal_strategy(client):
    """Estimate with minimal strategy."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "minimal",
        "features_count": 20
    })
    assert response.status_code == 200


def test_estimate_incremental_strategy(client):
    """Estimate with incremental strategy."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "incremental",
        "features_count": 15
    })
    assert response.status_code == 200


def test_estimate_invalid_strategy_400(client):
    """Estimate with invalid strategy returns 400."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "invalid",
        "features_count": 10
    })
    assert response.status_code == 400


def test_estimate_zero_features_400(client):
    """Estimate with zero features returns 400."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe",
        "features_count": 0
    })
    assert response.status_code == 400


def test_estimate_custom_avg_distance(client):
    """Estimate with custom avg_feature_distance."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe",
        "features_count": 10,
        "avg_feature_distance": 100.0
    })
    assert response.status_code == 200


def test_estimate_requires_strategy(client):
    """Estimate requires strategy field."""
    response = client.post("/api/cam/retract/estimate", json={
        "features_count": 10
    })
    assert response.status_code == 422


def test_estimate_requires_features_count(client):
    """Estimate requires features_count field."""
    response = client.post("/api/cam/retract/estimate", json={
        "strategy": "safe"
    })
    assert response.status_code == 422


# =============================================================================
# G-code Generation Endpoints
# =============================================================================

@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_returns_200(client):
    """POST /api/cam/retract/gcode returns 200."""
    response = client.post("/api/cam/retract/gcode")
    assert response.status_code == 200


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_returns_text_content_type(client):
    """G-code endpoint returns text content type."""
    response = client.post("/api/cam/retract/gcode")
    content_type = response.headers.get("content-type", "")
    assert "text" in content_type


def test_gcode_contains_g_commands(client):
    """Blocked retract JSON is not G-code.

    The pre-001B assertion ``"G" in content`` is not a G-code witness:
    ``FEASIBILITY_ENGINE_UNAVAILABLE`` contains the letter G, so it would
    pass on the 409 body. Assert machine markers instead.
    """
    response = client.post("/api/cam/retract/gcode")
    assert response.status_code == 409
    for marker in ("G21", "G90", "G0 Z", "G1 Z", "G2 X", "M30"):
        assert marker not in response.text


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_contains_m30(client):
    """G-code ends with M30."""
    response = client.post("/api/cam/retract/gcode")
    content = response.text
    assert "M30" in content


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_direct_strategy(client):
    """G-code with direct strategy."""
    response = client.post("/api/cam/retract/gcode?strategy=direct")
    assert response.status_code == 200
    assert "direct" in response.text.lower() or "Direct" in response.text


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_ramped_strategy(client):
    """G-code with ramped strategy."""
    response = client.post("/api/cam/retract/gcode?strategy=ramped")
    assert response.status_code == 200
    assert "ramped" in response.text.lower() or "Ramped" in response.text


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_helical_strategy(client):
    """G-code with helical strategy."""
    response = client.post("/api/cam/retract/gcode?strategy=helical")
    assert response.status_code == 200
    assert "G2" in response.text  # Arc command for helix


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_custom_safe_z(client):
    """G-code with custom safe_z."""
    response = client.post("/api/cam/retract/gcode?safe_z=20.0")
    assert response.status_code == 200
    assert "20" in response.text


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_custom_current_z(client):
    """G-code with custom current_z."""
    response = client.post("/api/cam/retract/gcode?current_z=-20.0")
    assert response.status_code == 200


def test_gcode_has_toolbox_lane_header(client):
    """Former draft path still advertises a lane header — now governed."""
    response = client.post("/api/cam/retract/gcode")
    assert response.status_code == 409
    assert "X-ToolBox-Lane" in response.headers


def test_gcode_lane_is_governed(client):
    """Former draft /gcode path inherits governed lane semantics."""
    response = client.post("/api/cam/retract/gcode")
    assert response.status_code == 409
    assert response.headers.get("X-ToolBox-Lane") == "governed"
    assert response.headers.get("X-Run-ID")


# =============================================================================
# G-code Governed Endpoint
# =============================================================================

@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_governed_returns_200(client):
    """POST /api/cam/retract/gcode_governed returns 200."""
    response = client.post("/api/cam/retract/gcode_governed")
    assert response.status_code == 200


def test_gcode_governed_has_run_id_header(client):
    """Governed endpoint returns X-Run-ID header (including while blocked)."""
    response = client.post("/api/cam/retract/gcode_governed")
    assert response.status_code == 409
    assert "X-Run-ID" in response.headers


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_governed_has_gcode_hash_header(client):
    """Governed endpoint returns X-GCode-SHA256 header."""
    response = client.post("/api/cam/retract/gcode_governed")
    assert "X-GCode-SHA256" in response.headers


def test_gcode_governed_lane_is_governed(client):
    """Governed endpoint has governed lane (including while blocked)."""
    response = client.post("/api/cam/retract/gcode_governed")
    assert response.status_code == 409
    assert response.headers.get("X-ToolBox-Lane") == "governed"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_governed_contains_gcode(client):
    """Governed endpoint returns valid G-code."""
    response = client.post("/api/cam/retract/gcode_governed")
    content = response.text
    assert "G" in content
    assert "M30" in content


# =============================================================================
# G-code Download Endpoint
# =============================================================================

@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_download_returns_200(client):
    """POST /api/cam/retract/gcode/download returns 200."""
    response = client.post("/api/cam/retract/gcode/download", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert response.status_code == 200


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_download_has_disposition_header(client):
    """Download has Content-Disposition header."""
    response = client.post("/api/cam/retract/gcode/download", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert "Content-Disposition" in response.headers


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_download_filename_contains_strategy(client):
    """Download filename contains strategy name."""
    response = client.post("/api/cam/retract/gcode/download", json={
        "features": SIMPLE_FEATURES,
        "strategy": "minimal"
    })
    disposition = response.headers.get("Content-Disposition", "")
    assert "minimal" in disposition


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_download_is_nc_file(client):
    """Download is .nc file."""
    response = client.post("/api/cam/retract/gcode/download", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    disposition = response.headers.get("Content-Disposition", "")
    assert ".nc" in disposition


def test_gcode_download_lane_is_governed(client):
    """Former draft download path inherits governed lane semantics."""
    response = client.post("/api/cam/retract/gcode/download", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert response.status_code == 409
    assert response.headers.get("X-ToolBox-Lane") == "governed"
    assert response.headers.get("X-Run-ID")


# =============================================================================
# G-code Download Governed Endpoint
# =============================================================================

@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_download_governed_returns_200(client):
    """POST /api/cam/retract/gcode/download_governed returns 200."""
    response = client.post("/api/cam/retract/gcode/download_governed", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert response.status_code == 200


def test_gcode_download_governed_has_run_id(client):
    """Download governed has X-Run-ID header (including while blocked)."""
    response = client.post("/api/cam/retract/gcode/download_governed", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert response.status_code == 409
    assert "X-Run-ID" in response.headers


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_download_governed_has_gcode_hash(client):
    """Download governed has X-GCode-SHA256 header."""
    response = client.post("/api/cam/retract/gcode/download_governed", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert "X-GCode-SHA256" in response.headers


def test_gcode_download_governed_lane_is_governed(client):
    """Download governed has governed lane (including while blocked)."""
    response = client.post("/api/cam/retract/gcode/download_governed", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    assert response.status_code == 409
    assert response.headers.get("X-ToolBox-Lane") == "governed"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_gcode_download_governed_is_nc_file(client):
    """Download governed is .nc file."""
    response = client.post("/api/cam/retract/gcode/download_governed", json={
        "features": SIMPLE_FEATURES,
        "strategy": "safe"
    })
    disposition = response.headers.get("Content-Disposition", "")
    assert ".nc" in disposition


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_apply_and_download_same_features(client):
    """Apply and download work with same features."""
    features = SIMPLE_FEATURES

    apply_response = client.post("/api/cam/retract/apply", json={
        "features": features,
        "strategy": "safe"
    })
    download_response = client.post("/api/cam/retract/gcode/download", json={
        "features": features,
        "strategy": "safe"
    })

    assert apply_response.status_code == 200
    assert download_response.status_code == 200


def test_all_strategies_work_with_apply(client):
    """All strategies work with apply endpoint."""
    for strategy in ["minimal", "safe", "incremental"]:
        response = client.post("/api/cam/retract/apply", json={
            "features": SIMPLE_FEATURES,
            "strategy": strategy
        })
        assert response.status_code == 200, f"Strategy '{strategy}' failed"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RMOS-CONVERGE-001B: the retract capability has no substantive feasibility "
        "evaluator, so all four G-code routes are blocked by design (409 SAFETY_BLOCKED) "
        "per the owner ruling of 2026-08-23 - an ungoverned convenience endpoint is not an "
        "accepted alternate production path. The assertions below are the contract to restore "
        "when a retract evaluator lands and the mode is registered in "
        "_PRODUCTION_FEASIBILITY_ENGINES; strict=True so they fail loudly the moment the lane "
        "reopens. Current behaviour is witnessed by "
        "tests/rmos/test_rmos_output_route_convergence.py."
    ),
)
def test_all_gcode_strategies_work(client):
    """All G-code strategies work."""
    for strategy in ["direct", "ramped", "helical"]:
        response = client.post(f"/api/cam/retract/gcode?strategy={strategy}")
        assert response.status_code == 200, f"Strategy '{strategy}' failed"


def test_legacy_and_alias_paths_share_one_authority_outcome(client):
    """Former draft URL and _governed alias return the same blocked outcome."""
    legacy = client.post("/api/cam/retract/gcode?strategy=direct")
    alias = client.post("/api/cam/retract/gcode_governed?strategy=direct")

    assert legacy.status_code == 409
    assert alias.status_code == 409
    assert legacy.headers.get("X-ToolBox-Lane") == "governed"
    assert alias.headers.get("X-ToolBox-Lane") == "governed"
    assert legacy.json()["detail"]["error"] == "SAFETY_BLOCKED"
    assert alias.json()["detail"]["error"] == "SAFETY_BLOCKED"
