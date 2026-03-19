"""
Tests for Neck Block and Tail Block Calculator (GEOMETRY-005)
"""

import pytest
from fastapi.testclient import TestClient

from app.calculators.neck_block_calc import (
    compute_neck_block,
    compute_tail_block,
    compute_both_blocks,
    list_body_styles,
    get_default_side_depths,
    BlockSpec,
)
from app.main import app

client = TestClient(app)


# ─── Unit Tests ───────────────────────────────────────────────────────────────

class TestComputeNeckBlock:
    """Tests for compute_neck_block function."""

    def test_neck_block_height_equals_side_depth(self):
        """Neck block height should equal side depth at neck."""
        spec = compute_neck_block(
            side_depth_at_neck_mm=100.0,
            neck_heel_width_mm=56.0,
            body_style="dreadnought",
        )
        assert spec.height_mm == 100.0

    def test_neck_block_width_includes_margin(self):
        """Neck block width should be heel width + 12mm (6mm each side)."""
        spec = compute_neck_block(
            side_depth_at_neck_mm=100.0,
            neck_heel_width_mm=56.0,
            body_style="dreadnought",
        )
        assert spec.width_mm == 68.0  # 56 + 12

    def test_neck_block_grain_is_vertical(self):
        """Neck block grain should be vertical for strength."""
        spec = compute_neck_block(
            side_depth_at_neck_mm=100.0,
            neck_heel_width_mm=56.0,
            body_style="dreadnought",
        )
        assert spec.grain_orientation == "vertical"

    def test_neck_block_green_gate_for_good_dimensions(self):
        """Good dimensions should produce GREEN gate."""
        spec = compute_neck_block(
            side_depth_at_neck_mm=100.0,
            neck_heel_width_mm=56.0,
            body_style="dreadnought",
        )
        assert spec.gate == "GREEN"


class TestComputeTailBlock:
    """Tests for compute_tail_block function."""

    def test_tail_block_height_equals_side_depth(self):
        """Tail block height should equal side depth at tail."""
        spec = compute_tail_block(
            side_depth_at_tail_mm=105.0,
            body_style="dreadnought",
        )
        assert spec.height_mm == 105.0

    def test_tail_block_grain_is_horizontal(self):
        """Tail block grain should be horizontal for end pin support."""
        spec = compute_tail_block(
            side_depth_at_tail_mm=105.0,
            body_style="dreadnought",
        )
        assert spec.grain_orientation == "horizontal"

    def test_tail_block_width_varies_by_body_style(self):
        """Tail block width should differ by body style."""
        dread = compute_tail_block(105.0, "dreadnought")
        parlor = compute_tail_block(90.0, "parlor")
        assert dread.width_mm > parlor.width_mm


class TestGateLogic:
    """Tests for GREEN/YELLOW/RED gate logic."""

    def test_small_neck_block_red_gate(self):
        """Very small neck block should be RED."""
        spec = compute_neck_block(
            side_depth_at_neck_mm=60.0,  # Too short
            neck_heel_width_mm=40.0,  # Too narrow
            body_style="dreadnought",
        )
        assert spec.gate == "RED"


# ─── API Endpoint Tests ───────────────────────────────────────────────────────

class TestBlocksEndpoint:
    """Tests for POST /api/instrument/blocks endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.post(
            "/api/instrument/blocks",
            json={"body_style": "dreadnought"},
        )
        assert response.status_code == 200

    def test_endpoint_returns_both_blocks(self):
        """Response should include both neck and tail blocks."""
        response = client.post(
            "/api/instrument/blocks",
            json={"body_style": "om_000"},
        )
        data = response.json()
        assert "neck" in data
        assert "tail" in data
        assert data["neck"]["block_type"] == "neck"
        assert data["tail"]["block_type"] == "tail"

    def test_endpoint_with_custom_dimensions(self):
        """Endpoint should accept custom dimensions."""
        response = client.post(
            "/api/instrument/blocks",
            json={
                "body_style": "dreadnought",
                "neck_heel_width_mm": 60.0,
                "side_depth_at_neck_mm": 102.0,
                "side_depth_at_tail_mm": 108.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["neck"]["height_mm"] == 102.0
        assert data["tail"]["height_mm"] == 108.0


class TestBlockOptionsEndpoint:
    """Tests for GET /api/instrument/blocks/options endpoint."""

    def test_endpoint_exists_and_returns_200(self):
        """Endpoint should exist and return 200."""
        response = client.get("/api/instrument/blocks/options")
        assert response.status_code == 200

    def test_endpoint_returns_body_styles(self):
        """Response should include body styles list."""
        response = client.get("/api/instrument/blocks/options")
        data = response.json()
        assert "body_styles" in data
        assert "dreadnought" in data["body_styles"]
        assert "parlor" in data["body_styles"]
        assert len(data["body_styles"]) >= 5
