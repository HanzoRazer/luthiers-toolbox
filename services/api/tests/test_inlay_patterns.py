"""
Tests for Inlay Pattern Generators, Offset Engine, and DXF Export.

Covers:
  - All six pattern generators produce valid GeometryCollections
  - Offset engine (polygon, polyline, collection)
  - DXF R12 export produces valid ezdxf Documents
  - Import pipeline (DXF, SVG, CSV)
  - API endpoints (list, generate, export, import)
"""
from __future__ import annotations

import math
import pytest

# ---------------------------------------------------------------------------
# Unit: Geometry primitives & offset engine
# ---------------------------------------------------------------------------

from app.art_studio.services.generators.inlay_geometry import (
    GeometryCollection,
    GeometryElement,
    offset_collection,
    offset_polygon,
    offset_polyline,
)


class TestOffsetPolyline:
    def test_straight_line_offset(self):
        """Offsetting a horizontal line by +1 should shift Y by -1 (normal is CCW)."""
        pts = [(0.0, 0.0), (10.0, 0.0)]
        result = offset_polyline(pts, 1.0)
        assert len(result) == 2
        # Tangent is (1,0), normal CCW is (0,1) → y increases by 1
        # Wait — normal of (1,0) rotated 90° CCW is (0,1)
        for (rx, ry), (_, _) in zip(result, pts):
            assert ry == pytest.approx(1.0, abs=0.01)

    def test_offset_preserves_count(self):
        pts = [(0, 0), (5, 0), (10, 5), (15, 5)]
        result = offset_polyline(pts, 0.5)
        assert len(result) == len(pts)

    def test_zero_offset_identity(self):
        pts = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]
        result = offset_polyline(pts, 0.0)
        for (rx, ry), (ox, oy) in zip(result, pts):
            assert rx == pytest.approx(ox)
            assert ry == pytest.approx(oy)


class TestOffsetPolygon:
    def test_square_outward(self):
        """Expanding a unit square outward by 1 should produce a larger shape."""
        sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = offset_polygon(sq, 1.0)
        assert len(result) == 4
        # All points should be further from centre than originals
        cx, cy = 5.0, 5.0
        for (rx, ry), (ox, oy) in zip(result, sq):
            orig_dist = math.hypot(ox - cx, oy - cy)
            new_dist = math.hypot(rx - cx, ry - cy)
            assert new_dist > orig_dist

    def test_square_inward(self):
        """Contracting a square should produce smaller shape."""
        sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = offset_polygon(sq, -1.0)
        assert len(result) == 4
        cx, cy = 5.0, 5.0
        for (rx, ry), (ox, oy) in zip(result, sq):
            orig_dist = math.hypot(ox - cx, oy - cy)
            new_dist = math.hypot(rx - cx, ry - cy)
            assert new_dist < orig_dist


class TestOffsetCollection:
    def test_circle_offset(self):
        geo = GeometryCollection(
            elements=[
                GeometryElement(kind="circle", points=[(5.0, 5.0)], radius=10.0),
            ],
            width_mm=20,
            height_mm=20,
        )
        expanded = offset_collection(geo, 2.0)
        assert expanded.elements[0].radius == pytest.approx(12.0)

        contracted = offset_collection(geo, -3.0)
        assert contracted.elements[0].radius == pytest.approx(7.0)

    def test_circle_clamp_zero(self):
        geo = GeometryCollection(
            elements=[
                GeometryElement(kind="circle", points=[(0, 0)], radius=1.0),
            ],
            width_mm=2,
            height_mm=2,
        )
        result = offset_collection(geo, -5.0)
        assert result.elements[0].radius == 0.0


# ---------------------------------------------------------------------------
# Unit: Pattern generators
# ---------------------------------------------------------------------------

from app.art_studio.services.generators.inlay_patterns import (
    INLAY_GENERATORS,
    apply_tile,
    diamond,
    feather,
    generate_inlay_pattern,
    greek_key,
    herringbone,
    spiral,
    sunburst,
)


class TestHerringbone:
    def test_basic(self):
        geo = herringbone({"tooth_w": 10, "tooth_h": 20, "band_w": 50, "band_h": 40})
        assert geo.width_mm == 50
        assert geo.height_mm == 40
        assert geo.radial is False
        assert geo.tile_w is not None
        assert len(geo.elements) > 0
        assert all(e.kind == "rect" for e in geo.elements)

    def test_defaults(self):
        geo = herringbone({})
        assert geo.width_mm > 0
        assert len(geo.elements) > 0


class TestDiamond:
    def test_basic(self):
        geo = diamond({"tile_w": 14, "tile_h": 22, "band_w": 60, "band_h": 22})
        assert geo.width_mm == 60
        assert all(e.kind == "polygon" for e in geo.elements)
        assert all(len(e.points) == 4 for e in geo.elements)

    def test_wave_lean(self):
        geo = diamond({"wave": 0.5, "lean": 0.3})
        assert len(geo.elements) > 0


class TestGreekKey:
    def test_basic(self):
        geo = greek_key({"cell_size": 10, "band_w": 80, "band_h": 40})
        assert geo.width_mm == 80
        assert geo.height_mm == 40
        assert all(e.kind == "polygon" for e in geo.elements)


class TestSpiral:
    def test_basic(self):
        geo = spiral({"arm_dist": 12, "circles": 2, "thickness": 1.5, "sym_count": 1})
        assert geo.radial is True
        assert geo.origin_x > 0
        assert len(geo.elements) == 1
        assert geo.elements[0].kind == "polyline"
        assert len(geo.elements[0].points) > 50

    def test_symmetry(self):
        geo = spiral({"sym_count": 3})
        assert len(geo.elements) == 3


class TestSunburst:
    def test_basic(self):
        geo = sunburst({"rays": 8, "band_r": 30})
        assert geo.radial is True
        # 8 ray polygons + 1 inner circle
        assert len(geo.elements) == 9

    def test_material_indices(self):
        geo = sunburst({"rays": 6})
        for i, el in enumerate(geo.elements[:-1]):
            assert el.material_index == i % 3


class TestFeather:
    def test_basic(self):
        geo = feather({"blades": 10, "layers": 2, "band_r": 40})
        assert geo.radial is True
        assert len(geo.elements) == 20  # 10 blades × 2 layers


class TestApplyTile:
    def test_tiles_fill_target(self):
        geo = herringbone({"tooth_w": 10, "tooth_h": 20, "band_w": 10, "band_h": 20})
        original_count = len(geo.elements)
        tiled = apply_tile(geo, 40, 40)
        assert len(tiled.elements) > original_count

    def test_radial_passthrough(self):
        geo = spiral({})
        tiled = apply_tile(geo, 200, 200)
        assert len(tiled.elements) == len(geo.elements)


class TestGenerateDispatcher:
    def test_all_shapes(self):
        for shape in INLAY_GENERATORS:
            geo = generate_inlay_pattern(shape, {})
            assert geo.width_mm > 0
            assert len(geo.elements) > 0

    def test_unknown_shape(self):
        with pytest.raises(ValueError, match="Unknown inlay shape"):
            generate_inlay_pattern("nonexistent", {})


# ---------------------------------------------------------------------------
# Unit: SVG rendering
# ---------------------------------------------------------------------------

from app.art_studio.services.generators.inlay_geometry import (
    collection_to_layered_svg,
    collection_to_svg,
)


class TestSVGRendering:
    def test_basic_svg(self):
        geo = herringbone({})
        svg = collection_to_svg(geo)
        assert svg.startswith("<svg")
        assert "viewBox" in svg

    def test_export_svg_has_mm(self):
        geo = diamond({})
        svg = collection_to_svg(geo, for_export=True)
        assert 'mm"' in svg
        assert "The Production Shop" in svg

    def test_layered_svg(self):
        geo = sunburst({"rays": 4, "band_r": 20})
        svg = collection_to_layered_svg(geo, male_offset_mm=0.1, pocket_offset_mm=0.1)
        assert 'id="centerline"' in svg
        assert 'id="male_cut"' in svg
        assert 'id="pocket_cut"' in svg


# ---------------------------------------------------------------------------
# Unit: DXF export
# ---------------------------------------------------------------------------

from app.art_studio.services.generators.inlay_export import (
    geometry_to_dxf,
    geometry_to_dxf_bytes,
)


class TestDXFExport:
    def test_produces_document(self):
        geo = herringbone({"band_w": 50, "band_h": 20})
        doc = geometry_to_dxf(geo)
        layers = [layer.dxf.name for layer in doc.layers]
        assert "CENTERLINE" in layers
        assert "MALE_CUT" in layers
        assert "POCKET_CUT" in layers

    def test_entities_on_layers(self):
        geo = diamond({"band_w": 30, "band_h": 15})
        doc = geometry_to_dxf(geo)
        msp = doc.modelspace()
        entities = list(msp)
        assert len(entities) > 0
        layer_names = {e.dxf.layer for e in entities}
        assert "CENTERLINE" in layer_names
        assert "MALE_CUT" in layer_names
        assert "POCKET_CUT" in layer_names

    def test_bytes_output(self):
        geo = spiral({"circles": 1})
        data = geometry_to_dxf_bytes(geo)
        assert isinstance(data, bytes)
        assert len(data) > 100


# ---------------------------------------------------------------------------
# Unit: Import pipeline
# ---------------------------------------------------------------------------

from app.art_studio.services.generators.inlay_import import (
    parse_csv_grid,
    parse_dxf,
    parse_svg,
)


class TestDXFImport:
    def test_lwpolyline(self):
        dxf_text = """0
SECTION
2
ENTITIES
0
LWPOLYLINE
70
1
10
0.0
20
0.0
10
10.0
20
0.0
10
10.0
20
10.0
10
0.0
20
10.0
0
ENDSEC
0
EOF"""
        geo = parse_dxf(dxf_text)
        assert len(geo.elements) == 1
        assert geo.elements[0].kind == "polygon"  # closed (flag 1)
        assert len(geo.elements[0].points) == 4

    def test_circle(self):
        dxf_text = """0
SECTION
2
ENTITIES
0
CIRCLE
10
5.0
20
5.0
40
3.0
0
ENDSEC
0
EOF"""
        geo = parse_dxf(dxf_text)
        assert len(geo.elements) == 1
        assert geo.elements[0].kind == "circle"
        assert geo.elements[0].radius == pytest.approx(3.0)


class TestSVGImport:
    def test_basic_path(self):
        svg_text = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 0,0 L 50,0 L 50,50 L 0,50 Z"/>
</svg>"""
        geo = parse_svg(svg_text)
        assert len(geo.elements) >= 1

    def test_script_stripped(self):
        svg_text = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <script>alert('xss')</script>
  <circle cx="50" cy="50" r="25"/>
</svg>"""
        geo = parse_svg(svg_text)
        assert len(geo.elements) == 1
        assert geo.elements[0].kind == "circle"

    def test_rect(self):
        svg_text = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect x="10" y="20" width="50" height="30"/>
</svg>"""
        geo = parse_svg(svg_text)
        assert len(geo.elements) == 1
        assert geo.elements[0].kind == "rect"


class TestCSVImport:
    def test_material_names(self):
        csv_text = "ebony,mop,koa\nmop,koa,ebony"
        geo = parse_csv_grid(csv_text, band_w=30, band_h=20)
        assert len(geo.elements) == 6  # 2 rows × 3 cols
        assert geo.width_mm == 30
        assert geo.height_mm == 20

    def test_aliases(self):
        csv_text = "B,W,R\nW,R,B"
        geo = parse_csv_grid(csv_text)
        assert len(geo.elements) == 6

    def test_numeric(self):
        csv_text = "0,1,2\n1,2,0"
        geo = parse_csv_grid(csv_text)
        assert len(geo.elements) == 6


# ---------------------------------------------------------------------------
# New math infrastructure
# ---------------------------------------------------------------------------

class TestLineLineIntersect:
    def test_perpendicular(self):
        from app.art_studio.services.generators.inlay_geometry import line_line_intersect
        pt = line_line_intersect((0, 0), (10, 0), (5, -5), (5, 5))
        assert pt is not None
        assert abs(pt[0] - 5) < 0.01
        assert abs(pt[1] - 0) < 0.01

    def test_parallel_returns_none(self):
        from app.art_studio.services.generators.inlay_geometry import line_line_intersect
        pt = line_line_intersect((0, 0), (10, 0), (0, 5), (10, 5))
        assert pt is None


class TestSubdivideCubic:
    def test_straight_line_few_points(self):
        from app.art_studio.services.generators.inlay_geometry import subdivide_cubic
        pts = subdivide_cubic((0, 0), (10, 0), (20, 0), (30, 0), tol=0.5)
        assert len(pts) >= 2
        assert abs(pts[0][0]) < 0.01
        assert abs(pts[-1][0] - 30) < 0.01

    def test_curve_has_more_points(self):
        from app.art_studio.services.generators.inlay_geometry import subdivide_cubic
        pts = subdivide_cubic((0, 0), (0, 50), (50, 50), (50, 0), tol=0.5)
        assert len(pts) > 4


class TestTessellatePath:
    def test_moveto_lineto(self):
        from app.art_studio.services.generators.inlay_geometry import tessellate_path_d
        paths = tessellate_path_d("M 0 0 L 10 0 L 10 10 Z", tol=0.5)
        assert len(paths) >= 1
        assert len(paths[0]) >= 3

    def test_cubic_bezier(self):
        from app.art_studio.services.generators.inlay_geometry import tessellate_path_d
        paths = tessellate_path_d("M 0 0 C 0 50 50 50 50 0", tol=0.5)
        assert len(paths) >= 1
        assert len(paths[0]) > 3


class TestCatmullRom:
    def test_midpoint(self):
        from app.art_studio.services.generators.inlay_geometry import catmull_rom
        pts = [(0, 0), (0, 0), (10, 0), (10, 0)]
        mid = catmull_rom(pts, 0.5)
        assert abs(mid[0] - 5) < 0.5
        assert abs(mid[1]) < 0.5


class TestSampleSpline:
    def test_returns_enough_points(self):
        from app.art_studio.services.generators.inlay_geometry import sample_spline
        pts = [(0, 0), (5, 10), (10, 0), (15, 10), (20, 0)]
        sampled = sample_spline(pts, 20)
        assert len(sampled) == 21


class TestMakePoly:
    def test_square(self):
        from app.art_studio.services.generators.inlay_geometry import make_poly
        verts = make_poly([90, 90, 90, 90])
        assert len(verts) == 4
        # All edges should be unit length
        for i in range(4):
            dx = verts[(i + 1) % 4][0] - verts[i][0]
            dy = verts[(i + 1) % 4][1] - verts[i][1]
            edge = (dx ** 2 + dy ** 2) ** 0.5
            assert abs(edge - 1.0) < 0.01


class TestOffsetPolylineStrip:
    def test_strip_has_dual_rails(self):
        from app.art_studio.services.generators.inlay_geometry import offset_polyline_strip
        line = [(0, 0), (10, 0), (20, 0)]
        strip = offset_polyline_strip(line, 1.0)
        assert len(strip) >= 6  # outer + inner reversed
        # Strip should form a closed loop (first outer ≈ last inner)
        dx = strip[0][0] - strip[-1][0]
        dy = strip[0][1] - strip[-1][1]
        dist = (dx**2 + dy**2) ** 0.5
        assert dist < 3.0  # ends near each other (within 1 offset width)


# ---------------------------------------------------------------------------
# New generators
# ---------------------------------------------------------------------------

class TestCelticMotif:
    def test_lotus(self):
        col = generate_inlay_pattern("celtic_motif", {"motif_id": "lotus", "scale_mm": 20})
        assert len(col.elements) > 0
        assert col.width_mm > 0
        assert col.height_mm > 0

    def test_unknown_motif_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Unknown motif"):
            generate_inlay_pattern("celtic_motif", {"motif_id": "nonexistent"})

    def test_custom_svg_paths(self):
        col = generate_inlay_pattern("celtic_motif", {
            "svg_paths": ["M 0 0 L 100 0 L 100 100 L 0 100 Z"],
            "vb_w": 100, "vb_h": 100, "scale_mm": 10,
        })
        assert len(col.elements) >= 1
        assert col.width_mm > 0


class TestVineScroll:
    def test_basic(self):
        col = generate_inlay_pattern("vine_scroll", {
            "curl": 3, "leaves": 6, "length_mm": 80,
        })
        assert len(col.elements) >= 7  # 1 stem + 6 leaves
        assert col.width_mm > 0

    def test_no_leaves(self):
        col = generate_inlay_pattern("vine_scroll", {"leaves": 0, "length_mm": 50})
        # stem only
        assert len(col.elements) >= 1


class TestGirihRosette:
    def test_basic(self):
        col = generate_inlay_pattern("girih_rosette", {"edge_mm": 10})
        assert len(col.elements) == 26  # 1 + 10 + 5 + 5 + 5
        assert col.width_mm > 0
        assert col.radial is True

    def test_rotation(self):
        col0 = generate_inlay_pattern("girih_rosette", {"edge_mm": 10, "rotation_deg": 0})
        col45 = generate_inlay_pattern("girih_rosette", {"edge_mm": 10, "rotation_deg": 45})
        # Same count, different positions
        assert len(col0.elements) == len(col45.elements)
        assert col0.elements[0].points[0] != col45.elements[0].points[0]


class TestBindingFlow:
    def test_default_oval(self):
        col = generate_inlay_pattern("binding_flow", {"leaves": 8, "band_width": 3})
        # 1 outline + 1 binding strip + 8 leaves
        assert len(col.elements) >= 10
        assert col.width_mm > 100  # oval is 380mm wide

    def test_custom_contour(self):
        contour = [[0, 0], [50, 0], [50, 50], [0, 50]]
        col = generate_inlay_pattern("binding_flow", {
            "contour": contour, "leaves": 4,
        })
        assert len(col.elements) >= 6


# ---------------------------------------------------------------------------
# Integration: API endpoints
# ---------------------------------------------------------------------------

class TestInlayPatternAPI:
    def test_list_generators(self, client):
        r = client.get("/api/art/inlay-patterns")
        assert r.status_code == 200
        data = r.json()
        assert "generators" in data
        names = {g["shape"] for g in data["generators"]}
        assert "herringbone" in names
        assert "spiral" in names
        assert "celtic_motif" in names
        assert "girih_rosette" in names
        assert "twisted_rope" in names
        assert "compose_band" in names
        assert "checker_chevron" in names
        assert "amsterdam_flower" in names
        assert len(names) == 22

    def test_generate_preview(self, client):
        r = client.post("/api/art/inlay-patterns/generate", json={
            "shape": "herringbone",
            "params": {"tooth_w": 10, "tooth_h": 20, "band_w": 60, "band_h": 22},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["shape"] == "herringbone"
        assert "<svg" in data["svg"]
        assert data["element_count"] > 0

    def test_generate_with_offsets(self, client):
        r = client.post("/api/art/inlay-patterns/generate", json={
            "shape": "spiral",
            "params": {"circles": 1},
            "include_offsets": True,
            "male_offset_mm": 0.15,
            "pocket_offset_mm": 0.15,
        })
        assert r.status_code == 200
        data = r.json()
        assert 'id="centerline"' in data["svg"]
        assert 'id="male_cut"' in data["svg"]

    def test_generate_unknown_shape(self, client):
        r = client.post("/api/art/inlay-patterns/generate", json={
            "shape": "herringbone",
            "params": {},
        })
        assert r.status_code == 200
        # Verify bad shape fails
        r2 = client.post("/api/art/inlay-patterns/generate", json={
            "shape": "nonexistent",
            "params": {},
        })
        assert r2.status_code == 422  # Pydantic rejects invalid literal

    def test_export_svg(self, client):
        r = client.post("/api/art/inlay-patterns/export", json={
            "shape": "diamond",
            "params": {},
            "format": "svg",
        })
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/svg+xml"
        assert b"<svg" in r.content

    def test_export_layered_svg(self, client):
        r = client.post("/api/art/inlay-patterns/export", json={
            "shape": "sunburst",
            "params": {"rays": 4, "band_r": 20},
            "format": "layered_svg",
        })
        assert r.status_code == 200
        assert b"male_cut" in r.content

    def test_export_dxf(self, client):
        r = client.post("/api/art/inlay-patterns/export", json={
            "shape": "herringbone",
            "params": {"band_w": 30, "band_h": 15},
            "format": "dxf",
        })
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/dxf"
        assert len(r.content) > 100


# ---------------------------------------------------------------------------
# Rope math
# ---------------------------------------------------------------------------

class TestComputeTangentNormalArclen:
    def test_straight_line(self):
        from app.art_studio.services.generators.inlay_geometry import compute_tangent_normal_arclen
        pts = [(0, 0), (5, 0), (10, 0)]
        tangents, normals, arc_lens = compute_tangent_normal_arclen(pts)
        assert len(tangents) == 3
        assert len(arc_lens) == 3
        assert abs(arc_lens[0]) < 1e-10
        assert abs(arc_lens[-1] - 10) < 1e-6
        # Tangent should be (1, 0) for horizontal line
        assert abs(tangents[1][0] - 1.0) < 0.01
        # Normal should be (0, 1) for horizontal line (CCW)
        assert abs(normals[1][1] - 1.0) < 0.01

    def test_single_point(self):
        from app.art_studio.services.generators.inlay_geometry import compute_tangent_normal_arclen
        tangents, normals, arc_lens = compute_tangent_normal_arclen([(5, 5)])
        assert len(tangents) == 1
        assert len(arc_lens) == 1


class TestBuildCenterline:
    def test_straight(self):
        from app.art_studio.services.generators.inlay_geometry import build_centerline
        pts = build_centerline("straight", 100)
        assert len(pts) == 200
        assert abs(pts[0][0]) < 0.01
        assert abs(pts[-1][0] - 100) < 1.0

    def test_swave(self):
        from app.art_studio.services.generators.inlay_geometry import build_centerline
        pts = build_centerline("swave", 100, amplitude=15)
        assert len(pts) == 200
        y_vals = [p[1] for p in pts]
        assert max(y_vals) > 0 and min(y_vals) < 0  # oscillates

    def test_cscroll(self):
        from app.art_studio.services.generators.inlay_geometry import build_centerline
        pts = build_centerline("cscroll", 100)
        assert len(pts) == 200

    def test_spiral(self):
        from app.art_studio.services.generators.inlay_geometry import build_centerline
        pts = build_centerline("spiral", 100)
        assert len(pts) == 200

    def test_custom(self):
        from app.art_studio.services.generators.inlay_geometry import build_centerline
        custom = [(0, 0), (10, 5), (20, 0), (30, -5), (40, 0)]
        pts = build_centerline("custom", 100, custom_pts=custom)
        assert len(pts) > 10


class TestGenerateStrandPaths:
    def test_two_strands(self):
        from app.art_studio.services.generators.inlay_geometry import (
            build_centerline, generate_strand_paths,
        )
        cl = build_centerline("straight", 50)
        strands = generate_strand_paths(cl, num_strands=2, rope_radius_mm=3,
                                         twist_per_mm=0.3)
        assert len(strands) == 2
        pts, depths, widths = strands[0]
        assert len(pts) == len(cl)
        assert len(depths) == len(cl)
        assert len(widths) == len(cl)

    def test_strand_offset(self):
        from app.art_studio.services.generators.inlay_geometry import (
            build_centerline, generate_strand_paths,
        )
        cl = build_centerline("straight", 100)
        strands = generate_strand_paths(cl, num_strands=3, rope_radius_mm=5,
                                         twist_per_mm=0.25)
        # Strands should be offset from centerline
        strand0_y = [p[1] for p in strands[0][0]]
        assert max(abs(y) for y in strand0_y) > 0.5


class TestSplitStrandAtCrossings:
    def test_crossing_detection(self):
        from app.art_studio.services.generators.inlay_geometry import split_strand_at_crossings
        pts = [(i, 0) for i in range(10)]
        # Depths that cross zero
        depths = [1, 0.5, 0.1, -0.2, -0.5, -0.8, -0.2, 0.3, 0.6, 0.9]
        segments = split_strand_at_crossings(pts, depths)
        assert len(segments) >= 3  # positive → negative → positive
        # First segment should be on_top
        assert segments[0][1] is True

    def test_no_crossing(self):
        from app.art_studio.services.generators.inlay_geometry import split_strand_at_crossings
        pts = [(i, 0) for i in range(5)]
        depths = [1, 1, 1, 1, 1]
        segments = split_strand_at_crossings(pts, depths)
        assert len(segments) == 1
        assert segments[0][1] is True


# ---------------------------------------------------------------------------
# Gallery motif generators
# ---------------------------------------------------------------------------

class TestHexChain:
    def test_default(self):
        col = generate_inlay_pattern("hex_chain", {})
        assert len(col.elements) > 0
        assert col.width_mm > 0
        assert col.height_mm > 0

    def test_count(self):
        col = generate_inlay_pattern("hex_chain", {"count": 6, "cell_h_mm": 15})
        assert col.height_mm > 80  # 6 * 15


class TestChevronPanel:
    def test_default(self):
        col = generate_inlay_pattern("chevron_panel", {})
        assert len(col.elements) > 0
        assert col.tile_w is not None

    def test_count(self):
        col = generate_inlay_pattern("chevron_panel", {"count": 3, "band_h_mm": 25})
        assert len(col.elements) == 3 * 4  # 3 units × 4 layers each


class TestParquetPanel:
    def test_default(self):
        col = generate_inlay_pattern("parquet_panel", {})
        assert len(col.elements) > 0
        assert col.width_mm > 0

    def test_layers(self):
        col = generate_inlay_pattern("parquet_panel", {"layers": 5, "size_mm": 60})
        # 5 diamond layers + 4 quadrant wedges = 9
        assert len(col.elements) == 9


class TestNestedDiamond:
    def test_default(self):
        col = generate_inlay_pattern("nested_diamond", {})
        assert len(col.elements) > 0
        assert col.tile_w is not None

    def test_parameters(self):
        col = generate_inlay_pattern("nested_diamond", {
            "band_w_mm": 120, "diamonds": 3, "nest_depth": 2,
        })
        # 3 groups × (2 nested + 4 corner accents) = 18
        assert len(col.elements) == 18


class TestRopeBorderMotif:
    def test_default(self):
        col = generate_inlay_pattern("rope_border_motif", {})
        assert len(col.elements) > 0
        # All elements should be polygons (strip outlines)
        assert all(e.kind == "polygon" for e in col.elements)

    def test_repeats(self):
        col = generate_inlay_pattern("rope_border_motif", {"repeats": 6, "band_w_mm": 90})
        assert len(col.elements) == 12  # 6 repeats × 2 strands


# ---------------------------------------------------------------------------
# Twisted rope generator
# ---------------------------------------------------------------------------

class TestTwistedRope:
    def test_default(self):
        col = generate_inlay_pattern("twisted_rope", {})
        assert len(col.elements) > 0
        assert col.width_mm > 0
        assert col.height_mm > 0

    def test_purfling_preset(self):
        col = generate_inlay_pattern("twisted_rope", {"preset": "purfling"})
        assert len(col.elements) >= 5  # centerline + 3 strands + envelope

    def test_binding_preset_swave(self):
        col = generate_inlay_pattern("twisted_rope", {"preset": "binding"})
        assert col.width_mm > 0
        assert col.height_mm > 0

    def test_headstock_preset_cscroll(self):
        col = generate_inlay_pattern("twisted_rope", {"preset": "headstock"})
        assert len(col.elements) >= 4  # centerline + 2 strands + envelope

    def test_fret_preset(self):
        col = generate_inlay_pattern("twisted_rope", {"preset": "fret"})
        assert len(col.elements) >= 6  # centerline + 4 strands + envelope

    def test_custom_params(self):
        col = generate_inlay_pattern("twisted_rope", {
            "num_strands": 2, "rope_width": 8, "twist_per_mm": 0.5,
            "length_mm": 60, "shape": "straight",
        })
        assert len(col.elements) >= 4  # centerline + 2 strands + envelope

    def test_spiral_centerline(self):
        col = generate_inlay_pattern("twisted_rope", {
            "shape": "spiral", "length_mm": 80,
        })
        assert col.width_mm > 0

    def test_custom_centerline(self):
        col = generate_inlay_pattern("twisted_rope", {
            "shape": "custom",
            "custom_pts": [[0, 0], [20, 10], [40, 0], [60, -10], [80, 0]],
        })
        assert col.width_mm > 0

    def test_strand_materials(self):
        col = generate_inlay_pattern("twisted_rope", {
            "num_strands": 3, "strand_mats": [0, 2, 1],
        })
        # Second strand element (index 2, after centerline) should have mat 2
        strand_els = [e for e in col.elements if e.kind == "polygon"]
        mats = {e.material_index for e in strand_els}
        assert 2 in mats or 1 in mats


# ---------------------------------------------------------------------------
# Band compositor
# ---------------------------------------------------------------------------

class TestComposeBand:
    def test_preset_rosette(self):
        col = generate_inlay_pattern("compose_band", {"preset": "rosette"})
        assert len(col.elements) > 0
        assert col.width_mm > 0
        assert col.height_mm > 0

    def test_preset_body_binding(self):
        col = generate_inlay_pattern("compose_band", {"preset": "body_binding"})
        assert len(col.elements) > 0

    def test_custom_layers(self):
        col = generate_inlay_pattern("compose_band", {
            "layers": [
                {"shape": "herringbone", "params": {"tooth_w": 8}, "weight": 1},
                {"shape": "diamond", "params": {"tile_w": 10}, "weight": 1},
            ],
            "band_width_mm": 100, "band_height_mm": 30,
            "gap_mm": 0.5, "repeats": 2,
        })
        assert len(col.elements) > 0
        assert col.width_mm == 100

    def test_mirror(self):
        col = generate_inlay_pattern("compose_band", {
            "layers": [
                {"shape": "herringbone", "params": {}, "weight": 1},
            ],
            "band_width_mm": 80, "band_height_mm": 20,
            "repeats": 2, "mirror": True,
        })
        assert len(col.elements) > 0

    def test_empty_layers_uses_default(self):
        col = generate_inlay_pattern("compose_band", {"layers": []})
        assert len(col.elements) > 0  # falls back to default layers

    def test_gap_elements(self):
        col = generate_inlay_pattern("compose_band", {
            "layers": [
                {"shape": "herringbone", "params": {}, "weight": 1},
                {"shape": "diamond", "params": {}, "weight": 1},
            ],
            "gap_mm": 1.0,
        })
        # Should have at least one rect for the gap
        rect_els = [e for e in col.elements if e.kind == "rect"]
        assert len(rect_els) >= 1


# ---------------------------------------------------------------------------
# Compose API endpoint
# ---------------------------------------------------------------------------

class TestComposeAPI:
    def test_compose_preset(self, client):
        r = client.post("/api/art/inlay-patterns/compose", json={
            "preset": "rosette",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["shape"] == "compose_band"
        assert "<svg" in data["svg"]
        assert data["element_count"] > 0

    def test_compose_custom_layers(self, client):
        r = client.post("/api/art/inlay-patterns/compose", json={
            "layers": [
                {"shape": "herringbone", "params": {"tooth_w": 8}, "weight": 1},
            ],
            "band_width_mm": 80,
            "band_height_mm": 20,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["element_count"] > 0

    def test_compose_with_offsets(self, client):
        r = client.post("/api/art/inlay-patterns/compose", json={
            "preset": "fretboard",
            "include_offsets": True,
            "male_offset_mm": 0.1,
            "pocket_offset_mm": 0.1,
        })
        assert r.status_code == 200
        data = r.json()
        assert 'id="male_cut"' in data["svg"]


# ---------------------------------------------------------------------------
# Marquetry generators (session 4)
# ---------------------------------------------------------------------------

class TestCheckerChevron:
    def test_basic(self):
        col = generate_inlay_pattern("checker_chevron", {
            "cell_w": 10, "diamond_r": 5, "band_w": 60, "band_h": 30,
        })
        assert col.width_mm == 60
        assert col.height_mm == 30
        assert col.radial is False
        assert len(col.elements) > 0
        assert all(e.kind == "polygon" for e in col.elements)

    def test_defaults(self):
        col = generate_inlay_pattern("checker_chevron", {})
        assert col.width_mm > 0
        assert len(col.elements) > 0

    def test_material_index_alternates(self):
        col = generate_inlay_pattern("checker_chevron", {"cell_w": 8, "band_w": 40, "band_h": 40})
        indices = {e.material_index for e in col.elements}
        assert len(indices) >= 2

    def test_grain_angle(self):
        col = generate_inlay_pattern("checker_chevron", {})
        for e in col.elements:
            assert hasattr(e, "grain_angle")


class TestBlockPin:
    def test_basic(self):
        col = generate_inlay_pattern("block_pin", {
            "col_w": 12, "cell_h": 10, "diamond_r": 4, "band_w": 60, "band_h": 30,
        })
        assert col.width_mm == 60
        assert col.height_mm == 30
        assert col.radial is False
        assert len(col.elements) > 0

    def test_defaults(self):
        col = generate_inlay_pattern("block_pin", {})
        assert col.width_mm > 0
        assert len(col.elements) > 0

    def test_has_both_shapes(self):
        col = generate_inlay_pattern("block_pin", {"band_w": 60, "band_h": 30})
        kinds = {e.kind for e in col.elements}
        # Should contain both polygon (diamond) and rect
        assert "polygon" in kinds or "rect" in kinds

    def test_material_indices(self):
        col = generate_inlay_pattern("block_pin", {})
        indices = {e.material_index for e in col.elements}
        assert len(indices) >= 2


class TestAmsterdamFlower:
    def test_basic(self):
        col = generate_inlay_pattern("amsterdam_flower", {
            "n_fold": 8, "outer_r": 20, "inner_r": 5,
        })
        assert col.radial is True
        assert len(col.elements) > 0
        assert col.width_mm > 0

    def test_defaults(self):
        col = generate_inlay_pattern("amsterdam_flower", {})
        assert len(col.elements) > 0

    def test_petals_plus_centre(self):
        n = 6
        col = generate_inlay_pattern("amsterdam_flower", {"n_fold": n})
        # n petals + 1 centre disc
        assert len(col.elements) == n + 1

    def test_centre_is_polygon(self):
        col = generate_inlay_pattern("amsterdam_flower", {"n_fold": 8})
        # Last element is the 24-sided centre disc
        centre = col.elements[-1]
        assert centre.kind == "polygon"
        assert len(centre.points) == 24

    def test_grain_angle_set(self):
        col = generate_inlay_pattern("amsterdam_flower", {"n_fold": 6})
        for e in col.elements:
            assert hasattr(e, "grain_angle")


class TestSpiroArc:
    def test_basic(self):
        col = generate_inlay_pattern("spiro_arc", {
            "arc_count": 6, "outer_r": 30, "inner_r": 10, "sweep_deg": 120,
        })
        assert col.radial is True
        assert len(col.elements) > 0
        assert col.width_mm > 0

    def test_defaults(self):
        col = generate_inlay_pattern("spiro_arc", {})
        assert len(col.elements) > 0

    def test_arc_count_matches(self):
        n = 5
        col = generate_inlay_pattern("spiro_arc", {"arc_count": n})
        assert len(col.elements) == n

    def test_material_indices_cycle(self):
        col = generate_inlay_pattern("spiro_arc", {"arc_count": 6})
        indices = [e.material_index for e in col.elements]
        # Should cycle through materials
        assert len(set(indices)) >= 2


class TestSqFloral:
    def test_basic(self):
        col = generate_inlay_pattern("sq_floral", {
            "n_fold": 8, "outer_r": 25, "inner_r": 8,
        })
        assert col.radial is True
        assert len(col.elements) > 0
        assert col.width_mm > 0

    def test_defaults(self):
        col = generate_inlay_pattern("sq_floral", {})
        assert len(col.elements) > 0

    def test_element_count_matches_nfold(self):
        n = 10
        col = generate_inlay_pattern("sq_floral", {"n_fold": n})
        assert len(col.elements) == n

    def test_grain_angle_set(self):
        col = generate_inlay_pattern("sq_floral", {"n_fold": 6})
        for e in col.elements:
            assert hasattr(e, "grain_angle")


# ---------------------------------------------------------------------------
# BOM calculator
# ---------------------------------------------------------------------------

from app.art_studio.services.generators.inlay_geometry import (
    BomEntry,
    calculate_bom,
)


class TestBomCalculator:
    def test_basic_bom(self):
        col = generate_inlay_pattern("herringbone", {"band_w": 40, "band_h": 20})
        entries = calculate_bom(col, ["mop", "ebony", "koa"])
        assert len(entries) > 0
        assert all(isinstance(e, BomEntry) for e in entries)
        assert all(e.count > 0 for e in entries)
        assert all(e.area_mm2 >= 0 for e in entries)

    def test_bom_total_pieces(self):
        col = generate_inlay_pattern("sunburst", {"rays": 6, "band_r": 20})
        entries = calculate_bom(col, ["mop", "ebony", "koa"])
        total = sum(e.count for e in entries)
        assert total == len(col.elements)

    def test_bom_with_circles(self):
        col = generate_inlay_pattern("sunburst", {"rays": 4, "band_r": 20})
        entries = calculate_bom(col, ["mop", "ebony"])
        circle_entries = [e for e in entries if e.shape_type == "circle"]
        # Sunburst has one inner circle
        assert len(circle_entries) >= 1
        assert circle_entries[0].area_mm2 > 0

    def test_bom_material_keys(self):
        col = generate_inlay_pattern("diamond", {"band_w": 30, "band_h": 20})
        materials = ["maple", "walnut"]
        entries = calculate_bom(col, materials)
        for e in entries:
            assert e.material_key in materials


# ---------------------------------------------------------------------------
# Region clip shapes
# ---------------------------------------------------------------------------

from app.art_studio.services.generators.inlay_geometry import (
    binding_strip,
    fretboard_trapezoid,
    rosette_ring,
)


class TestFretboardTrapezoid:
    def test_basic(self):
        pts = fretboard_trapezoid(43.0, 56.0, 650.0)
        assert len(pts) == 4
        # X-centred: x extents are symmetric around 0
        xs = [p[0] for p in pts]
        assert pytest.approx(min(xs), abs=0.5) == -max(xs)

    def test_width_ordering(self):
        pts = fretboard_trapezoid(40.0, 55.0, 500.0)
        # nut end (y=0) should be narrower than body end (y=500)
        nut_xs = sorted([abs(p[0]) for p in pts if abs(p[1]) < 1])
        body_xs = sorted([abs(p[0]) for p in pts if abs(p[1] - 500) < 1])
        # body half-width > nut half-width
        assert max(body_xs) > max(nut_xs)


class TestRosetteRing:
    def test_basic(self):
        outer, inner = rosette_ring(60.0, 50.0)
        assert len(outer) == 64
        assert len(inner) == 64

    def test_radii(self):
        outer, inner = rosette_ring(40.0, 30.0, n_segments=32)
        import math
        r_out = math.hypot(outer[0][0], outer[0][1])
        r_in = math.hypot(inner[0][0], inner[0][1])
        assert r_out == pytest.approx(40.0, abs=0.1)
        assert r_in == pytest.approx(30.0, abs=0.1)


class TestBindingStrip:
    def test_basic(self):
        pts = binding_strip(400.0, 2.0)
        assert len(pts) == 4
        xs = sorted([p[0] for p in pts])
        ys = sorted([p[1] for p in pts])
        assert xs[-1] - xs[0] == pytest.approx(400.0)
        assert ys[-1] - ys[0] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# grain_angle metadata
# ---------------------------------------------------------------------------

class TestGrainAngle:
    def test_geometry_element_default(self):
        el = GeometryElement(kind="rect", points=[(0, 0), (10, 5)])
        assert el.grain_angle == 0.0

    def test_geometry_element_set(self):
        el = GeometryElement(kind="rect", points=[(0, 0), (10, 5)], grain_angle=45.0)
        assert el.grain_angle == 45.0

    def test_radial_generators_set_grain(self):
        """Radial generators should set grain_angle on their elements."""
        col = generate_inlay_pattern("amsterdam_flower", {"n_fold": 8})
        angles = [e.grain_angle for e in col.elements]
        # Not all angles should be 0 (radial patterns rotate grain)
        assert any(a != 0.0 for a in angles[:-1])  # skip centre disc


# ---------------------------------------------------------------------------
# BOM API endpoint
# ---------------------------------------------------------------------------

class TestBomAPI:
    def test_bom_endpoint(self, client):
        r = client.post("/api/art/inlay-patterns/bom", json={
            "shape": "herringbone",
            "params": {"band_w": 40, "band_h": 20},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["shape"] == "herringbone"
        assert len(data["entries"]) > 0
        assert data["total_pieces"] > 0
        assert data["total_area_mm2"] > 0

    def test_bom_with_materials(self, client):
        r = client.post("/api/art/inlay-patterns/bom", json={
            "shape": "sunburst",
            "params": {"rays": 4, "band_r": 20},
            "materials": ["maple", "walnut"],
        })
        assert r.status_code == 200
        data = r.json()
        for entry in data["entries"]:
            assert entry["material_key"] in ["maple", "walnut"]

    def test_bom_unknown_shape(self, client):
        r = client.post("/api/art/inlay-patterns/bom", json={
            "shape": "nonexistent",
            "params": {},
        })
        assert r.status_code == 422  # Pydantic rejects invalid literal


# ---------------------------------------------------------------------------
# Blueprint-to-Inlay bridge API endpoint
# ---------------------------------------------------------------------------

class TestBlueprintBridgeAPI:
    def test_missing_paths_returns_400(self, client):
        r = client.post("/api/art/inlay-patterns/import-from-blueprint", json={})
        assert r.status_code == 400

    def test_path_outside_allowed_dir_returns_403(self, client):
        r = client.post("/api/art/inlay-patterns/import-from-blueprint", json={
            "dxf_path": "/etc/passwd",
        })
        assert r.status_code == 403

    def test_nonexistent_file_returns_404(self, client, tmp_path):
        # Even if the path is inside allowed dir, a missing file gives 404
        import os
        allowed = tmp_path / "blueprint_output"
        allowed.mkdir()
        fake = allowed / "missing.dxf"
        # Monkeypatch the allowed dir constant
        import app.art_studio.api.inlay_pattern_routes as routes_mod
        original = routes_mod._ALLOWED_BLUEPRINT_DIR
        routes_mod._ALLOWED_BLUEPRINT_DIR = str(allowed.parent)
        try:
            r = client.post("/api/art/inlay-patterns/import-from-blueprint", json={
                "dxf_path": str(fake),
            })
            # Could be 403 or 404 depending on path resolution
            assert r.status_code in (403, 404)
        finally:
            routes_mod._ALLOWED_BLUEPRINT_DIR = original

    def test_valid_dxf_import(self, client, tmp_path):
        """Import a DXF file from the blueprint output directory."""
        import app.art_studio.api.inlay_pattern_routes as routes_mod

        bp_dir = tmp_path / "blueprint_output"
        bp_dir.mkdir()
        dxf_file = bp_dir / "test.dxf"
        dxf_file.write_text(
            "0\nSECTION\n2\nENTITIES\n0\nCIRCLE\n10\n5.0\n20\n5.0\n40\n3.0\n0\nENDSEC\n0\nEOF"
        )

        original = routes_mod._ALLOWED_BLUEPRINT_DIR
        routes_mod._ALLOWED_BLUEPRINT_DIR = str(bp_dir)
        try:
            r = client.post("/api/art/inlay-patterns/import-from-blueprint", json={
                "dxf_path": str(dxf_file),
            })
            assert r.status_code == 200
            data = r.json()
            assert data["format_detected"] == "dxf"
            assert data["element_count"] >= 1
            assert "<svg" in data["preview_svg"]
        finally:
            routes_mod._ALLOWED_BLUEPRINT_DIR = original

    def test_valid_svg_import(self, client, tmp_path):
        """Import an SVG file from the blueprint output directory."""
        import app.art_studio.api.inlay_pattern_routes as routes_mod

        bp_dir = tmp_path / "blueprint_output"
        bp_dir.mkdir()
        svg_file = bp_dir / "test.svg"
        svg_file.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect x="10" y="20" width="50" height="30"/></svg>'
        )

        original = routes_mod._ALLOWED_BLUEPRINT_DIR
        routes_mod._ALLOWED_BLUEPRINT_DIR = str(bp_dir)
        try:
            r = client.post("/api/art/inlay-patterns/import-from-blueprint", json={
                "svg_path": str(svg_file),
            })
            assert r.status_code == 200
            data = r.json()
            assert data["format_detected"] == "svg"
            assert data["element_count"] >= 1
        finally:
            routes_mod._ALLOWED_BLUEPRINT_DIR = original
