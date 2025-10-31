"""Tests for costing module."""

import pytest
from luthiers_toolbox.costing import (
    MaterialCost,
    MaterialDatabase,
    LaborCost,
    LaborEstimator,
    CostEstimator,
)


def test_material_cost_creation():
    """Test MaterialCost creation."""
    mat = MaterialCost("mahogany", 15.0, "board_foot")
    assert mat.name == "mahogany"
    assert mat.unit_price == 15.0


def test_material_cost_calculation():
    """Test material cost calculation."""
    mat = MaterialCost("mahogany", 15.0, "board_foot", waste_factor=1.2)
    cost = mat.calculate_cost(2.0)
    assert cost == 15.0 * 2.0 * 1.2


def test_material_database_creation():
    """Test MaterialDatabase creation."""
    db = MaterialDatabase()
    assert len(db.materials) > 0


def test_material_database_get():
    """Test getting materials from database."""
    db = MaterialDatabase()
    mahogany = db.get_material("mahogany")
    assert mahogany is not None
    assert mahogany.name == "mahogany"


def test_material_database_board_feet():
    """Test board feet calculation."""
    db = MaterialDatabase()
    bf = db.calculate_board_feet(12, 12, 1)
    assert bf == 1.0


def test_labor_cost_creation():
    """Test LaborCost creation."""
    labor = LaborCost("test_task", 2.0, 50.0)
    assert labor.task == "test_task"
    assert labor.hours == 2.0


def test_labor_cost_calculation():
    """Test labor cost calculation."""
    labor = LaborCost("test_task", 2.0, 50.0)
    cost = labor.calculate_cost()
    assert cost == 100.0


def test_labor_estimator_creation():
    """Test LaborEstimator creation."""
    estimator = LaborEstimator(hourly_rate=50.0)
    assert estimator.hourly_rate == 50.0


def test_labor_estimator_estimate():
    """Test labor estimation."""
    estimator = LaborEstimator(hourly_rate=50.0)
    labor = estimator.estimate_task("body_rough_cut")
    assert labor.hours > 0


def test_cost_estimator_creation():
    """Test CostEstimator creation."""
    estimator = CostEstimator()
    assert estimator.material_db is not None
    assert estimator.labor_estimator is not None


def test_cost_estimator_guitar():
    """Test guitar cost estimation."""
    estimator = CostEstimator()
    project = estimator.estimate_guitar(
        body_wood="mahogany",
        neck_wood="maple",
        fretboard_wood="rosewood",
    )
    assert project is not None
    breakdown = project.get_breakdown()
    assert breakdown["total"] > 0
    assert breakdown["materials"] > 0
    assert breakdown["labor"] > 0
