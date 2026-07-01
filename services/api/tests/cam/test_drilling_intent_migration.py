"""
Tests for Drilling CamIntentV1 Migration (Dev Order 8I).

Covers the intent adapter, feasibility (incl. the mandatory peck rule), and the
intent router endpoint (live 200, provenance hashes, normalization, blocking,
legacy parity).
"""
import pytest
from fastapi.testclient import TestClient

from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1, CamUnitsV1
from app.cam.drilling.intent_adapter import drilling_params_from_intent
from app.cam.drilling.peck_cycle import DrillConfig, DrillHole
from app.cam.drilling.feasibility import (
    compute_drilling_feasibility,
    hash_feasibility_result,
)


def _route_registered(client, path: str) -> bool:
    """True iff ``path`` is a mounted route, independent of HTTP method or
    FastAPI's internal route-tree shape. An unmounted path yields 404; a mounted
    one yields 200/405/409/422 for a probe POST.

    Deliberately NOT ``{r.path for r in app.routes}`` introspection: under the
    repo's fastapi>=0.137 pin, nested ``include_router`` keeps ``_IncludedRouter``
    wrappers whose children carry *relative* paths, so an assembled path such as
    ``/api/cam/drilling/intent-gcode`` never appears as a single string in
    ``app.routes`` (and the wrappers themselves have no ``.path``). The endpoints
    resolve and serve — the live-200 tests in this class prove it; only naive
    path-string introspection could not see them. Probing reachability tests the
    property the parity check actually cares about and is robust to fastapi
    internals."""
    return client.post(path, json={}).status_code != 404


def _valid_design() -> dict:
    return {
        "holes": [{"x": 0, "y": 0}, {"x": 10.5, "y": 0, "label": "s2"}],
        "hole_depth_mm": 20.0,
        "hole_diameter_mm": 3.0,
        "peck_drilling": True,
        "peck_depth_mm": 5.0,
    }


# ---------------------------------------------------------------- adapter

class TestDrillingIntentAdapter:
    def _intent(self, **ov) -> CamIntentV1:
        kw = {
            "mode": CamModeV1.ROUTER_3AXIS,
            "units": CamUnitsV1.MM,
            "design": _valid_design(),
            "context": {},
            "options": {},
        }
        kw.update(ov)
        return CamIntentV1(**kw)

    def test_returns_holes_and_config(self):
        holes, config = drilling_params_from_intent(self._intent())
        assert isinstance(holes, list) and len(holes) == 2
        assert isinstance(holes[0], DrillHole)
        assert isinstance(config, DrillConfig)

    def test_design_fields_into_config(self):
        _, config = drilling_params_from_intent(self._intent())
        assert config.hole_depth_mm == 20.0
        assert config.peck_depth_mm == 5.0
        assert config.drill_diameter_mm == 3.0
        assert config.use_canned_cycle is True  # peck_drilling -> canned cycle

    def test_holes_mapped_with_diameter(self):
        holes, _ = drilling_params_from_intent(self._intent())
        assert holes[0].x == 0 and holes[0].y == 0
        assert holes[1].label == "s2"
        assert all(h.diameter_mm == 3.0 for h in holes)

    def test_context_fields_extracted(self):
        intent = self._intent(context={
            "feed_rate_mm_min": 250.0,
            "spindle_rpm": 3000,
            "safe_z_mm": 12.0,
            "retract_z_mm": 3.0,
            "dwell_ms": 100,
        })
        _, config = drilling_params_from_intent(intent)
        assert config.feed_rate == 250.0
        assert config.spindle_rpm == 3000
        assert config.safe_z_mm == 12.0
        assert config.retract_z_mm == 3.0
        assert config.dwell_ms == 100

    def test_defaults_for_missing_context(self):
        _, config = drilling_params_from_intent(self._intent(context={}))
        assert config.feed_rate == 100.0
        assert config.spindle_rpm == 2000
        assert config.safe_z_mm == 10.0
        assert config.retract_z_mm == 2.0

    def test_retract_height_alias(self):
        _, config = drilling_params_from_intent(self._intent(context={"retract_height_mm": 4.0}))
        assert config.retract_z_mm == 4.0

    def test_invalid_context_raises_valueerror(self):
        with pytest.raises(ValueError):
            drilling_params_from_intent(self._intent(context={"feed_rate_mm_min": "fast"}))


# ---------------------------------------------------------------- feasibility

class TestDrillingFeasibility:
    def _f(self, **ov):
        kw = dict(
            hole_depth_mm=20.0, hole_diameter_mm=3.0, peck_drilling=True,
            peck_depth_mm=5.0, hole_count=2, feed_rate_mm_min=100.0,
            spindle_rpm=2000, safe_z_mm=10.0, retract_z_mm=2.0,
        )
        kw.update(ov)
        return compute_drilling_feasibility(**kw)

    def test_valid_is_feasible(self):
        r = self._f()
        assert r.feasible is True
        assert r.risk_level in ("low", "medium")

    def test_peck_ge_depth_blocks(self):
        r = self._f(peck_depth_mm=20.0)  # == hole_depth
        assert r.feasible is False
        assert r.risk_level == "blocked"
        assert any("peck_depth_mm" in i for i in r.issues)

    def test_peck_gt_depth_blocks(self):
        r = self._f(peck_depth_mm=25.0)
        assert r.feasible is False

    def test_nonpositive_peck_blocks(self):
        r = self._f(peck_depth_mm=0.0)
        assert r.feasible is False

    def test_nonpositive_diameter_blocks(self):
        r = self._f(hole_diameter_mm=0.0)
        assert r.feasible is False

    def test_zero_holes_blocks(self):
        r = self._f(hole_count=0)
        assert r.feasible is False

    def test_deep_hole_warns_not_blocks(self):
        # depth 50 / dia 3 = 16.7 ratio > 10, peck 5 < 50 (valid)
        r = self._f(hole_depth_mm=50.0, peck_depth_mm=5.0, hole_diameter_mm=3.0)
        assert r.feasible is True
        assert any("Deep hole" in w for w in r.warnings)

    def test_hash_stable(self):
        r = self._f()
        assert hash_feasibility_result(r) == hash_feasibility_result(r)


# ---------------------------------------------------------------- router

class TestDrillingIntentRouterIntegration:
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def _req(self, **ov) -> dict:
        body = {
            "mode": "router_3axis",
            "units": "mm",
            "design": _valid_design(),
            "context": {"feed_rate_mm_min": 100.0, "spindle_rpm": 2000},
            "options": {},
        }
        body.update(ov)
        return body

    def test_valid_request_returns_200(self, client):
        resp = client.post("/api/cam/drilling/intent-gcode", json=self._req())
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["gcode"]
        assert data["run_id"]
        assert data["metadata"]["hole_count"] == 2

    def test_response_carries_provenance_hashes(self, client):
        data = client.post("/api/cam/drilling/intent-gcode", json=self._req()).json()
        for k in ("request_sha256", "feasibility_sha256", "gcode_sha256"):
            assert k in data["hashes"] and len(data["hashes"][k]) == 64

    def test_response_has_issues_list(self, client):
        # normalization report surfaced (no silent normalization)
        data = client.post("/api/cam/drilling/intent-gcode", json=self._req()).json()
        assert "issues" in data and isinstance(data["issues"], list)

    def test_peck_rule_blocks_409(self, client):
        bad = self._req()
        bad["design"] = {**_valid_design(), "peck_depth_mm": 20.0}  # == hole_depth
        resp = client.post("/api/cam/drilling/intent-gcode", json=bad)
        assert resp.status_code == 409, resp.text
        assert resp.json()["detail"]["error"] == "FEASIBILITY_BLOCKED"

    def test_invalid_mode_422(self, client):
        resp = client.post("/api/cam/drilling/intent-gcode", json=self._req(mode="mill_4axis"))
        assert resp.status_code == 422

    def test_invalid_design_422(self, client):
        bad = self._req()
        bad["design"] = {"holes": [], "hole_depth_mm": 20, "hole_diameter_mm": 3, "peck_depth_mm": 5}
        resp = client.post("/api/cam/drilling/intent-gcode", json=bad)
        assert resp.status_code == 422

    def test_legacy_routes_unchanged(self, client):
        # parity: the intent lane did not displace legacy drilling routes
        for path in (
            "/api/cam/drilling/intent-gcode",
            "/api/cam/drilling/gcode",
            "/api/cam/drilling/pattern/gcode",
        ):
            assert _route_registered(client, path), f"route not mounted: {path}"
