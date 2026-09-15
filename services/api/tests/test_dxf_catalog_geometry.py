"""
DXF-CATALOG-GATE-001: the outline geometry model (third review round).

Each test is a witness a probe confirmed against the previous model, which
reduced every edge to its endpoint chord, snapped endpoints to a fixed grid,
and judged "bounds" by bbox alone:
- an ARC crossing another edge passed both gates (the crossing test saw a chord);
- the chain-crossing check ran only if closed_outline ran first;
- a LINE chord over a shallow ARC was de-duplicated away (same endpoints);
- an outline built from ARCs failed coverage (endpoint bbox vs sampled extent);
- sub-micron endpoint differences counted as a self-crossing in the Files gate;
- endpoints 0.03 mm apart joined or not depending on where the grid fell;
- a spline was chained at its control points, not where the curve ends;
- a thin contour running corner to corner passed as the body;
- a bulged LWPOLYLINE was read as its chords, and ARCs in a mirrored OCS
  were placed unmirrored;
- layer names were compared case-sensitively (DXF compares them without case);
- a quarantine record was called stale for clauses the gate never ran.
"""
import copy
import math

import ezdxf
import pytest

from app.ci import check_dxf_files
from app.ci import dxf_catalog_geometry as geometry
from app.ci import dxf_catalog_policy as policy
from tests.test_dxf_catalog_gate import (  # noqa: F401  (fixtures are used by name)
    BODY, ELLIPSE, _lines, _record, _save, asset_gate, bare_registry, mini_catalog, registry,
)

pytestmark = pytest.mark.allow_missing_request_id

OUTLINE = {"layer": "BODY_OUTLINE"}


def _outline(path, registry):  # noqa: F811
    doc = ezdxf.readfile(str(path))
    return policy.check_closed_outline(list(doc.modelspace()), registry["asset_classes"][BODY]).failure


def _gates(path, registry, asset_gate):  # noqa: F811
    files = check_dxf_files.validate_dxf_file(path, registry, asset_class=BODY)
    assets = asset_gate.validate_dxf_file(path, registry, asset_class=BODY)
    return files["status"], files["info"]["failed_clauses"], assets.status


def _arc(msp, center, radius, start, end, **attribs):
    msp.add_arc(center, radius, start, end, dxfattribs={**OUTLINE, **attribs})


def _shallow_arc(msp, p, q, sagitta):
    """ARC from p to q bulging away from the origin by `sagitta` mm."""
    half = math.dist(p, q) / 2
    radius = (half * half + sagitta * sagitta) / (2 * sagitta)
    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    nx, ny = (q[1] - p[1]) / (2 * half), (p[0] - q[0]) / (2 * half)  # unit normal to the chord
    if nx * mid[0] + ny * mid[1] < 0:
        nx, ny = -nx, -ny  # point it away from the origin
    center = (mid[0] - (radius - sagitta) * nx, mid[1] - (radius - sagitta) * ny)
    a, b = (math.degrees(math.atan2(pt[1] - center[1], pt[0] - center[0])) for pt in (p, q))
    _arc(msp, center, radius, *((a, b) if (b - a) % 360 < 180 else (b, a)))


# -----------------------------------------------------------------------------
# Crossings
# -----------------------------------------------------------------------------

def test_an_arc_that_crosses_another_edge_fails_topology(tmp_path, bare_registry, asset_gate):  # noqa: F811
    # A 300 x 200 rectangle whose left side is an ARC from (0, 0) to (0, 200) that swings right,
    # through (60, 0) on the bottom edge. Its chord is the left side, so a chord model sees no crossing.
    def build(m):
        m.add_line((0, 0), (300, 0), dxfattribs=OUTLINE)
        m.add_line((300, 0), (300, 200), dxfattribs=OUTLINE)
        m.add_line((300, 200), (0, 200), dxfattribs=OUTLINE)
        _arc(m, (30.0, 100.0), math.hypot(30, 100),
             math.degrees(math.atan2(-100, -30)), math.degrees(math.atan2(100, -30)))
    files, failed, assets = _gates(_save(tmp_path, "arc_cross", "R12", build), bare_registry, asset_gate)
    assert (files, failed, assets) == ("FAIL", ["topology_valid"], "PASS")


def test_the_chain_crossing_check_does_not_depend_on_clause_order(tmp_path, bare_registry):  # noqa: F811
    bowtie = [(-175, -225), (175, 225), (175, -225), (-175, 225)]
    path = _save(tmp_path, "bowtie", "R12", lambda m: _lines(m, bowtie))
    reordered = copy.deepcopy(bare_registry)
    contract = reordered["asset_classes"][BODY]["contract"]
    contract.remove("closed_outline")
    contract.append("closed_outline")  # topology_valid now runs before closed_outline
    for reg in (bare_registry, reordered):
        assert check_dxf_files.validate_dxf_file(path, reg, asset_class=BODY)["info"]["failed_clauses"] \
            == ["topology_valid"]


def _filleted_rectangle(msp, angle_deg=23.0, radius=20.0, w=300.0, h=400.0):
    """Rounded rectangle, rotated; LINE ends rounded to 3 dp (catalog precision), ARCs exact."""
    t = math.radians(angle_deg)

    def rot(x, y):
        return (round(x * math.cos(t) - y * math.sin(t), 3), round(x * math.sin(t) + y * math.cos(t), 3))
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    sides = [((x0 + radius, y0), (x1 - radius, y0)), ((x1, y0 + radius), (x1, y1 - radius)),
             ((x1 - radius, y1), (x0 + radius, y1)), ((x0, y1 - radius), (x0, y0 + radius))]
    for a, b in sides:
        msp.add_line(rot(*a), rot(*b), dxfattribs=OUTLINE)
    corners = [((x1 - radius, y0 + radius), -90), ((x1 - radius, y1 - radius), 0),
               ((x0 + radius, y1 - radius), 90), ((x0 + radius, y0 + radius), 180)]
    for (cx, cy), start in corners:
        c = (cx * math.cos(t) - cy * math.sin(t), cx * math.sin(t) + cy * math.cos(t))
        _arc(msp, c, radius, start + angle_deg, start + 90 + angle_deg)


# Under the previous model 164 of 360 such rectangles (0-89.5 deg in 0.5 deg steps, radius 20 or 7.5)
# failed: 5.0 deg read as a self-crossing in the Files gate; 2.0 deg split on the snap grid.
@pytest.mark.parametrize("angle", [5.0, 2.0, 23.0])
def test_sub_micron_endpoint_differences_are_not_a_crossing(tmp_path, bare_registry, asset_gate, angle):  # noqa: F811
    path = _save(tmp_path, "fillet", "R12", lambda m: _filleted_rectangle(m, angle_deg=angle))
    assert _gates(path, bare_registry, asset_gate) == ("PASS", [], "PASS")


# -----------------------------------------------------------------------------
# Edge identity and arcs
# -----------------------------------------------------------------------------

def test_a_chord_over_a_shallow_arc_makes_the_outline_branch(tmp_path, registry):  # noqa: F811
    def build(m):
        _lines(m, ELLIPSE[1:] + ELLIPSE[:1], closed=False)  # every edge except ELLIPSE[0] -> ELLIPSE[1]
        _shallow_arc(m, ELLIPSE[0], ELLIPSE[1], 1.0)
        m.add_line(ELLIPSE[0], ELLIPSE[1], dxfattribs=OUTLINE)
    assert "branch or touch themselves" in _outline(_save(tmp_path, "chord_arc", "R12", build), registry)


def test_the_same_arc_drawn_twice_is_one_edge(tmp_path, registry):  # noqa: F811
    def build(m):
        _lines(m, ELLIPSE[1:] + ELLIPSE[:1], closed=False)
        _shallow_arc(m, ELLIPSE[0], ELLIPSE[1], 1.0)
        _shallow_arc(m, ELLIPSE[1], ELLIPSE[0], 1.0)
    assert _outline(_save(tmp_path, "arc_twice", "R12", build), registry) is None


def _stadium(msp, **attribs):
    msp.add_line((-100, -50), (100, -50), dxfattribs=OUTLINE)
    msp.add_line((100, 50), (-100, 50), dxfattribs=OUTLINE)
    _arc(msp, (100, 0), 50, -90, 90, **attribs)
    _arc(msp, (-100, 0), 50, 90, 270, **attribs)


def test_an_outline_with_arc_ends_passes_both_gates(tmp_path, bare_registry, asset_gate):  # noqa: F811
    assert _gates(_save(tmp_path, "stadium", "R12", _stadium), bare_registry, asset_gate) == ("PASS", [], "PASS")


def test_a_lens_of_two_arcs_between_the_same_vertices_is_closed(tmp_path, registry):  # noqa: F811
    def build(m):
        r = math.hypot(150, 100)
        a = math.degrees(math.atan2(100, 150))
        _arc(m, (0, -100), r, a, 180 - a)    # upper arc, (150, 0) -> (-150, 0)
        _arc(m, (0, 100), r, 180 + a, -a)    # lower arc, (-150, 0) -> (150, 0)
    assert _outline(_save(tmp_path, "lens", "R12", build), registry) is None


def test_arcs_in_a_mirrored_ocs_are_placed_in_world_coordinates(tmp_path, registry):  # noqa: F811
    def build(m):
        m.add_line((-100, -50), (100, -50), dxfattribs=OUTLINE)
        m.add_line((100, 50), (-100, 50), dxfattribs=OUTLINE)
        # Extrusion -Z mirrors x: OCS centre (-100, 0) is world (100, 0), and OCS angles run the other way.
        _arc(m, (-100, 0), 50, 90, 270, extrusion=(0, 0, -1))
        _arc(m, (100, 0), 50, -90, 90, extrusion=(0, 0, -1))
    assert _outline(_save(tmp_path, "mirrored", "R12", build), registry) is None


def test_a_bulged_lwpolyline_is_read_as_its_arcs(tmp_path, registry):  # noqa: F811
    def build(m):
        # Stadium as one closed LWPOLYLINE: semicircular ends are bulge 1 (x reaches +/-150).
        m.add_lwpolyline([(-100, -50, 0), (100, -50, 1), (100, 50, 0), (-100, 50, 1)], format="xyb",
                         close=True, dxfattribs=OUTLINE)
        m.add_line((140, -10), (140, 10), dxfattribs=OUTLINE)  # inside the right cap, outside its chord
    assert _outline(_save(tmp_path, "bulge", "R2000", build), registry) is None


# -----------------------------------------------------------------------------
# Vertices and splines
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("x0", [175.0, 175.024, 175.026])  # a 0.05 mm grid would split the pair at 175.025
@pytest.mark.parametrize("gap,closed", [(0.03, True), (0.06, False)])
def test_endpoint_join_depends_on_the_gap_not_on_where_it_falls(tmp_path, registry, x0, gap, closed):  # noqa: F811
    pts = [(x0, 0.0)] + list(ELLIPSE[1:])
    path = _save(tmp_path, "gap", "R12", lambda m: (
        _lines(m, pts, closed=False), m.add_line(pts[-1], (x0 + gap, 0.0), dxfattribs=OUTLINE)))
    assert (_outline(path, registry) is None) is closed


def _uniform_spline(msp, control):
    spline = msp.add_spline(dxfattribs=OUTLINE)
    spline.dxf.degree = 3
    spline.control_points = control
    spline.knots = [float(i) for i in range(len(control) + 4)]  # uniform: not clamped to its ends
    return spline


def test_a_spline_is_chained_where_its_curve_ends_not_at_its_control_points(tmp_path, registry):  # noqa: F811
    # The control polygon runs (0, 400) -> (0, 0), but an unclamped cubic curve starts at
    # (P0 + 4 P1 + P2) / 6 = (-25, 283.3) and ends at (-25, 116.7): the rectangle is open.
    def build(m):
        _lines(m, [(0, 0), (300, 0), (300, 400), (0, 400)], closed=False)
        _uniform_spline(m, [(0, 400), (-30, 300), (-30, 100), (0, 0)])
    assert "No simple closed contour" in _outline(_save(tmp_path, "spline", "R2000", build), registry)


def test_uniform_cubic_evaluation_matches_the_closed_form():
    doc = ezdxf.new("R2000")
    spline = _uniform_spline(doc.modelspace(), [(0, 400), (-30, 300), (-30, 100), (0, 0)])
    points = geometry.spline_points(spline)
    assert points[0] == pytest.approx((-25.0, 1700 / 6))
    assert points[-1] == pytest.approx((-25.0, 700 / 6))


# -----------------------------------------------------------------------------
# Bounds: bbox coverage is necessary, not sufficient
# -----------------------------------------------------------------------------

def test_a_thin_contour_spanning_the_bbox_does_not_stand_in_for_the_body(tmp_path, registry):  # noqa: F811
    sliver = [(-175, -225), (-173, -225), (175, 225), (173, 225)]  # 2 mm wide, corner to corner
    path = _save(tmp_path, "sliver", "R12", lambda m: (_lines(m, sliver), _lines(m, ELLIPSE, closed=False)))
    failure = _outline(path, registry)
    assert failure and "encloses only" in failure


def test_marks_inside_the_body_count_as_enclosed(tmp_path, registry):  # noqa: F811
    path = _save(tmp_path, "marks", "R12", lambda m: (
        _lines(m, ELLIPSE), _lines(m, [(-50, -50), (50, -50), (50, 50), (-50, 50)], closed=False)))
    assert _outline(path, registry) is None


# -----------------------------------------------------------------------------
# Layer names and the healed-clause rule
# -----------------------------------------------------------------------------

def test_layer_names_are_compared_without_case(tmp_path, bare_registry):  # noqa: F811
    def build(m):
        m.add_lwpolyline(ELLIPSE, close=True, dxfattribs={"layer": "body_outline"})
        m.add_lwpolyline([(0, 0), (50, 50), (50, 0), (0, 50), (0, 0)], dxfattribs={"layer": "Body_Points"})
    result = check_dxf_files.validate_dxf_file(_save(tmp_path, "case", "R2000", build), bare_registry,
                                               asset_class=BODY)
    assert result["info"]["failed_clauses"] == ["version_allowed"]


def test_clauses_after_an_early_stop_are_not_called_healed(mini_catalog, bare_registry, asset_gate):  # noqa: F811
    folder = mini_catalog / "body" / "dxf" / "electric"
    path = _save(folder, "x", "R2000", lambda m: m.add_text("BODY"))
    record = _record("body/dxf/electric/x.dxf", ["geometry_present", "version_allowed"], policy.file_sha256(path))
    bare_registry["quarantine"] = [record]
    files = check_dxf_files.validate_dxf_file(path, bare_registry)
    assert (files["status"], asset_gate.validate_dxf_file(path, bare_registry).status) \
        == ("QUARANTINED", "QUARANTINED"), files["errors"]
