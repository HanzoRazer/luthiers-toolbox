"""
Pocket solid mesh tests.

Target: instrument_geometry/tests/test_pocket_solid_mesh.py

Note: These tests require a build_geom_fixture pytest fixture that returns
an InstrumentGeometry instance with an api.get() method.
"""
import pytest
from app.instrument_geometry.api import keys as K


# Skip these tests until the geom fixture is implemented
pytestmark = pytest.mark.skip(reason="Requires build_geom_fixture implementation")


def test_solid_mesh_counts(build_geom_fixture):
    geom = build_geom_fixture()
    
    m = geom.api.get(K.TRUSS_UNION_SOLID_MESH, z_top_mm=0.0, z_floor_mm=-10.0)
    
    v = m["vertex_count"]
    t = m["triangle_count"]
    
    assert v > 0 and t > 0
    # should contain both caps and walls:
    # at least (2 triangles per edge) + (n-2 for top) + (n-2 for bottom)
    # can't know n easily from json without counting, so just check "lots"
    assert t > 20


def test_solid_mesh_earclip(build_geom_fixture):
    geom = build_geom_fixture()
    
    m = geom.api.get(K.TRUSS_UNION_SOLID_MESH, z_top_mm=0.0, z_floor_mm=-10.0, cap_mode="earclip")
    
    assert m["vertex_count"] > 0
    assert m["triangle_count"] > 0
    # should be more triangles than fan mode in many concave cases; but at least nontrivial
    assert m["triangle_count"] > 20
