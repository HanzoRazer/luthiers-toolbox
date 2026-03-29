"""Tests for board_feet and seasonal_movement wrapper."""

from __future__ import annotations

import pytest

from app.woodworking.board_feet import (
    board_feet,
    movement_budget_for_species,
    seasonal_movement,
    wood_weight,
)


def test_board_feet_one_board():
    # 1" x 6" x 96" = 4 bf
    assert abs(board_feet(1, 6, 96, 1) - 4.0) < 1e-6


def test_seasonal_movement_wraps():
    r = seasonal_movement(400.0, "maple", 40.0, 55.0, "tangential")
    assert "movement_mm" in r
    assert r["species"] == "maple"


def test_movement_budget_coefficient():
    r = movement_budget_for_species("maple", "tangential")
    assert r["shrinkage_coefficient_per_pct_mc"] > 0
    assert "wood_movement_calc" in r["source"]


def test_wood_weight_unknown_species():
    r = wood_weight(1, 6, 96, "unknown_wood_xyz")
    assert "note" in r
    assert r["weight_lb"] > 0


def test_unknown_species_seasonal_raises():
    with pytest.raises(ValueError):
        seasonal_movement(100.0, "not_a_real_species_key", 40, 50)
