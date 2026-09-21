"""CAM-CONTAIN-001: the containment seen through the live routes.

Split out of ``test_generator_readiness.py`` on 2026-09-21: that file crossed the
500-line ratchet, and the two halves answer different questions anyway. This half
exercises the HTTP surface -- what each route actually returns, what the inventory
discovers, and what the status endpoint advertises. The policy half next door
tests the registry and the state model without touching a route.

Read-only with respect to hardware: nothing here drives a machine.
"""
import re
import uuid

import pytest

from app.cam.generator_readiness import GENERATOR_READINESS

pytestmark = pytest.mark.allow_missing_request_id

STRAT_ROUTE = "/api/cam/guitar/stratocaster/body/gcode"
LES_PAUL_ROUTE = "/api/cam/guitar/les_paul/body/gcode"
FLYING_V_ROUTE = "/api/cam/guitar/flying_v/body/gcode"
NECK_ROUTE = "/api/cam/guitar/les_paul/neck/gcode"
ACOUSTIC_BODY_ROUTE = "/api/cam/guitar/acoustic/dreadnought/body/gcode"
ACOUSTIC_SOUNDHOLE_ROUTE = "/api/cam/guitar/acoustic/dreadnought/soundhole/gcode"
ACOUSTIC_BINDING_ROUTE = "/api/cam/guitar/acoustic/dreadnought/binding/gcode"

# Bodies that would otherwise produce a real program, so a refusal cannot be
# mistaken for a validation error on missing fields.
_ACOUSTIC_BODY_REQUEST = {
    "scale": 1.0,
    "machine": {},
    "tool_diameter_mm": 6.0,
    "total_depth_mm": 12.0,
    "stepdown_mm": 3.0,
    "tab_count": 8,
    "tab_width_mm": 15.0,
    "tab_height_mm": 3.0,
    "soundhole_diameter_mm": 100.0,
    "depth_mm": 3.0,
    "channel_depth_mm": 2.0,
    "channel_width_mm": 2.0,
}




# -----------------------------------------------------------------------------
# Through the live route
# -----------------------------------------------------------------------------

class _Status:
    value = "ready"


class _State:
    """Stand-in for parsed design state, matching the contract the real route reads.

    Mirrors test_lespaul_manufacturing_authority._State so the Les Paul regression
    is compared like for like: the route must get far enough to hit asset
    authority, which is the behaviour under test.
    """

    manufacturing_state = type("M", (), {"status": _Status()})()
    spec = type("S", (), {"scale_length_mm": 628.65})()
    body_config = None


@pytest.fixture
def authenticated(client, monkeypatch):
    import importlib

    from app.auth.deps import get_current_principal
    from app.main import app

    principal = type(
        "P", (), {"user_id": "test-user", "roles": ["owner"], "sub": "test-user"}
    )()
    app.dependency_overrides[get_current_principal] = lambda: principal
    # The neck route now lives in its own module; stub both so a route that is
    # NOT blocked still gets past project lookup.
    for dotted in ("app.routers.cam.guitar.body_gcode_router",
                   "app.routers.neck.gcode_router"):
        mod = importlib.import_module(dotted)
        monkeypatch.setattr(mod, "_get_project_or_404", lambda *a, **k: object())
        monkeypatch.setattr(
            mod, "_parse_design_state_or_422", lambda project: _State()
        )
    yield client
    app.dependency_overrides.pop(get_current_principal, None)


def test_shared_project_lookup_helper_executes_without_missing_imports(monkeypatch):
    """Exercise the real shared helper so router monkeypatches cannot hide import drift."""
    from app.routers import _project_gcode_common as common

    project_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    project = type("ProjectStub", (), {"archived_at": None, "owner_id": owner_id})()
    db = type("DbStub", (), {"get": lambda self, model, pid: project})()
    principal = type("PrincipalStub", (), {"user_id": owner_id})()

    assert common._get_project_or_404(str(project_id), principal, db) is project


def test_strat_route_cannot_emit_gcode(authenticated):
    """The witnessed emission is stopped."""
    response = authenticated.post(f"{STRAT_ROUTE}?project_id={uuid.uuid4()}")
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["generator_readiness"] == "BLOCKED"
    body = response.text
    for token in ("G0", "G1 ", "M3", "M30", "G21", "G90"):
        assert token not in body, f"G-code token {token!r} escaped a blocked route"


def test_strat_route_does_no_project_work_when_blocked(authenticated, monkeypatch):
    """The gate is the first statement: a blocked route touches no project."""
    import importlib

    router_module = importlib.import_module(
        "app.routers.cam.guitar.body_gcode_router"
    )
    calls = []
    monkeypatch.setattr(
        router_module,
        "_get_project_or_404",
        lambda *a, **k: calls.append(a) or object(),
    )
    authenticated.post(f"{STRAT_ROUTE}?project_id={uuid.uuid4()}")
    assert calls == [], "project lookup ran despite the route being blocked"


def test_les_paul_route_still_refuses_with_asset_authority(authenticated):
    """#380's refusal must reach the client unchanged, not be shadowed by readiness."""
    response = authenticated.post(f"{LES_PAUL_ROUTE}?project_id={uuid.uuid4()}")
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "DXF_MANUFACTURING_AUTHORITY_BLOCKED", (
        "generator readiness shadowed the asset-authority refusal"
    )
    assert detail["manufacturing_authority"] == "BLOCKED"
    assert detail["disposition"] == "UNADJUDICATED"
    assert "G0" not in response.text and "M3" not in response.text


def test_flying_v_route_refuses_while_review_required(authenticated):
    """Ungated and unqualified must not mean "emits anyway"."""
    response = authenticated.post(f"{FLYING_V_ROUTE}?project_id={uuid.uuid4()}")
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["route"] == "flying_v_body"
    assert detail["generator_readiness"] == "REVIEW_REQUIRED"
    for token in ("G0", "G1 ", "M3", "M30", "G21", "G90"):
        assert token not in response.text, f"G-code token {token!r} escaped"


def test_neck_route_refuses_while_review_required(authenticated):
    response = authenticated.post(f"{NECK_ROUTE}?project_id={uuid.uuid4()}")
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["route"] == "neck"
    assert detail["generator_readiness"] == "REVIEW_REQUIRED"
    for token in ("G0", "G1 ", "M3", "M30", "G21", "G90"):
        assert token not in response.text, f"G-code token {token!r} escaped"


# Every G-code route under the guitar prefix is behind generator readiness.
# The set is empty on purpose: an entry here is a declared hole in containment,
# and there are none. test_declared_gaps_are_not_silently_gated keeps it honest.
UNGATED_GUITAR_GCODE_ROUTES: set = set()

GATED_GUITAR_GCODE_ROUTES = {
    "stratocaster/body/gcode",
    "les_paul/body/gcode",
    "flying_v/body/gcode",
    "{model_id}/neck/gcode",
    "acoustic/{style}/body/gcode",
    "acoustic/{style}/soundhole/gcode",
    "acoustic/{style}/binding/gcode",
}


def _discover_guitar_gcode_routes() -> set:
    """Every POST /...gcode path under the guitar prefix, as the live app serves it.

    Enumerated from the OpenAPI schema rather than ``app.routes``. Starlette 0.49
    stopped flattening included routers into ``app.routes`` -- they appear as
    ``_IncludedRouter`` proxies with no ``.path`` -- so walking ``app.routes``
    raised AttributeError, and merely guarding with ``hasattr`` would have made
    this inventory silently EMPTY. The schema is the surface clients actually see.
    """
    from app.main import app

    prefix = "/api/cam/guitar/"
    schema = app.openapi()
    return {
        path[len(prefix):]
        for path, operations in schema["paths"].items()
        if path.startswith(prefix)
        and "post" in operations
        and path.endswith("/gcode")
    }


def test_route_discovery_is_not_vacuous():
    """The guard below is worthless if discovery returns nothing. Prove it doesn't."""
    discovered = _discover_guitar_gcode_routes()
    assert discovered, (
        "route discovery found no guitar G-code routes at all -- the enumeration "
        "is broken, not the surface; a coverage guard that cannot see the routes "
        "cannot fail on them"
    )
    assert len(discovered) >= len(GATED_GUITAR_GCODE_ROUTES)


def test_current_guitar_manufacturing_routes_have_readiness_records():
    """Pin coverage so a new guitar manufacturing route cannot silently bypass readiness."""
    discovered = _discover_guitar_gcode_routes()
    expected_paths = GATED_GUITAR_GCODE_ROUTES | UNGATED_GUITAR_GCODE_ROUTES
    assert discovered == expected_paths, (
        "guitar manufacturing route surface changed; classify every new/removed "
        "route in generator readiness (or add it to UNGATED_GUITAR_GCODE_ROUTES "
        "with a reason) before updating this inventory"
    )
    assert set(GENERATOR_READINESS) == {
        "stratocaster_body", "les_paul_body", "flying_v_body", "neck",
        "acoustic_body", "acoustic_soundhole", "acoustic_binding",
    }


def test_declared_gaps_are_not_silently_gated():
    """The declared gaps must stay declared: absent from the registry, present in the surface.

    If someone later gates an acoustic route, this fails and forces the inventory
    to be updated in the same change -- which is the point of declaring the gap.
    """
    discovered = _discover_guitar_gcode_routes()
    assert UNGATED_GUITAR_GCODE_ROUTES <= discovered, (
        "a declared-ungated route vanished from the surface; remove it from "
        "UNGATED_GUITAR_GCODE_ROUTES in the same change"
    )
    assert not UNGATED_GUITAR_GCODE_ROUTES, (
        "containment now covers every guitar G-code route; adding an entry here "
        "reopens a hole and must be justified in the same change"
    )
    assert GATED_GUITAR_GCODE_ROUTES.isdisjoint(UNGATED_GUITAR_GCODE_ROUTES)
    assert not (UNGATED_GUITAR_GCODE_ROUTES & set(GENERATOR_READINESS)), (
        "an acoustic route is now in the readiness registry; move it out of "
        "UNGATED_GUITAR_GCODE_ROUTES and into GATED_GUITAR_GCODE_ROUTES"
    )


def test_status_does_not_advertise_contained_routes_cam_ready(authenticated):
    response = authenticated.get("/api/cam/guitar/status")
    assert response.status_code == 200, response.text
    endpoints = response.json()["gen4_endpoints"]
    assert set(endpoints) == {
        "stratocaster", "les_paul", "flying_v", "neck",
        "acoustic_body", "acoustic_soundhole", "acoustic_binding",
    }
    assert all(item["cam_ready"] is False for item in endpoints.values())


@pytest.mark.parametrize(
    "route, route_key",
    [
        (ACOUSTIC_BODY_ROUTE, "acoustic_body"),
        (ACOUSTIC_SOUNDHOLE_ROUTE, "acoustic_soundhole"),
        (ACOUSTIC_BINDING_ROUTE, "acoustic_binding"),
    ],
)
def test_acoustic_route_refuses_generation(client, route, route_key):
    """Each acoustic route refuses under the current non-READY state, and emits nothing.

    These returned .nc downloads before CAM-CONTAIN-001 was widened on the
    2026-09-21 owner ruling. The request bodies are complete, so a 422 here is
    the readiness refusal and not a validation error on missing fields.
    """
    response = client.post(route, json=_ACOUSTIC_BODY_REQUEST)
    assert response.status_code == 422, f"{route}: {response.text}"
    detail = response.json()["detail"]
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED", route
    assert detail["route"] == route_key, route
    assert detail["generator_readiness"] in {"BLOCKED", "REVIEW_REQUIRED"}, route
    assert detail["reason"] and detail["exit_condition"], route


@pytest.mark.parametrize(
    "route",
    [ACOUSTIC_BODY_ROUTE, ACOUSTIC_SOUNDHOLE_ROUTE, ACOUSTIC_BINDING_ROUTE],
)
def test_acoustic_refusal_emits_no_manufacturing_content(client, route):
    """No program reaches the client: no .nc download, no gcode field, no motion lines.

    Deliberately NOT a substring scan of the whole body. The readiness reason for
    acoustic_body quotes the offending program header verbatim as evidence --
    "( Tabs: 16 x ... )" -- so a naive scan flags the explanation as a leak. The
    check is therefore structural: the response is a JSON refusal carrying no
    program payload, and no field of it contains a G-code motion line.
    """
    response = client.post(route, json=_ACOUSTIC_BODY_REQUEST)
    assert response.status_code == 422

    # Not a file download
    assert "attachment" not in response.headers.get("content-disposition", "")
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()
    assert set(payload) == {"detail"}, f"{route}: unexpected top-level keys {sorted(payload)}"
    assert "gcode" not in payload["detail"]
    assert "nc" not in payload["detail"]

    # No emitted program: a G-code line starts with a motion/spindle word at line start.
    program_line = re.compile(r"^\s*(G0|G1|G2|G3|G17|G20|G21|G90|M3|M5|M30)\b", re.MULTILINE)
    for field in ("code", "route", "generator_readiness"):
        assert not program_line.search(str(payload["detail"].get(field, ""))), field
    assert payload["detail"]["code"] == "GENERATOR_READINESS_BLOCKED"


def test_acoustic_routes_refuse_before_the_generator_is_constructed():
    """The gate is the first statement, so no generator is built for a refused request.

    Placement matters: constructing the generator is where parameters are
    interpreted, and a refused request must not get that far.
    """
    import importlib
    import inspect

    # NB: ``from app.routers.cam.guitar import acoustic_cam_router`` binds the
    # re-exported APIRouter, not the module -- the package __init__ shadows it.
    mod = importlib.import_module("app.routers.cam.guitar.acoustic_cam_router")

    for fn_name, key in (
        ("generate_body_perimeter", "acoustic_body"),
        ("generate_soundhole", "acoustic_soundhole"),
        ("generate_binding_channel", "acoustic_binding"),
    ):
        fn = getattr(mod, fn_name)
        src = inspect.getsource(getattr(fn, "_original_func", fn))
        gate_at = src.index(f'_readiness_gate("{key}")')
        make_at = src.index("_create_generator(")
        assert gate_at < make_at, (
            f"{fn_name}: readiness gate must precede generator construction"
        )


def test_every_exposed_route_now_fails_closed(authenticated):
    """The whole CAM surface refuses: three at this layer, one at asset authority."""
    expected = {
        STRAT_ROUTE: "GENERATOR_READINESS_BLOCKED",
        FLYING_V_ROUTE: "GENERATOR_READINESS_BLOCKED",
        NECK_ROUTE: "GENERATOR_READINESS_BLOCKED",
        LES_PAUL_ROUTE: "DXF_MANUFACTURING_AUTHORITY_BLOCKED",
    }
    for route, code in expected.items():
        response = authenticated.post(f"{route}?project_id={uuid.uuid4()}")
        assert response.status_code == 422, f"{route}: {response.text}"
        assert response.json()["detail"]["code"] == code, route
        assert "G0" not in response.text and "M3" not in response.text, route
