"""Smoke tests for Art Presets Aggregate endpoint (wired to art_presets_store.py)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_presets_aggregate_endpoint_exists(client):
    """GET /api/art/presets_aggregate endpoint exists."""
    response = client.get("/api/art/presets_aggregate")
    assert response.status_code != 404


# =============================================================================
# Response Structure
# =============================================================================

def test_presets_aggregate_returns_200(client):
    """GET /api/art/presets_aggregate returns 200."""
    response = client.get("/api/art/presets_aggregate")
    assert response.status_code == 200


def test_presets_aggregate_returns_list(client):
    """GET /api/art/presets_aggregate returns a list."""
    response = client.get("/api/art/presets_aggregate")
    data = response.json()
    assert isinstance(data, list)


def test_presets_aggregate_accepts_lane_filter(client):
    """GET /api/art/presets_aggregate accepts lane query parameter."""
    response = client.get("/api/art/presets_aggregate?lane=rosette")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# =============================================================================
# Response Fields
# =============================================================================

def test_presets_aggregate_fields_when_presets_exist(client, monkeypatch):
    """Preset aggregate response has all required fields."""
    # Mock list_presets to return a test preset
    mock_presets = [
        {
            "id": "test_preset_001",
            "name": "Test Rosette",
            "lane": "rosette",
            "params": {
                "parent_id": None,
                "rationale": "Test preset",
                "source": "manual",
            },
            "created_at": 1700000000.0,
        }
    ]
    monkeypatch.setattr(
        "app.routers.art.root_art_router.list_presets",
        lambda lane=None: mock_presets
    )

    response = client.get("/api/art/presets_aggregate")
    data = response.json()

    assert len(data) == 1
    preset = data[0]

    # Required fields from schema
    assert "preset_id" in preset
    assert "preset_name" in preset
    assert "lane" in preset
    assert "parent_id" in preset
    assert "parent_name" in preset
    assert "diff_summary" in preset
    assert "rationale" in preset
    assert "source" in preset

    # Stats fields
    assert "job_count" in preset
    assert "risk_count" in preset
    assert "critical_count" in preset
    assert "avg_total_length" in preset
    assert "avg_total_lines" in preset
    assert "health_color" in preset
    assert "trend_direction" in preset
    assert "trend_delta" in preset


def test_presets_aggregate_stats_are_numeric(client, monkeypatch):
    """Preset aggregate stats fields are numeric."""
    mock_presets = [
        {
            "id": "test_preset_002",
            "name": "Adaptive Test",
            "lane": "adaptive",
            "params": {},
            "created_at": 1700000000.0,
        }
    ]
    monkeypatch.setattr(
        "app.routers.art.root_art_router.list_presets",
        lambda lane=None: mock_presets
    )

    response = client.get("/api/art/presets_aggregate")
    data = response.json()

    assert len(data) == 1
    preset = data[0]

    assert isinstance(preset["job_count"], (int, float))
    assert isinstance(preset["risk_count"], (int, float))
    assert isinstance(preset["critical_count"], (int, float))
    assert isinstance(preset["avg_total_length"], (int, float))
    assert isinstance(preset["avg_total_lines"], (int, float))
    assert isinstance(preset["trend_delta"], (int, float))


def test_presets_aggregate_health_color_valid(client, monkeypatch):
    """Preset aggregate health_color is a valid value."""
    mock_presets = [
        {
            "id": "test_preset_003",
            "name": "Relief Test",
            "lane": "relief",
            "params": {},
            "created_at": 1700000000.0,
        }
    ]
    monkeypatch.setattr(
        "app.routers.art.root_art_router.list_presets",
        lambda lane=None: mock_presets
    )

    response = client.get("/api/art/presets_aggregate")
    data = response.json()

    assert len(data) == 1
    preset = data[0]
    assert preset["health_color"] in ("green", "yellow", "red")


def test_presets_aggregate_trend_direction_valid(client, monkeypatch):
    """Preset aggregate trend_direction is a valid value."""
    mock_presets = [
        {
            "id": "test_preset_004",
            "name": "Another Test",
            "lane": "rosette",
            "params": {},
            "created_at": 1700000000.0,
        }
    ]
    monkeypatch.setattr(
        "app.routers.art.root_art_router.list_presets",
        lambda lane=None: mock_presets
    )

    response = client.get("/api/art/presets_aggregate")
    data = response.json()

    assert len(data) == 1
    preset = data[0]
    assert preset["trend_direction"] in ("up", "down", "flat")


# =============================================================================
# Lane Filtering
# =============================================================================

def test_presets_aggregate_lane_filter_works(client, monkeypatch):
    """Lane filter correctly filters presets."""
    mock_presets_all = [
        {"id": "rosette_001", "name": "Rosette 1", "lane": "rosette", "params": {}, "created_at": 1700000000.0},
        {"id": "adaptive_001", "name": "Adaptive 1", "lane": "adaptive", "params": {}, "created_at": 1700000001.0},
        {"id": "all_001", "name": "All Lanes", "lane": "all", "params": {}, "created_at": 1700000002.0},
    ]

    def mock_list_presets(lane=None):
        if lane:
            return [p for p in mock_presets_all if p.get("lane") in (lane, "all")]
        return mock_presets_all

    monkeypatch.setattr(
        "app.routers.art.root_art_router.list_presets",
        mock_list_presets
    )

    # Request all
    response = client.get("/api/art/presets_aggregate")
    data = response.json()
    assert len(data) == 3

    # Request rosette only
    response = client.get("/api/art/presets_aggregate?lane=rosette")
    data = response.json()
    assert len(data) == 2  # rosette + all
    lanes = [p["lane"] for p in data]
    assert "rosette" in lanes
    assert "all" in lanes


# =============================================================================
# Empty State
# =============================================================================

def test_presets_aggregate_empty_when_no_presets(client, monkeypatch):
    """Returns empty list when no presets exist."""
    monkeypatch.setattr(
        "app.routers.art.root_art_router.list_presets",
        lambda lane=None: []
    )

    response = client.get("/api/art/presets_aggregate")
    data = response.json()
    assert data == []


# =============================================================================
# Lineage Fields
# =============================================================================

def test_presets_aggregate_lineage_fields(client, monkeypatch):
    """Preset with parent has lineage fields populated."""
    mock_presets = [
        {
            "id": "child_preset",
            "name": "Child Preset",
            "lane": "rosette",
            "params": {
                "parent_id": "parent_preset",
                "parent_name": "Parent Preset",
                "diff_summary": "Changed stepover by 10%",
                "rationale": "Better surface finish",
                "source": "auto_tune",
            },
            "created_at": 1700000000.0,
        }
    ]
    monkeypatch.setattr(
        "app.routers.art.root_art_router.list_presets",
        lambda lane=None: mock_presets
    )

    response = client.get("/api/art/presets_aggregate")
    data = response.json()

    assert len(data) == 1
    preset = data[0]

    assert preset["preset_id"] == "child_preset"
    assert preset["parent_id"] == "parent_preset"
    assert preset["parent_name"] == "Parent Preset"
    assert preset["diff_summary"] == "Changed stepover by 10%"
    assert preset["rationale"] == "Better surface finish"
    assert preset["source"] == "auto_tune"
