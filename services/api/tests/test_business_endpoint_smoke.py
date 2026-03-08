"""Smoke tests for Business Suite router endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Health Check
# =============================================================================

def test_business_health_endpoint_exists(client):
    """GET /api/business/health endpoint exists."""
    response = client.get("/api/business/health")
    assert response.status_code != 404


def test_business_health_returns_200(client):
    """Business health returns 200."""
    response = client.get("/api/business/health")
    assert response.status_code == 200


def test_business_health_response_structure(client):
    """Business health has expected structure."""
    response = client.get("/api/business/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["module"] == "business"
    assert "services" in data


# =============================================================================
# BOM Endpoints - Existence
# =============================================================================

def test_materials_list_endpoint_exists(client):
    """GET /api/business/materials endpoint exists."""
    response = client.get("/api/business/materials")
    assert response.status_code != 404


def test_materials_get_endpoint_exists(client):
    """GET /api/business/materials/{id} endpoint exists."""
    response = client.get("/api/business/materials/test-id")
    # 404 for not found is valid (endpoint exists)
    assert response.status_code in [200, 404]


def test_materials_post_endpoint_exists(client):
    """POST /api/business/materials endpoint exists."""
    response = client.post("/api/business/materials", json={
        "id": "test-mat-001",
        "name": "Test Material",
        "category": "tonewood",
        "unit": "bd_ft",
        "unit_cost": 10.0
    })
    assert response.status_code != 404


def test_bom_templates_endpoint_exists(client):
    """GET /api/business/bom/templates endpoint exists."""
    response = client.get("/api/business/bom/templates")
    assert response.status_code != 404


def test_bom_from_template_endpoint_exists(client):
    """POST /api/business/bom/from-template endpoint exists."""
    response = client.post(
        "/api/business/bom/from-template",
        params={"instrument_type": "acoustic_dreadnought", "instrument_name": "Test Guitar"}
    )
    assert response.status_code != 404


# =============================================================================
# BOM Endpoints - Response Tests
# =============================================================================

def test_materials_list_returns_list(client):
    """Materials list returns list."""
    response = client.get("/api/business/materials")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_materials_filter_by_category(client):
    """Materials can be filtered by category."""
    response = client.get("/api/business/materials", params={"category": "tonewood"})
    assert response.status_code == 200


def test_bom_templates_returns_dict(client):
    """BOM templates returns dict with templates."""
    response = client.get("/api/business/bom/templates")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data


def test_bom_from_template_creates_bom(client):
    """BOM from template creates valid BOM."""
    response = client.post(
        "/api/business/bom/from-template",
        params={"instrument_type": "acoustic_dreadnought", "instrument_name": "Test Guitar"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["instrument_name"] == "Test Guitar"
    assert data["instrument_type"] == "acoustic_dreadnought"


# =============================================================================
# COGS Endpoints - Existence
# =============================================================================

def test_cogs_calculate_endpoint_exists(client):
    """POST /api/business/cogs/calculate endpoint exists."""
    response = client.post("/api/business/cogs/calculate", json={
        "instrument_type": "acoustic_dreadnought",
        "instrument_name": "Test",
        "created_at": "2024-01-01",
        "items": [],
        "total_materials_cost": 0.0,
        "total_items": 0,
        "cost_by_category": {}
    })
    assert response.status_code != 404


def test_cogs_labor_rates_endpoint_exists(client):
    """GET /api/business/cogs/labor-rates endpoint exists."""
    response = client.get("/api/business/cogs/labor-rates")
    assert response.status_code != 404


def test_cogs_labor_rate_update_endpoint_exists(client):
    """PUT /api/business/cogs/labor-rates/{category} endpoint exists."""
    response = client.put(
        "/api/business/cogs/labor-rates/design",
        params={"hourly_rate": 50.0}
    )
    assert response.status_code != 404


def test_cogs_overhead_endpoint_exists(client):
    """GET /api/business/cogs/overhead endpoint exists."""
    response = client.get("/api/business/cogs/overhead")
    assert response.status_code != 404


# =============================================================================
# COGS Endpoints - Response Tests
# =============================================================================

def test_cogs_labor_rates_returns_rates(client):
    """Labor rates endpoint returns rates list."""
    response = client.get("/api/business/cogs/labor-rates")
    assert response.status_code == 200
    data = response.json()
    assert "rates" in data


def test_cogs_overhead_returns_summary(client):
    """Overhead endpoint returns summary."""
    response = client.get("/api/business/cogs/overhead")
    assert response.status_code == 200


def test_cogs_labor_rate_update_works(client):
    """Labor rate can be updated."""
    response = client.put(
        "/api/business/cogs/labor-rates/design",
        params={"hourly_rate": 55.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"


# =============================================================================
# Pricing Endpoints - Existence
# =============================================================================

def test_pricing_calculate_endpoint_exists(client):
    """POST /api/business/pricing/calculate endpoint exists."""
    response = client.post(
        "/api/business/pricing/calculate",
        params={
            "cogs": 500.0,
            "instrument_name": "Test Guitar"
        }
    )
    assert response.status_code != 404


def test_pricing_competitors_get_endpoint_exists(client):
    """GET /api/business/pricing/competitors endpoint exists."""
    response = client.get("/api/business/pricing/competitors")
    assert response.status_code != 404


def test_pricing_competitors_post_endpoint_exists(client):
    """POST /api/business/pricing/competitors endpoint exists."""
    response = client.post("/api/business/pricing/competitors", json={
        "competitor_name": "Test Luthier",
        "instrument_type": "acoustic_dreadnought",
        "price": 2500.0,
        "quality_tier": "mid"
    })
    assert response.status_code != 404


# =============================================================================
# Pricing Endpoints - Response Tests
# =============================================================================

def test_pricing_calculate_returns_strategy(client):
    """Pricing calculate returns strategy."""
    response = client.post(
        "/api/business/pricing/calculate",
        params={
            "cogs": 500.0,
            "instrument_name": "Test Guitar"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "cost_plus_price" in data
    assert "recommended_price" in data


def test_pricing_calculate_with_markup(client):
    """Pricing calculate accepts custom markup."""
    response = client.post(
        "/api/business/pricing/calculate",
        params={
            "cogs": 500.0,
            "instrument_name": "Test Guitar",
            "markup_pct": 75.0
        }
    )
    assert response.status_code == 200


def test_pricing_competitors_returns_summary(client):
    """Competitor endpoint returns summary."""
    response = client.get("/api/business/pricing/competitors")
    assert response.status_code == 200


# =============================================================================
# Break-Even Endpoints - Existence
# =============================================================================

def test_breakeven_calculate_endpoint_exists(client):
    """POST /api/business/breakeven/calculate endpoint exists."""
    response = client.post(
        "/api/business/breakeven/calculate",
        params={
            "fixed_costs_monthly": 2000.0,
            "variable_cost_per_unit": 500.0,
            "selling_price_per_unit": 1500.0
        }
    )
    assert response.status_code != 404


def test_breakeven_target_profit_endpoint_exists(client):
    """POST /api/business/breakeven/target-profit endpoint exists."""
    response = client.post(
        "/api/business/breakeven/target-profit",
        params={
            "fixed_costs": 2000.0,
            "variable_cost": 500.0,
            "price": 1500.0,
            "target_monthly_profit": 3000.0
        }
    )
    assert response.status_code != 404


def test_breakeven_sensitivity_endpoint_exists(client):
    """POST /api/business/breakeven/sensitivity endpoint exists."""
    response = client.post(
        "/api/business/breakeven/sensitivity",
        params={
            "fixed_costs": 2000.0,
            "variable_cost": 500.0,
            "price": 1500.0
        }
    )
    assert response.status_code != 404


# =============================================================================
# Break-Even Endpoints - Response Tests
# =============================================================================

def test_breakeven_calculate_returns_analysis(client):
    """Break-even calculate returns analysis."""
    response = client.post(
        "/api/business/breakeven/calculate",
        params={
            "fixed_costs_monthly": 2000.0,
            "variable_cost_per_unit": 500.0,
            "selling_price_per_unit": 1500.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "break_even_units" in data
    assert "contribution_margin" in data


def test_breakeven_target_profit_returns_volume(client):
    """Target profit endpoint returns required volume."""
    response = client.post(
        "/api/business/breakeven/target-profit",
        params={
            "fixed_costs": 2000.0,
            "variable_cost": 500.0,
            "price": 1500.0,
            "target_monthly_profit": 3000.0
        }
    )
    assert response.status_code == 200


def test_breakeven_sensitivity_returns_scenarios(client):
    """Sensitivity analysis returns scenarios."""
    response = client.post(
        "/api/business/breakeven/sensitivity",
        params={
            "fixed_costs": 2000.0,
            "variable_cost": 500.0,
            "price": 1500.0
        }
    )
    assert response.status_code == 200


# =============================================================================
# Cash Flow Endpoints - Existence
# =============================================================================

def test_cashflow_project_endpoint_exists(client):
    """POST /api/business/cashflow/project endpoint exists."""
    response = client.post(
        "/api/business/cashflow/project",
        params={
            "projection_name": "Test Projection",
            "months": 12,
            "starting_cash": 10000.0
        }
    )
    assert response.status_code != 404


def test_cashflow_startup_endpoint_exists(client):
    """POST /api/business/cashflow/startup endpoint exists."""
    response = client.post(
        "/api/business/cashflow/startup",
        params={
            "projection_name": "Startup Plan",
            "starting_cash": 20000.0,
            "monthly_overhead": 2000.0,
            "target_monthly_revenue": 5000.0
        }
    )
    assert response.status_code != 404


def test_cashflow_required_capital_endpoint_exists(client):
    """POST /api/business/cashflow/required-capital endpoint exists."""
    response = client.post(
        "/api/business/cashflow/required-capital",
        params={
            "monthly_overhead": 2000.0,
            "target_monthly_revenue": 5000.0
        }
    )
    assert response.status_code != 404


# =============================================================================
# Cash Flow Endpoints - Response Tests
# =============================================================================

def test_cashflow_project_returns_projection(client):
    """Cash flow project returns projection."""
    response = client.post(
        "/api/business/cashflow/project",
        params={
            "projection_name": "Test Projection",
            "months": 6,
            "starting_cash": 10000.0,
            "monthly_revenue": 3000.0,
            "monthly_overhead": 1500.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "monthly_data" in data
    assert len(data["monthly_data"]) == 6


def test_cashflow_startup_returns_ramp_projection(client):
    """Startup projection returns ramp-up model."""
    response = client.post(
        "/api/business/cashflow/startup",
        params={
            "projection_name": "Startup Plan",
            "starting_cash": 20000.0,
            "monthly_overhead": 2000.0,
            "target_monthly_revenue": 5000.0,
            "months_to_ramp": 6,
            "total_months": 12
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "monthly_data" in data


def test_cashflow_required_capital_returns_amount(client):
    """Required capital endpoint returns amount."""
    response = client.post(
        "/api/business/cashflow/required-capital",
        params={
            "monthly_overhead": 2000.0,
            "target_monthly_revenue": 5000.0,
            "months_to_revenue": 3,
            "buffer_months": 2
        }
    )
    assert response.status_code == 200


# =============================================================================
# Engineering Estimator Endpoints - Existence
# =============================================================================

def test_estimate_parametric_endpoint_exists(client):
    """POST /api/business/estimate/parametric endpoint exists."""
    response = client.post("/api/business/estimate/parametric", json={
        "instrument_type": "acoustic_dreadnought",
        "complexity_level": "standard"
    })
    assert response.status_code != 404


def test_estimate_quote_endpoint_exists(client):
    """POST /api/business/estimate/quote endpoint exists."""
    response = client.post("/api/business/estimate/quote", json={
        "instrument_type": "acoustic_dreadnought",
        "customer_name": "Test Customer"
    })
    assert response.status_code != 404


def test_estimate_factors_endpoint_exists(client):
    """GET /api/business/estimate/factors endpoint exists."""
    response = client.get("/api/business/estimate/factors")
    assert response.status_code != 404


def test_estimate_wbs_endpoint_exists(client):
    """GET /api/business/estimate/wbs/{instrument_type} endpoint exists."""
    response = client.get("/api/business/estimate/wbs/acoustic_dreadnought")
    assert response.status_code != 404


def test_estimate_learning_curve_endpoint_exists(client):
    """GET /api/business/estimate/learning-curve endpoint exists."""
    response = client.get(
        "/api/business/estimate/learning-curve",
        params={"first_unit_hours": 80.0, "quantity": 5}
    )
    assert response.status_code != 404


# =============================================================================
# Engineering Estimator Endpoints - Response Tests
# =============================================================================

def test_estimate_factors_returns_summary(client):
    """Factors endpoint returns complexity factors."""
    response = client.get("/api/business/estimate/factors")
    assert response.status_code == 200


def test_estimate_wbs_returns_structure(client):
    """WBS endpoint returns work breakdown structure."""
    response = client.get("/api/business/estimate/wbs/acoustic_dreadnought")
    assert response.status_code == 200
    data = response.json()
    assert "instrument_type" in data
    assert "phases" in data


def test_estimate_wbs_unknown_type_returns_error(client):
    """WBS endpoint returns error for unknown type."""
    response = client.get("/api/business/estimate/wbs/unknown_type")
    # Returns 422 (validation error) or 404 (not found) for invalid type
    assert response.status_code in [404, 422]


def test_estimate_learning_curve_returns_projection(client):
    """Learning curve returns projection."""
    response = client.get(
        "/api/business/estimate/learning-curve",
        params={"first_unit_hours": 80.0, "quantity": 5, "learning_rate": 0.85}
    )
    assert response.status_code == 200


# =============================================================================
# Goals Endpoints - Existence
# =============================================================================

def test_goals_list_endpoint_exists(client):
    """GET /api/business/goals endpoint exists."""
    response = client.get("/api/business/goals")
    assert response.status_code != 404


def test_goals_create_endpoint_exists(client):
    """POST /api/business/goals endpoint exists."""
    response = client.post("/api/business/goals", json={
        "name": "Test Goal",
        "instrument_type": "acoustic_dreadnought",
        "target_cost": 500.0,
        "target_hours": 80.0
    })
    assert response.status_code != 404


def test_goals_get_endpoint_exists(client):
    """GET /api/business/goals/{id} endpoint exists."""
    response = client.get("/api/business/goals/test-id")
    # 404 for not found is valid (endpoint exists)
    assert response.status_code in [200, 404]


def test_goals_update_endpoint_exists(client):
    """PATCH /api/business/goals/{id} endpoint exists."""
    response = client.patch("/api/business/goals/test-id", json={
        "target_cost": 450.0
    })
    # 404 for not found is valid (endpoint exists)
    assert response.status_code in [200, 404]


def test_goals_delete_endpoint_exists(client):
    """DELETE /api/business/goals/{id} endpoint exists."""
    response = client.delete("/api/business/goals/test-id")
    # 404 for not found is valid (endpoint exists)
    assert response.status_code in [200, 404]


def test_goals_link_estimate_endpoint_exists(client):
    """POST /api/business/goals/{id}/link-estimate/{estimate_id} endpoint exists."""
    response = client.post("/api/business/goals/test-goal/link-estimate/test-estimate")
    # 404 for not found is valid (endpoint exists)
    assert response.status_code in [200, 404]


# =============================================================================
# Goals Endpoints - Response Tests
# =============================================================================

def test_goals_list_returns_structure(client):
    """Goals list returns expected structure."""
    response = client.get("/api/business/goals")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "goals" in data
    assert "total" in data


def test_goals_create_and_delete(client):
    """Can create and delete a goal."""
    # Create
    create_response = client.post("/api/business/goals", json={
        "name": "Test Goal for Deletion",
        "instrument_type": "acoustic_dreadnought",
        "target_cost": 500.0,
        "target_hours": 80.0
    })
    assert create_response.status_code == 200
    goal_id = create_response.json()["goal"]["id"]

    # Delete
    delete_response = client.delete(f"/api/business/goals/{goal_id}")
    assert delete_response.status_code == 200


def test_goals_update_works(client):
    """Can update a goal."""
    # Create first
    create_response = client.post("/api/business/goals", json={
        "name": "Test Goal for Update",
        "instrument_type": "classical",
        "target_cost": 600.0,
        "target_hours": 100.0
    })
    assert create_response.status_code == 200
    goal_id = create_response.json()["goal"]["id"]

    # Update
    update_response = client.patch(f"/api/business/goals/{goal_id}", json={
        "target_cost": 550.0
    })
    assert update_response.status_code == 200
    assert update_response.json()["goal"]["target_cost"] == 550.0

    # Cleanup
    client.delete(f"/api/business/goals/{goal_id}")


# =============================================================================
# Integration Tests
# =============================================================================

def test_all_business_endpoints_exist(client):
    """All business endpoints exist (not 404)."""
    # GET endpoints
    get_endpoints = [
        "/api/business/health",
        "/api/business/materials",
        "/api/business/bom/templates",
        "/api/business/cogs/labor-rates",
        "/api/business/cogs/overhead",
        "/api/business/pricing/competitors",
        "/api/business/estimate/factors",
        "/api/business/goals",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"GET {path} returned 404"

    # WBS endpoint with param
    response = client.get("/api/business/estimate/wbs/acoustic_dreadnought")
    assert response.status_code != 404, "GET wbs endpoint returned 404"

    # Learning curve with query params
    response = client.get(
        "/api/business/estimate/learning-curve",
        params={"first_unit_hours": 80.0, "quantity": 5}
    )
    assert response.status_code != 404, "GET learning-curve returned 404"


def test_business_workflow_bom_to_cogs_to_pricing(client):
    """Integration: BOM → COGS → Pricing workflow."""
    # 1. Create BOM from template
    bom_response = client.post(
        "/api/business/bom/from-template",
        params={"instrument_type": "acoustic_dreadnought", "instrument_name": "Integration Test"}
    )
    assert bom_response.status_code == 200
    bom = bom_response.json()

    # 2. Calculate COGS
    cogs_response = client.post("/api/business/cogs/calculate", json=bom)
    assert cogs_response.status_code == 200
    cogs = cogs_response.json()
    total_cogs = cogs["total_cogs"]

    # 3. Calculate pricing
    pricing_response = client.post(
        "/api/business/pricing/calculate",
        params={
            "cogs": total_cogs,
            "instrument_name": "Integration Test",
            "instrument_type": "acoustic_dreadnought"
        }
    )
    assert pricing_response.status_code == 200
    pricing = pricing_response.json()
    assert pricing["recommended_price"] > total_cogs


def test_business_workflow_break_even_analysis(client):
    """Integration: Break-even with sensitivity."""
    # Calculate break-even
    breakeven_response = client.post(
        "/api/business/breakeven/calculate",
        params={
            "fixed_costs_monthly": 3000.0,
            "variable_cost_per_unit": 600.0,
            "selling_price_per_unit": 1800.0
        }
    )
    assert breakeven_response.status_code == 200
    breakeven = breakeven_response.json()
    assert breakeven["break_even_units"] > 0

    # Run sensitivity
    sensitivity_response = client.post(
        "/api/business/breakeven/sensitivity",
        params={
            "fixed_costs": 3000.0,
            "variable_cost": 600.0,
            "price": 1800.0
        }
    )
    assert sensitivity_response.status_code == 200
