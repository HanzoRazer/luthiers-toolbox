"""MANUFACTURING-SPINE-001 — Profiling vertical spine witness.

Freezes the *current* runtime truth of the Profiling manufacturing path:

    Q1  governed vertical path (authority before generation)   -> PROVEN here
    Q2  controlled production surface                          -> NOT PROVEN (MS-F01)
    Q3  machine-ready release claim                            -> NOT PROVEN (MS-F03/F04)

Scope discipline (owner ruling, MANUFACTURING-SPINE-001 G4):

* This module ADDS NO REQUIREMENTS. Where a capability is absent today
  (machine/post identity, post-generation G-code validation) it is documented
  as absent, not asserted as if it existed. Turning those into failing
  assertions would manufacture a requirement that forces unauthorized
  production changes.
* MS-F01 (the ungoverned ``/api/v1/cam/profile`` route) is FROZEN as a fact,
  not failed. We already know it exists; a red suite would add no information
  and would block unrelated work. When a remediation order closes it, the
  expected classification here changes deliberately.
* No production module is modified by this increment.

Placement: this lives beside ``test_profiling_authority_convergence.py``
(RMOS-PROFILING-CONVERGE-001) because it asserts the same authority boundary
end to end. No new test directory was created for it.
"""

from __future__ import annotations

import json

import pytest


# Four-point closed rectangle: the smallest deterministic specimen that clears
# the >=3-point guard in generate_profile_gcode and exercises B01..B07 with
# schema defaults everywhere else. Same shape family as the fixtures used by
# tests/cam/test_profile_intent_migration.py.
SPECIMEN_CONTOUR = [
    {"x": 0.0, "y": 0.0},
    {"x": 100.0, "y": 0.0},
    {"x": 100.0, "y": 60.0},
    {"x": 0.0, "y": 60.0},
]

GOVERNED_PATH = "/api/cam/profiling/gcode"
BYPASS_PATH = "/api/v1/cam/profile"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Isolated TestClient — all persistent state redirected to tmp_path."""
    runs = tmp_path / "rmos_runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "_index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ART_STUDIO_DB_PATH", str(tmp_path / "art.db"))
    monkeypatch.setenv("ENV", "test")
    try:
        from app.rmos.runs_v2 import store_api as runs_v2_store_api

        runs_v2_store_api._default_store = None
    except ImportError:
        pass

    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def _specimen(**overrides):
    body = {"contour": SPECIMEN_CONTOUR}
    body.update(overrides)
    return body


def _looks_like_gcode(text: str) -> bool:
    return "G21" in text or "G0" in text or "G1" in text


# ---------------------------------------------------------------- MS-B01
def test_ms_b01_governed_profiling_route_is_mounted(client):
    """The governed route is reachable in the live app, not merely importable.

    aggregator.py wraps the profiling import in ``except ImportError`` (MS-F02),
    so an import failure would silently unmount this route while the app still
    starts.

    Reachability is proven by REQUEST, not by enumerating ``app.routes``. This
    application wraps included routers in a custom ``_IncludedRouter`` object,
    so neither ``app.routes`` nor the repo's own ``/api/_meta/routing-truth``
    surface reports these paths -- enumeration reports absence for a route that
    demonstrably answers. A non-404 response is the truthful mount witness.
    """
    r = client.post(GOVERNED_PATH, json=_specimen())
    assert r.status_code != 404, f"{GOVERNED_PATH} is not mounted (404)"
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------- MS-B02..B05
def test_ms_b02_b05_specimen_traverses_governed_path(client):
    """Valid specimen -> 200 + real G-code + authority metadata."""
    r = client.post(GOVERNED_PATH, json=_specimen())
    assert r.status_code == 200, r.text
    assert _looks_like_gcode(r.text), r.text[:200]

    # Authority metadata is emitted with the release, not reconstructed later.
    assert r.headers.get("X-ToolBox-Lane") == "governed"
    assert r.headers.get("X-Run-ID")
    assert r.headers.get("X-GCode-SHA256")
    assert r.headers.get("X-Risk-Level") in {"GREEN", "YELLOW"}


def test_ms_b03_authority_precedes_generation(client, monkeypatch):
    """RMOS evaluation must run BEFORE ProfileToolpath.generate().

    Ordering is observed, not inferred: both boundaries are wrapped and the
    call sequence is recorded. The real implementations still run.
    """
    order: list[str] = []

    # NOTE: ``app.cam.routers.profiling.__init__`` does
    # ``from .profile_router import router as profile_router``, which rebinds
    # that name to the APIRouter object and shadows the submodule. Import the
    # module explicitly rather than by attribute access.
    import importlib

    pr_mod = importlib.import_module("app.cam.routers.profiling.profile_router")
    from app.cam.profiling import profile_toolpath as tp_mod

    real_feasibility = pr_mod.compute_feasibility_internal
    real_generate = tp_mod.ProfileToolpath.generate

    def spy_feasibility(*a, **kw):
        order.append("authority")
        return real_feasibility(*a, **kw)

    def spy_generate(self, *a, **kw):
        order.append("generate")
        return real_generate(self, *a, **kw)

    monkeypatch.setattr(pr_mod, "compute_feasibility_internal", spy_feasibility)
    monkeypatch.setattr(tp_mod.ProfileToolpath, "generate", spy_generate)

    r = client.post(GOVERNED_PATH, json=_specimen())
    assert r.status_code == 200, r.text
    assert "authority" in order and "generate" in order, order
    assert order.index("authority") < order.index("generate"), order


def test_ms_b03_blocking_authority_releases_no_gcode(client, monkeypatch):
    """A blocking safety decision must yield 409 and no machine output."""
    from app.rmos.policies.safety_policy import SafetyPolicy

    monkeypatch.setattr(SafetyPolicy, "should_block", classmethod(lambda cls, level: True))

    r = client.post(GOVERNED_PATH, json=_specimen())
    assert r.status_code == 409, r.text
    assert not _looks_like_gcode(r.text)
    assert "X-GCode-SHA256" not in r.headers, "blocked run must not emit a G-code hash"
    detail = r.json().get("detail") or {}
    assert detail.get("error") == "SAFETY_BLOCKED"
    assert detail.get("run_id"), "a blocked run is still audited"


# ---------------------------------------------------------------- MS-B07
def test_ms_b07_released_output_is_traceable_to_its_run(client):
    """Released G-code can be tied back to the authority decision that allowed it.

    Custody is DURABLE (persisted RunArtifact); traceability is via the run id
    and the G-code hash emitted with the release.
    """
    import hashlib

    r = client.post(GOVERNED_PATH, json=_specimen())
    assert r.status_code == 200, r.text

    run_id = r.headers["X-Run-ID"]
    declared = r.headers["X-GCode-SHA256"]

    # The declared hash describes the bytes actually released.
    assert hashlib.sha256(r.text.encode("utf-8")).hexdigest() == declared

    from app.rmos.runs_v2.store import _get_default_store

    artifact = _get_default_store().get(run_id)
    assert artifact is not None, f"no persisted RunArtifact for run {run_id}"

    payload = artifact if isinstance(artifact, dict) else artifact.model_dump()
    blob = json.dumps(payload, default=str)
    assert declared in blob, "released G-code hash is not recorded in the run artifact"
    assert "feasibility" in payload or "feasibility" in blob


# ---------------------------------------------------------------- MS-F01
def test_ms_f01_ungoverned_bypass_route_is_frozen_as_present(client):
    """MS-F01: POST /api/v1/cam/profile is mounted and does NOT traverse the spine.

    This asserts the DEFECT AS IT CURRENTLY STANDS. It is deliberately not a
    failing test: the bypass is known, and failing here would neither add
    information nor be repairable under this authorization.

    When a remediation order closes MS-F01, this test is expected to change --
    that change is the signal that the bypass was actually closed.
    """
    r = client.post(
        BYPASS_PATH,
        json={
            "loops": [{"pts": [[0, 0], [100, 0], [100, 60], [0, 60]]}],
            "tool_diameter_mm": 6.35,
            "depth_mm": 6.0,
        },
    )
    assert r.status_code != 404, "MS-F01 route missing; classification must be re-derived"
    assert r.status_code == 200, r.text
    body = r.json()

    # It answers, and it emits G-code-shaped text ...
    data = body.get("data") or {}
    assert "gcode_preview" in data

    # ... with none of the governed lane's authority evidence.
    assert "X-Run-ID" not in r.headers
    assert "X-GCode-SHA256" not in r.headers
    assert r.headers.get("X-ToolBox-Lane") != "governed"
    assert "run_id" not in body and "run_id" not in data
    assert "feasibility" not in body and "feasibility" not in data


# ---------------------------------------------------------------- MS-F03 / MS-F04
def test_ms_f03_f04_absent_capabilities_are_documented_not_required(client):
    """MS-F03/MS-F04: record what the governed release does NOT carry today.

    Machine/post identity and post-generation G-code validation are absent.
    This test freezes that absence so a future increment that adds them is
    visible as a deliberate change -- it does not demand them now.
    """
    r = client.post(GOVERNED_PATH, json=_specimen())
    assert r.status_code == 200, r.text

    header_blob = " ".join(f"{k}:{v}" for k, v in r.headers.items()).lower()

    # MS-F03 -- no machine or postprocessor identity travels with the release.
    assert "machine" not in header_blob
    assert "post-id" not in header_blob and "postprocessor" not in header_blob

    # MS-F04 -- the only validation in the path is audit-record completeness
    # (validate_and_persist), which never raises and cannot block release.
    # There is no verdict header describing the emitted G-code itself.
    assert "x-gcode-validation" not in header_blob
    assert "x-validation" not in header_blob
