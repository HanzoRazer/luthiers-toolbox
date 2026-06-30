"""
Tests for Pocketing CamIntentV1 Migration (Dev Order 8J, reconstructed from bytecode).

Covers adapter, shapely-based feasibility (geometry/island rules), and the intent
router (live 200, provenance hashes, normalization, blocking, registration parity).
"""
import warnings

import pytest
from fastapi.testclient import TestClient

from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1, CamUnitsV1
from app.cam.pocketing.intent_adapter import pocket_params_from_intent, PocketIntentAdaptation
from app.cam.pocketing.feasibility import compute_pocket_feasibility, hash_feasibility_result

warnings.filterwarnings("ignore")  # silence L.1 island-subtraction UserWarning


def _route_paths(app) -> set:
    """All mounted route paths, robust to FastAPI route wrappers that don't
    expose ``.path`` directly (e.g. ``_IncludedRouter`` in fastapi>=0.137).
    Walks nested ``.routes`` so flattened or nested routes are both captured."""
    paths: set = set()
    stack = list(app.routes)
    while stack:
        route = stack.pop()
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)
        sub = getattr(route, "routes", None)
        if sub:
            stack.extend(sub)
    return paths


def _square(s=100.0):
    return [{"x": 0, "y": 0}, {"x": s, "y": 0}, {"x": s, "y": s}, {"x": 0, "y": s}]


def _valid_design() -> dict:
    return {
        "boundary": _square(),
        "islands": [],
        "pocket_depth_mm": 6.0,
        "tool_diameter_mm": 6.0,
        "stepover_percent": 50.0,
    }


# ---------------------------------------------------------------- adapter

class TestPocketingAdapter:
    def _intent(self, **ov) -> CamIntentV1:
        kw = {"mode": CamModeV1.ROUTER_3AXIS, "units": CamUnitsV1.MM,
              "design": _valid_design(), "context": {}, "options": {}}
        kw.update(ov)
        return CamIntentV1(**kw)

    def test_returns_adaptation(self):
        ad = pocket_params_from_intent(self._intent())
        assert isinstance(ad, PocketIntentAdaptation)

    def test_stepover_percent_to_fraction(self):
        ad = pocket_params_from_intent(self._intent())
        assert ad.stepover == 0.5  # 50% -> 0.5 fraction for plan_adaptive_l1

    def test_loops_boundary_plus_islands(self):
        d = _valid_design()
        d["islands"] = [{"boundary": [{"x": 40, "y": 40}, {"x": 60, "y": 40}, {"x": 60, "y": 60}]}]
        ad = pocket_params_from_intent(self._intent(design=d))
        assert len(ad.loops) == 2  # boundary + 1 island
        assert ad.loops[0][0] == (0.0, 0.0)

    def test_context_extraction(self):
        ad = pocket_params_from_intent(self._intent(context={
            "stepdown_mm": 1.5, "margin_mm": 0.5, "strategy": "Lanes",
            "smoothing_radius_mm": 0.3, "feed_rate_mm_min": 1200.0,
            "plunge_rate_mm_min": 400.0, "safe_z_mm": 8.0, "retract_z_mm": 3.0,
        }))
        assert ad.stepdown == 1.5
        assert ad.margin == 0.5
        assert ad.strategy == "Lanes"
        assert ad.feed_xy == 1200.0
        assert ad.safe_z == 8.0

    def test_defaults(self):
        ad = pocket_params_from_intent(self._intent(context={}))
        assert ad.strategy == "Spiral"
        assert ad.stepdown == 2.0
        assert ad.feed_xy == 1500.0

    def test_invalid_strategy_rejected(self):
        with pytest.raises(ValueError):
            pocket_params_from_intent(self._intent(context={"strategy": "Zigzag"}))


# ---------------------------------------------------------------- feasibility

class TestPocketingFeasibility:
    def _f(self, **ov):
        kw = dict(
            boundary=[(0, 0), (100, 0), (100, 100), (0, 100)], islands=[],
            pocket_depth_mm=6.0, tool_diameter_mm=6.0, stepover_percent=50.0,
            feed_rate_mm_min=1500.0, plunge_rate_mm_min=500.0, safe_z_mm=5.0,
            retract_z_mm=2.0, stepdown_mm=2.0, finish_allowance_mm=0.3,
        )
        kw.update(ov)
        return compute_pocket_feasibility(**kw)

    def test_valid_feasible(self):
        r = self._f()
        assert r.feasible is True
        assert r.summary["pocket_area_mm2"] == 10000.0

    def test_island_outside_boundary_blocks(self):
        r = self._f(islands=[[(200, 200), (210, 200), (210, 210)]])
        assert r.feasible is False
        assert any("island" in i and "boundary" in i for i in r.issues)

    def test_overlapping_islands_block(self):
        r = self._f(islands=[
            [(40, 40), (60, 40), (60, 60), (40, 60)],
            [(50, 50), (70, 50), (70, 70), (50, 70)],
        ])
        assert r.feasible is False
        assert any("overlap" in i for i in r.issues)

    def test_tool_below_l1_min_blocks(self):
        r = self._f(tool_diameter_mm=0.3)
        assert r.feasible is False

    def test_deep_pocket_warns(self):
        r = self._f(pocket_depth_mm=80.0, tool_diameter_mm=6.0)  # ratio 13 > 10
        assert r.feasible is True
        assert any("Deep pocket" in w for w in r.warnings)

    def test_area_minus_islands(self):
        r = self._f(islands=[[(40, 40), (60, 40), (60, 60), (40, 60)]])  # 20x20=400 hole
        # island within boundary -> feasible; area = 10000 - 400
        assert r.summary["pocket_area_mm2"] == 9600.0

    def test_hash_stable(self):
        r = self._f()
        assert hash_feasibility_result(r) == hash_feasibility_result(r)


# ---------------------------------------------------------------- router

class TestPocketingIntentRouterIntegration:
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def _req(self, **ov) -> dict:
        body = {"mode": "router_3axis", "units": "mm", "design": _valid_design(),
                "context": {"stepdown_mm": 2.0, "feed_rate_mm_min": 1500.0}, "options": {}}
        body.update(ov)
        return body

    def test_valid_request_returns_200(self, client):
        resp = client.post("/api/cam/pocketing/intent-gcode", json=self._req())
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["gcode"]
        assert "G1" in data["gcode"]
        assert data["run_id"]

    def test_metadata_and_hashes(self, client):
        data = client.post("/api/cam/pocketing/intent-gcode", json=self._req()).json()
        assert data["metadata"]["pocket_area_mm2"] == 10000.0
        assert data["metadata"]["island_count"] == 0
        assert data["metadata"]["stepover_percent"] == 50.0
        for k in ("request_sha256", "feasibility_sha256", "gcode_sha256"):
            assert len(data["hashes"][k]) == 64

    def test_issues_list_present(self, client):
        data = client.post("/api/cam/pocketing/intent-gcode", json=self._req()).json()
        assert isinstance(data["issues"], list)

    def test_island_outside_blocks_409(self, client):
        bad = self._req()
        bad["design"] = {**_valid_design(), "islands": [{"boundary": [{"x": 200, "y": 200}, {"x": 210, "y": 200}, {"x": 210, "y": 210}]}]}
        resp = client.post("/api/cam/pocketing/intent-gcode", json=bad)
        assert resp.status_code == 409, resp.text
        assert resp.json()["detail"]["error"] == "FEASIBILITY_BLOCKED"

    def test_invalid_mode_422(self, client):
        resp = client.post("/api/cam/pocketing/intent-gcode", json=self._req(mode="mill_4axis"))
        assert resp.status_code == 422

    def test_invalid_design_422(self, client):
        bad = self._req()
        bad["design"] = {"boundary": [{"x": 0, "y": 0}, {"x": 1, "y": 0}], "pocket_depth_mm": 6, "tool_diameter_mm": 6}
        resp = client.post("/api/cam/pocketing/intent-gcode", json=bad)
        assert resp.status_code == 422

    def test_registration_and_parity(self, client):
        paths = _route_paths(client.app)
        assert "/api/cam/pocketing/intent-gcode" in paths
        # sibling lanes still present (no displacement)
        assert "/api/cam/drilling/intent-gcode" in paths
        assert "/api/cam/profiling/intent-gcode" in paths
