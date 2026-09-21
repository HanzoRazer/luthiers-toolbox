"""CAM-CONTAIN-001: generator readiness is the middle authority layer.

The Stratocaster body route returned 200 with manufacturing G-code while carrying
five verified stock-destroying findings. This suite proves it no longer can, that
the refusal is explicit, and -- equally important -- that adding this layer did
not disturb the asset-authority semantics merged by #380.

It also pins two facts the containment audit established, so they cannot drift
silently: the Flying V depth validator is still NOT on the emission path, and no
route in the readiness registry is marked manufacturing-ready.

Read-only with respect to hardware: nothing here drives a machine.
"""
import uuid

import pytest

from app.cam.generator_readiness import (
    GENERATOR_READINESS,
    GeneratorReadiness,
    GeneratorReadinessBlocked,
    GeneratorReadinessRecord,
    require_generator_readiness,
    resolve_generator_readiness,
)

pytestmark = pytest.mark.allow_missing_request_id

STRAT_ROUTE = "/api/cam/guitar/stratocaster/body/gcode"
LES_PAUL_ROUTE = "/api/cam/guitar/les_paul/body/gcode"


# -----------------------------------------------------------------------------
# The state model
# -----------------------------------------------------------------------------

def test_no_route_is_marked_manufacturing_ready():
    """The registry can decline to authorize; it can never authorize.

    There is deliberately no READY/QUALIFIED member. If one is ever added, this
    test fails and forces the decision to be made deliberately.
    """
    members = {m.name for m in GeneratorReadiness}
    assert not (members & {"READY", "QUALIFIED", "AUTHORIZED", "APPROVED"}), (
        "a qualifying state was added to GeneratorReadiness; granting manufacturing "
        "readiness is an evidence-backed decision, not a default"
    )


def test_the_strat_body_generator_is_blocked():
    record = GENERATOR_READINESS["stratocaster_body"]
    assert record.readiness is GeneratorReadiness.BLOCKED
    assert record.permits_emission is False
    assert record.exit_condition, "a blocked route must state how it becomes unblocked"


def test_all_four_exposed_routes_are_represented():
    assert set(GENERATOR_READINESS) == {
        "stratocaster_body",
        "les_paul_body",
        "flying_v_body",
        "neck",
    }


def test_representation_does_not_mean_blocked():
    """Inclusion in the registry is not a blanket prohibition."""
    blocked = {k for k, v in GENERATOR_READINESS.items() if not v.permits_emission}
    assert blocked == {"stratocaster_body"}


def test_unqualified_routes_are_recorded_not_invented():
    """Flying V and neck are declared unqualified rather than assumed fine."""
    for key in ("flying_v_body", "neck"):
        record = GENERATOR_READINESS[key]
        assert record.readiness is GeneratorReadiness.REVIEW_REQUIRED
        assert record.evidence, f"{key} must cite the evidence for its state"


# -----------------------------------------------------------------------------
# Fail closed
# -----------------------------------------------------------------------------

def test_an_unknown_route_fails_closed():
    record = resolve_generator_readiness("a_route_that_does_not_exist")
    assert record.readiness is GeneratorReadiness.UNKNOWN
    assert record.permits_emission is False
    with pytest.raises(GeneratorReadinessBlocked):
        require_generator_readiness("a_route_that_does_not_exist")


def test_omitting_a_record_cannot_create_an_authorized_state():
    """Deleting the Strat record must not open the route."""
    without_strat = {k: v for k, v in GENERATOR_READINESS.items()
                     if k != "stratocaster_body"}
    with pytest.raises(GeneratorReadinessBlocked) as caught:
        require_generator_readiness("stratocaster_body", registry=without_strat)
    assert caught.value.record.readiness is GeneratorReadiness.UNKNOWN


def test_renaming_a_record_cannot_create_an_authorized_state():
    renamed = {("strat_body" if k == "stratocaster_body" else k): v
               for k, v in GENERATOR_READINESS.items()}
    with pytest.raises(GeneratorReadinessBlocked):
        require_generator_readiness("stratocaster_body", registry=renamed)


def test_blocking_is_explicit_and_carries_no_filesystem_path():
    with pytest.raises(GeneratorReadinessBlocked) as caught:
        require_generator_readiness("stratocaster_body")
    detail = caught.value.as_detail()
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["route"] == "stratocaster_body"
    assert detail["generator_readiness"] == "BLOCKED"
    assert detail["reason"] and detail["exit_condition"]
    blob = repr(detail)
    assert "instrument_geometry" not in blob and ".dxf" not in blob
    assert "C:\\" not in blob and "/app/" not in blob


def test_a_deferring_route_is_permitted_but_not_authorized():
    """GOVERNED_BY_ASSET_AUTHORITY passes this layer so #380 can do its job."""
    record = require_generator_readiness("les_paul_body")
    assert record.readiness is GeneratorReadiness.GOVERNED_BY_ASSET_AUTHORITY
    assert record.permits_emission is True


# -----------------------------------------------------------------------------
# This layer does not disturb asset authority (#380)
# -----------------------------------------------------------------------------

def test_readiness_does_not_change_dxf_authority_semantics():
    from app.instrument_geometry import dxf_authority as authority

    asset = (authority.CATALOG_ROOT / "body" / "dxf" / "electric"
             / "LesPaul_CAM_Closed.dxf")
    resolved = authority.resolve_manufacturing_authority(asset)
    assert resolved.state == authority.BLOCKED
    with pytest.raises(authority.ManufacturingAuthorityBlocked):
        authority.require_manufacturing_authority(asset)


def test_readiness_module_does_not_import_dxf_authority():
    """The two layers answer different questions and must not couple.

    Tested against the parsed import statements, not the text: the module
    docstring legitimately names the asset layer when describing the hierarchy.
    """
    import ast
    import inspect

    from app.cam import generator_readiness

    tree = ast.parse(inspect.getsource(generator_readiness))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    offenders = {m for m in imported if "dxf_authority" in m or "instrument_geometry" in m}
    assert not offenders, (
        f"generator readiness imports the asset layer {offenders}; the layers must "
        f"stay independent so neither can silently redefine the other"
    )


# -----------------------------------------------------------------------------
# The Flying V validator stays off the emission path
# -----------------------------------------------------------------------------

def test_flying_v_depth_validator_is_not_wired_into_emission():
    """Pins the audit finding. This increment must not promote it silently."""
    import importlib
    import inspect

    # The package re-exports an APIRouter under this name, so import the module.
    body_gcode_router = importlib.import_module(
        "app.routers.cam.guitar.body_gcode_router"
    )
    source = inspect.getsource(body_gcode_router)
    for name in ("validate_all_depths", "validate_neck_pocket_depth",
                 "validate_control_cavity_depth", "depth_validator"):
        assert name not in source, (
            f"{name} appeared on the emission path; wiring preflight is a separate, "
            f"un-authorized increment"
        )


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

    router_module = importlib.import_module(
        "app.routers.cam.guitar.body_gcode_router"
    )
    principal = type(
        "P", (), {"user_id": "test-user", "roles": ["owner"], "sub": "test-user"}
    )()
    app.dependency_overrides[get_current_principal] = lambda: principal
    monkeypatch.setattr(router_module, "_get_project_or_404", lambda *a, **k: object())
    monkeypatch.setattr(
        router_module, "_parse_design_state_or_422", lambda project: _State()
    )
    yield client
    app.dependency_overrides.pop(get_current_principal, None)


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
