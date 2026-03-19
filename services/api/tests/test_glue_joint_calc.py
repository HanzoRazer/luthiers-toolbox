"""Tests for glue_joint_calc (CONSTRUCTION-005). Neck and plate joints, gate logic."""

import pytest

from app.calculators.glue_joint_calc import (
    compute_neck_joint,
    compute_plate_joint,
    GlueJointSpec,
    GLUE_HIDE,
    GLUE_PVA,
    GLUE_EPOXY,
    JOINT_BUTT,
    JOINT_LAP,
)


def test_dovetail_hide_glue_green():
    """Dovetail + hide glue → GREEN (800+ mm² > 500 mm² min)."""
    spec = compute_neck_joint(
        joint_type="dovetail",
        neck_heel_width_mm=80.0,
        neck_heel_length_mm=50.0,
        glue_type=GLUE_HIDE,
    )
    assert spec.gate == "GREEN"
    assert spec.joint_type == "dovetail"
    assert spec.glue_surface_mm2 >= 500.0
    assert spec.glue_type == GLUE_HIDE


def test_small_neck_joint_hide_glue_yellow_or_red():
    """Small joint (e.g. scarf) + hide glue → YELLOW or RED."""
    # Use a joint type that has no floor (generic branch) so small dimensions → low surface
    spec = compute_neck_joint(
        joint_type="scarf",
        neck_heel_width_mm=20.0,
        neck_heel_length_mm=10.0,
        glue_type=GLUE_HIDE,
    )
    assert spec.gate in ("YELLOW", "RED")
    assert spec.glue_surface_mm2 < 500.0 or spec.gate == "YELLOW"


def test_bolt_on_green_no_glue_surface():
    """Bolt-on → GREEN, no glue surface."""
    spec = compute_neck_joint(
        joint_type="bolt_on",
        neck_heel_width_mm=80.0,
        neck_heel_length_mm=50.0,
        glue_type=GLUE_HIDE,
    )
    assert spec.gate == "GREEN"
    assert spec.glue_surface_mm2 == 0.0
    assert "bolt-on" in spec.notes[0].lower() or "no glue" in spec.notes[0].lower()


def test_mortise_tenon_pva_surface_adequacy():
    """Mortise-tenon + PVA → check surface adequacy (≥ 400 mm² for PVA)."""
    spec = compute_neck_joint(
        joint_type="mortise_tenon",
        neck_heel_width_mm=70.0,
        neck_heel_length_mm=50.0,
        glue_type=GLUE_PVA,
    )
    assert spec.joint_type == "mortise_tenon"
    assert spec.glue_type == GLUE_PVA
    assert spec.glue_surface_mm2 >= 400.0
    assert spec.gate == "GREEN"


def test_plate_butt_joint_hide_glue_green():
    """Plate butt joint + hide glue → GREEN when surface ≥ 500 mm²."""
    spec = compute_plate_joint(
        joint_type=JOINT_BUTT,
        length_mm=50.0,
        width_mm=20.0,
        glue_type=GLUE_HIDE,
    )
    assert spec.gate == "GREEN"
    assert spec.glue_surface_mm2 == 50.0 * 20.0
    assert spec.glue_surface_mm2 >= 500.0


def test_very_small_plate_joint_red():
    """Very small plate joint → RED (below minimum for any glue type)."""
    spec = compute_plate_joint(
        joint_type=JOINT_BUTT,
        length_mm=10.0,
        width_mm=10.0,
        glue_type=GLUE_HIDE,
    )
    assert spec.gate == "RED"
    assert spec.glue_surface_mm2 == 100.0


def test_epoxy_lower_minimum_threshold():
    """Epoxy joint → lower minimum (300 mm²) so smaller joint can be GREEN."""
    # 320 mm²: above epoxy min (300), below hide min (500)
    spec = compute_plate_joint(
        joint_type=JOINT_BUTT,
        length_mm=20.0,
        width_mm=16.0,
        glue_type=GLUE_EPOXY,
    )
    assert spec.glue_surface_mm2 == 320.0
    assert spec.gate == "GREEN"
    assert spec.glue_type == GLUE_EPOXY


def test_plate_joint_lap_vs_butt_lap_larger_surface():
    """compute_plate_joint lap vs butt → lap can have larger surface (width = overlap)."""
    butt = compute_plate_joint(
        joint_type=JOINT_BUTT,
        length_mm=100.0,
        width_mm=5.0,
        glue_type=GLUE_HIDE,
    )
    lap = compute_plate_joint(
        joint_type=JOINT_LAP,
        length_mm=100.0,
        width_mm=15.0,
        glue_type=GLUE_HIDE,
    )
    assert lap.glue_surface_mm2 > butt.glue_surface_mm2
    assert butt.glue_surface_mm2 == 500.0
    assert lap.glue_surface_mm2 == 1500.0
