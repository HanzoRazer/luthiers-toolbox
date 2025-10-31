"""Tests for tonewood module."""

import pytest
from luthiers_toolbox.tonewood import (
    TonewoodDatabase,
    Wood,
    WoodProperties,
    AcousticProperties,
    TonewoodAnalyzer,
)


def test_tonewood_database_creation():
    """Test TonewoodDatabase creation."""
    db = TonewoodDatabase()
    assert len(db.woods) > 0


def test_tonewood_database_get():
    """Test getting wood from database."""
    db = TonewoodDatabase()
    mahogany = db.get_wood("mahogany")
    assert mahogany is not None
    assert mahogany.name == "Mahogany"


def test_tonewood_database_list():
    """Test listing woods."""
    db = TonewoodDatabase()
    woods = db.list_woods()
    assert len(woods) > 0
    assert "mahogany" in woods


def test_tonewood_database_find_by_use():
    """Test finding woods by use."""
    db = TonewoodDatabase()
    body_woods = db.find_by_use("body")
    assert len(body_woods) > 0


def test_tonewood_database_find_by_property():
    """Test finding woods by property."""
    db = TonewoodDatabase()
    woods = db.find_by_property("density", 500, 700)
    assert len(woods) > 0


def test_tonewood_database_compare():
    """Test comparing woods."""
    db = TonewoodDatabase()
    comparison = db.compare_woods("mahogany", "maple")
    assert "wood1" in comparison
    assert "wood2" in comparison


def test_wood_properties():
    """Test WoodProperties methods."""
    props = WoodProperties(
        density=550,
        hardness=800,
        stiffness=10.0,
        workability="good",
    )
    assert props.classify_density() == "medium"
    assert props.classify_hardness() == "medium"


def test_acoustic_properties():
    """Test AcousticProperties methods."""
    acoustics = AcousticProperties(
        frequency_response="bright",
        resonance="high",
        damping="low",
        tonal_character="test",
    )
    assert acoustics.get_resonance_score() == 0.75
    assert acoustics.get_damping_score() == 0.25


def test_tonewood_analyzer_creation():
    """Test TonewoodAnalyzer creation."""
    analyzer = TonewoodAnalyzer()
    assert analyzer.database is not None


def test_tonewood_analyzer_combination():
    """Test analyzing wood combination."""
    analyzer = TonewoodAnalyzer()
    profile = analyzer.analyze_wood_combination(
        "mahogany", "maple", "rosewood"
    )
    assert profile is not None
    assert profile.body_wood == "Mahogany"
    assert profile.neck_wood == "Maple"


def test_tonewood_analyzer_recommendations():
    """Test style recommendations."""
    analyzer = TonewoodAnalyzer()
    recs = analyzer.recommend_for_style("rock")
    assert "body" in recs
    assert "neck" in recs
    assert "fretboard" in recs


def test_tonewood_analyzer_alternatives():
    """Test finding alternatives."""
    analyzer = TonewoodAnalyzer()
    alternatives = analyzer.find_alternatives("mahogany", "tone")
    assert isinstance(alternatives, list)
