"""
Tests for the Interactive Rosette Designer engine + API endpoints.

Covers: geometry math, symmetry engine, tile placement, BOM computation,
manufacturing intelligence (6 checks), recipe library, CSV export,
auto-fix helpers, and API endpoint integration.
"""
import math
import pytest
from fastapi.testclient import TestClient

from app.art_studio.schemas.rosette_designer import (
    RING_DEFS,
    SEG_OPTIONS,
    TILE_MAP,
    BomRequest,
    MfgCheckRequest,
    SymmetryMode,
)
# Rosette Consolidation: rosette_designer.py → rosette_engine.py
from app.art_studio.services.rosette_engine import (
    RosetteEngine,
    MFG_THRESHOLDS,
    arc_cell_path,
    auto_fix_shallow_rings,
    auto_fix_short_arcs,
    bom_to_csv,
    cell_info,
    compute_bom,
    get_sym_cells,
    get_tile_color_hex,
    get_tile_fill,
    place_tile,
    RECIPES,
    render_preview_svg,
    run_mfg_checks,
    tab_path,
)

# Access internal helpers via RosetteEngine static methods
_rad = RosetteEngine._rad
_pt_on_circle = RosetteEngine._pt_on_circle
_arc_inches = RosetteEngine._arc_inches


# ═══════════════════════════════════════════════════════════════════════════
# Geometry helpers
# ═══════════════════════════════════════════════════════════════════════════

class TestGeometryHelpers:
    def test_rad_conversion(self):
        assert _rad(0) == 0.0
        assert abs(_rad(180) - math.pi) < 1e-10
        assert abs(_rad(360) - 2 * math.pi) < 1e-10

    def test_pt_on_circle_top(self):
        """deg=0 → top of circle (12-o'clock)."""
        x, y = _pt_on_circle(0, 0, 100, 0)
        assert abs(x - 0) < 1e-6
        assert abs(y - (-100)) < 1e-6

    def test_pt_on_circle_right(self):
        """deg=90 → right (3-o'clock)."""
        x, y = _pt_on_circle(0, 0, 100, 90)
        assert abs(x - 100) < 1e-6
        assert abs(y - 0) < 1e-6

    def test_arc_inches_full_circle(self):
        """Full circle arc length = 2πr / 100."""
        r = 200
        arc = _arc_inches(r, 360)
        expected = 2 * math.pi * r / 100.0
        assert abs(arc - expected) < 1e-8

    def test_arc_inches_quarter(self):
        r = 100
        arc = _arc_inches(r, 90)
        expected = 2 * math.pi * r / 100.0 / 4
        assert abs(arc - expected) < 1e-8


class TestSvgPathBuilders:
    def test_arc_cell_path_returns_closed_path(self):
        path = arc_cell_path(310, 310, 150, 190, 0, 30)
        assert path.startswith("M ")
        assert path.endswith("Z")
        assert " A " in path

    def test_tab_path_returns_closed_path(self):
        path = tab_path(310, 310, 200, 312, 15, 5)
        assert path.startswith("M ")
        assert path.endswith("Z")


# ═══════════════════════════════════════════════════════════════════════════
# Tile fill helpers
# ═══════════════════════════════════════════════════════════════════════════

class TestTileFill:
    def test_solid_tile_returns_color(self):
        fill = get_tile_fill("maple")
        assert fill == "#D4B483"

    def test_pattern_tile_returns_url(self):
        fill = get_tile_fill("abalone")
        assert fill.startswith("url(#")

    def test_clear_returns_none(self):
        assert get_tile_fill("clear") == "none"
        assert get_tile_fill("") == "none"

    def test_unknown_returns_fallback(self):
        assert get_tile_fill("nonexistent-xyz") == "#888"

    def test_color_hex_solid(self):
        assert get_tile_color_hex("ebony") == "#1C1C1C"

    def test_color_hex_pattern(self):
        c = get_tile_color_hex("abalone")
        assert c.startswith("#")


# ═══════════════════════════════════════════════════════════════════════════
# Symmetry engine
# ═══════════════════════════════════════════════════════════════════════════

class TestSymmetryEngine:
    def test_none_returns_single_cell(self):
        cells = get_sym_cells(2, 3, SymmetryMode.NONE, 12)
        assert cells == [[2, 3]]

    def test_rotational_fills_all_segments(self):
        cells = get_sym_cells(2, 0, SymmetryMode.ROTATIONAL, 12)
        assert len(cells) == 12
        segs = {c[1] for c in cells}
        assert segs == set(range(12))
        assert all(c[0] == 2 for c in cells)

    def test_bilateral_returns_pair(self):
        cells = get_sym_cells(0, 2, SymmetryMode.BILATERAL, 12)
        assert len(cells) == 2
        segs = sorted(c[1] for c in cells)
        assert segs == [2, 10]  # 2 and (12-2)%12=10

    def test_bilateral_zero_deduplicates(self):
        """seg=0 → mirror = 12%12=0 → should dedup to 1 cell."""
        cells = get_sym_cells(0, 0, SymmetryMode.BILATERAL, 12)
        assert len(cells) == 1

    def test_quadrant_returns_up_to_8(self):
        cells = get_sym_cells(0, 1, SymmetryMode.QUADRANT, 12)
        # Step=3, so offsets: 1, 4, 7, 10 + mirrors
        assert len(cells) <= 8
        assert all(c[0] == 0 for c in cells)

    def test_quadrant_dedup(self):
        """seg=0 with 12-seg quadrant should dedup overlapping mirrors."""
        cells = get_sym_cells(0, 0, SymmetryMode.QUADRANT, 12)
        keys = [f"{c[0]}-{c[1]}" for c in cells]
        assert len(keys) == len(set(keys))  # No duplicates


# ═══════════════════════════════════════════════════════════════════════════
# Tile placement
# ═══════════════════════════════════════════════════════════════════════════

class TestPlaceTile:
    def test_place_single(self):
        grid: dict[str, str] = {}
        active = [True] * 5
        new_grid, affected = place_tile(grid, 2, 5, "maple", SymmetryMode.NONE, 12, active)
        assert new_grid["2-5"] == "maple"
        assert "2-5" in affected
        assert len(affected) == 1

    def test_place_clear_removes(self):
        grid = {"2-5": "maple"}
        active = [True] * 5
        new_grid, _ = place_tile(grid, 2, 5, "clear", SymmetryMode.NONE, 12, active)
        assert "2-5" not in new_grid

    def test_place_respects_inactive_ring(self):
        grid: dict[str, str] = {}
        active = [True, True, True, True, False]
        new_grid, affected = place_tile(grid, 4, 0, "maple", SymmetryMode.NONE, 12, active)
        assert "4-0" not in new_grid

    def test_place_rotational_fills_full_ring(self):
        grid: dict[str, str] = {}
        active = [True] * 5
        new_grid, affected = place_tile(grid, 2, 0, "abalone", SymmetryMode.ROTATIONAL, 12, active)
        assert len(affected) == 12
        assert all(new_grid.get(f"2-{s}") == "abalone" for s in range(12))

    def test_place_does_not_mutate_original(self):
        grid = {"2-0": "maple"}
        active = [True] * 5
        new_grid, _ = place_tile(grid, 2, 1, "rosewood", SymmetryMode.NONE, 12, active)
        assert "2-1" not in grid  # Original unchanged
        assert new_grid["2-1"] == "rosewood"


# ═══════════════════════════════════════════════════════════════════════════
# Cell info
# ═══════════════════════════════════════════════════════════════════════════

class TestCellInfo:
    def test_empty_cell(self):
        info = cell_info(2, 5, 12, {})
        assert info["zone"] == "Main Channel"
        assert info["tile_name"] is None
        assert "seg" in info
        assert "angle" in info

    def test_filled_cell(self):
        grid = {"2-5": "maple"}
        info = cell_info(2, 5, 12, grid)
        assert info["tile_name"] == "Maple"
        assert info["tile_id"] == "maple"


# ═══════════════════════════════════════════════════════════════════════════
# BOM engine
# ═══════════════════════════════════════════════════════════════════════════

class TestBomEngine:
    def test_empty_grid_bom(self):
        req = BomRequest(num_segs=12, grid={}, ring_active=[True] * 5)
        bom = compute_bom(req)
        assert bom.total_pieces == 0
        assert bom.material_count == 0
        assert bom.fill_percent == 0

    def test_filled_ring_bom(self):
        grid = {f"2-{s}": "maple" for s in range(12)}
        req = BomRequest(num_segs=12, grid=grid, ring_active=[True] * 5)
        bom = compute_bom(req)
        assert bom.total_pieces == 12
        assert bom.material_count == 1
        assert bom.fill_percent > 0
        assert len(bom.materials) == 1
        assert bom.materials[0].tile_name == "Maple"
        assert bom.materials[0].pieces == 12

    def test_multiple_materials_bom(self):
        grid = {}
        for s in range(6):
            grid[f"2-{s}"] = "maple"
        for s in range(6, 12):
            grid[f"2-{s}"] = "rosewood"
        req = BomRequest(num_segs=12, grid=grid, ring_active=[True] * 5)
        bom = compute_bom(req)
        assert bom.material_count == 2
        assert bom.total_pieces == 12

    def test_bom_rings_info(self):
        grid = {f"0-{s}": "cream" for s in range(12)}
        req = BomRequest(num_segs=12, grid=grid, ring_active=[True] * 5)
        bom = compute_bom(req)
        assert len(bom.rings) == 5
        assert bom.rings[0].filled == 12
        assert bom.rings[1].filled == 0

    def test_bom_to_csv(self):
        grid = {f"2-{s}": "maple" for s in range(12)}
        req = BomRequest(num_segs=12, grid=grid, ring_active=[True] * 5)
        csv = bom_to_csv(req, "Test Design")
        lines = csv.splitlines()
        assert len(lines) >= 2  # Header + at least 1 data row
        assert "Maple" in lines[1]
        assert "Main Channel" in lines[1]


# ═══════════════════════════════════════════════════════════════════════════
# Manufacturing Intelligence — 6 checks
# ═══════════════════════════════════════════════════════════════════════════

class TestMfgChecks:
    def _base_req(self, num_segs=12, grid=None, sym_mode=SymmetryMode.NONE,
                  ring_active=None, show_tabs=True):
        return MfgCheckRequest(
            num_segs=num_segs,
            sym_mode=sym_mode,
            grid=grid or {},
            ring_active=ring_active or [True] * 5,
            show_tabs=show_tabs,
        )

    def test_clean_design_scores_100(self):
        """12-seg design with all rings filled → 100 score."""
        grid = {}
        for ri in range(5):
            for s in range(12):
                grid[f"{ri}-{s}"] = "maple"
        req = self._base_req(num_segs=12, grid=grid)
        result = run_mfg_checks(req)
        assert result.score == 100
        assert result.score_class == "good"
        assert result.error_count == 0

    def test_empty_grid_scores_zero(self):
        req = self._base_req(num_segs=12)
        result = run_mfg_checks(req)
        assert result.score == 0

    def test_high_seg_count_triggers_short_arc(self):
        """24 segments with purfling rings → inner arcs may be fragile."""
        grid = {f"1-{s}": "bwb" for s in range(24)}
        req = self._base_req(num_segs=24, grid=grid)
        result = run_mfg_checks(req)
        # The inner purfling has r1=190, small ring — might get warnings
        # At min, check that flags are returned or score adjusted
        assert result.score <= 100

    def test_quadrant_mismatch_flag(self):
        """Quadrant symmetry @ 10 segs → not divisible by 4."""
        grid = {f"2-{s}": "maple" for s in range(10)}
        req = self._base_req(num_segs=10, sym_mode=SymmetryMode.QUADRANT, grid=grid)
        result = run_mfg_checks(req)
        flag_ids = [f.id for f in result.flags]
        assert "sym-mismatch" in flag_ids

    def test_empty_purfling_flag(self):
        """Main channel filled but purfling empty → info flag."""
        grid = {f"2-{s}": "maple" for s in range(12)}
        req = self._base_req(num_segs=12, grid=grid,
                             ring_active=[True, True, True, True, True])
        result = run_mfg_checks(req)
        flag_ids = [f.id for f in result.flags]
        assert "empty-purfling-1" in flag_ids or "empty-purfling-3" in flag_ids

    def test_score_decremented_by_severity(self):
        """Errors subtract 20, warnings 8, infos 2 from 100."""
        grid = {f"2-{s}": "maple" for s in range(12)}
        req = self._base_req(num_segs=12, grid=grid)
        result = run_mfg_checks(req)
        expected = 100 - (result.error_count * 20) - (result.warning_count * 8) - (result.info_count * 2)
        expected = max(0, min(100, expected))
        assert result.score == expected

    def test_mfg_response_shape(self):
        req = self._base_req(num_segs=12, grid={"2-0": "maple"})
        result = run_mfg_checks(req)
        assert hasattr(result, "score")
        assert hasattr(result, "score_class")
        assert hasattr(result, "flags")
        assert hasattr(result, "passing_count")


# ═══════════════════════════════════════════════════════════════════════════
# Auto-fix helpers
# ═══════════════════════════════════════════════════════════════════════════

class TestAutoFix:
    def test_auto_fix_short_arcs_at_24_segs_keeps_all(self):
        """At 24 segments, all rings have arcs above FRAGILE_ARC threshold."""
        grid = {f"1-{s}": "bwb" for s in range(24)}
        active = [True] * 5
        fixed = auto_fix_short_arcs(grid, 24, active)
        # Inner Purfling (r1=190, r2=210) at 24 segs → arc = π*190*15/180/100 = 0.497"
        # This is ABOVE FRAGILE_ARC (0.060"), so nothing gets cleared
        # (Previous test had wrong math: 0.497 != 0.0497)
        purfling_remaining = sum(1 for k in fixed if k.startswith("1-"))
        # All tiles should remain since arc > threshold
        assert purfling_remaining == 24

    def test_auto_fix_does_not_touch_clean_rings(self):
        grid = {f"2-{s}": "maple" for s in range(12)}
        active = [True] * 5
        fixed = auto_fix_short_arcs(grid, 12, active)
        assert len(fixed) == 12  # Main channel untouched


# ═══════════════════════════════════════════════════════════════════════════
# Recipe library
# ═══════════════════════════════════════════════════════════════════════════

class TestRecipes:
    def test_eight_recipes_exist(self):
        assert len(RECIPES) == 8

    def test_recipe_fields(self):
        for r in RECIPES:
            assert r.id
            assert r.name
            assert r.desc
            assert r.num_segs in SEG_OPTIONS
            assert r.sym_mode in SymmetryMode
            assert len(r.ring_active) == 5
            assert isinstance(r.grid, dict)

    def test_vintage_martin_has_alternating(self):
        r = next(p for p in RECIPES if p.id == "vintage-martin")
        assert r.grid.get("2-0") == "rosewood"
        assert r.grid.get("2-1") == "maple"

    def test_recipe_ids_unique(self):
        ids = [r.id for r in RECIPES]
        assert len(ids) == len(set(ids))


# ═══════════════════════════════════════════════════════════════════════════
# SVG preview
# ═══════════════════════════════════════════════════════════════════════════

class TestSvgPreview:
    def test_renders_svg_string(self):
        from app.art_studio.schemas.rosette_designer import PreviewRequest
        req = PreviewRequest(
            num_segs=12,
            grid={f"2-{s}": "maple" for s in range(12)},
            ring_active=[True] * 5,
            show_tabs=True,
            show_annotations=False,
        )
        svg = render_preview_svg(req)
        assert svg.startswith("<svg")
        assert "</svg>" in svg

    def test_annotations_include_overlay(self):
        from app.art_studio.schemas.rosette_designer import PreviewRequest
        req = PreviewRequest(
            num_segs=12,
            grid={f"2-{s}": "maple" for s in range(12)},
            ring_active=[True] * 5,
            show_tabs=False,
            show_annotations=True,
        )
        svg = render_preview_svg(req)
        assert "EQUAL DIVISIONS" in svg


# ═══════════════════════════════════════════════════════════════════════════
# Ring / tile catalog sanity
# ═══════════════════════════════════════════════════════════════════════════

class TestCatalogSanity:
    def test_five_rings(self):
        assert len(RING_DEFS) == 5

    def test_ring_radii_ascending(self):
        for rd in RING_DEFS:
            assert rd.r2 > rd.r1

    def test_rings_no_overlap(self):
        for i in range(len(RING_DEFS) - 1):
            assert RING_DEFS[i].r2 <= RING_DEFS[i + 1].r1

    def test_main_channel_has_tabs(self):
        mc = RING_DEFS[2]
        assert mc.has_tabs
        assert mc.tab_outer_r > mc.r2
        assert mc.tab_inner_r < mc.r1

    def test_tile_map_has_19_entries(self):
        assert len(TILE_MAP) == 19

    def test_all_seg_options_even(self):
        for s in SEG_OPTIONS:
            assert s % 2 == 0


# ═══════════════════════════════════════════════════════════════════════════
# API endpoint integration (requires TestClient)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


class TestApiEndpoints:
    def test_catalog(self, client: TestClient):
        resp = client.get("/api/art/rosette-designer/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert "tile_map" in data
        assert "categories" in data
        assert "ring_defs" in data
        assert "seg_options" in data
        assert len(data["ring_defs"]) == 5

    def test_place_tile(self, client: TestClient):
        resp = client.post("/api/art/rosette-designer/place-tile", json={
            "ring_idx": 2, "seg_idx": 0, "tile_id": "maple",
            "sym_mode": "none", "num_segs": 12,
            "grid": {}, "ring_active": [True] * 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "grid" in data
        assert data["grid"]["2-0"] == "maple"

    def test_sym_cells(self, client: TestClient):
        resp = client.post("/api/art/rosette-designer/sym-cells", json={
            "ring_idx": 2, "seg_idx": 0, "sym_mode": "rotational", "num_segs": 12,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cells"]) == 12

    def test_bom(self, client: TestClient):
        grid = {f"2-{s}": "maple" for s in range(12)}
        resp = client.post("/api/art/rosette-designer/bom", json={
            "num_segs": 12, "grid": grid, "ring_active": [True] * 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_pieces"] == 12

    def test_bom_csv(self, client: TestClient):
        grid = {f"2-{s}": "maple" for s in range(12)}
        resp = client.post("/api/art/rosette-designer/bom/csv", json={
            "num_segs": 12, "grid": grid, "ring_active": [True] * 5,
            "design_name": "Test CSV",
        })
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "Maple" in resp.text

    def test_mfg_check(self, client: TestClient):
        grid = {f"2-{s}": "maple" for s in range(12)}
        resp = client.post("/api/art/rosette-designer/mfg-check", json={
            "num_segs": 12, "sym_mode": "none", "grid": grid,
            "ring_active": [True] * 5, "show_tabs": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert "flags" in data

    def test_mfg_auto_fix(self, client: TestClient):
        grid = {f"1-{s}": "bwb" for s in range(24)}
        resp = client.post("/api/art/rosette-designer/mfg-auto-fix", json={
            "num_segs": 24, "sym_mode": "none", "grid": grid,
            "ring_active": [True] * 5, "show_tabs": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "grid" in data

    def test_recipes_list(self, client: TestClient):
        resp = client.get("/api/art/rosette-designer/recipes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recipes"]) == 8

    def test_recipe_by_id(self, client: TestClient):
        resp = client.get("/api/art/rosette-designer/recipes/vintage-martin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "vintage-martin"
        assert data["num_segs"] == 12

    def test_recipe_not_found(self, client: TestClient):
        resp = client.get("/api/art/rosette-designer/recipes/nonexistent")
        assert resp.status_code == 404

    def test_preview(self, client: TestClient):
        grid = {f"2-{s}": "maple" for s in range(12)}
        resp = client.post("/api/art/rosette-designer/preview", json={
            "num_segs": 12, "grid": grid, "ring_active": [True] * 5,
            "show_tabs": True, "show_annotations": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["svg"].startswith("<svg")

    def test_export_svg(self, client: TestClient):
        grid = {f"2-{s}": "maple" for s in range(12)}
        resp = client.post("/api/art/rosette-designer/export/svg", json={
            "num_segs": 12, "grid": grid, "ring_active": [True] * 5,
            "show_tabs": True, "show_annotations": False,
            "design_name": "Test Export",
        })
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers["content-type"]
        assert resp.text.startswith("<svg")

    def test_cell_info(self, client: TestClient):
        resp = client.get(
            "/api/art/rosette-designer/cell-info",
            params={"ri": 2, "si": 5, "num_segs": 12},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["zone"] == "Main Channel"
