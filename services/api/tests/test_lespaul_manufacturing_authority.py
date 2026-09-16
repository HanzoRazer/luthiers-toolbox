"""
DXF-RUNTIME-AUTHORITY-001: the Les Paul path obeys catalog manufacturing authority.

`LesPaul_CAM_Closed.dxf` is UNADJUDICATED in the registry, and until PR #378 the
runtime loaded it anyway. Every entry point must now refuse it, and the refusal
must reach an HTTP caller as a deterministic 422 with no G-code produced.

Entry points covered: the BodyGenerator factory (for_model), direct construction of
LesPaulBodyGenerator (so bypassing the factory evades nothing), from_project(),
and the live route. The route test stubs only project lookup and design-state
parsing - auth, routing, the generator selection and the error mapping are the
real ones.
"""
import uuid
from pathlib import Path

import pytest

from app.generators.body_generator import BodyGenerator
from app.generators.lespaul_body_generator import LesPaulBodyGenerator
from app.instrument_geometry import dxf_authority as authority

pytestmark = pytest.mark.allow_missing_request_id

LES_PAUL = authority.CATALOG_ROOT / "body" / "dxf" / "electric" / "LesPaul_CAM_Closed.dxf"
ROUTE = "/api/cam/guitar/les_paul/body/gcode"


def test_the_factory_cannot_build_a_generator_on_a_blocked_template():
    """T1: the principal regression witness, through the documented entry point."""
    with pytest.raises(authority.ManufacturingAuthorityBlocked) as caught:
        BodyGenerator.for_model("lespaul")
    assert caught.value.asset == "body/dxf/electric/LesPaul_CAM_Closed.dxf"
    assert caught.value.disposition == "UNADJUDICATED"


def test_direct_construction_cannot_bypass_the_factory():
    """T2: the check sits at the generator, not above it."""
    with pytest.raises(authority.ManufacturingAuthorityBlocked):
        LesPaulBodyGenerator(str(LES_PAUL))


def test_the_blocked_template_is_never_read():
    """The refusal happens before geometry is loaded, not after."""
    reads = []
    import app.generators.lespaul_body_generator as module
    real_reader = module.LesPaulDXFReader

    class _Recording(real_reader):
        def __init__(self, filepath):
            reads.append(filepath)
            super().__init__(filepath)

    module.LesPaulDXFReader = _Recording
    try:
        with pytest.raises(authority.ManufacturingAuthorityBlocked):
            LesPaulBodyGenerator(str(LES_PAUL))
    finally:
        module.LesPaulDXFReader = real_reader
    assert reads == [], "the DXF was opened despite being blocked"


class _Status:
    value = "ready"


class _State:
    manufacturing_state = type("M", (), {"status": _Status()})()
    spec = type("S", (), {"scale_length_mm": 628.65})()
    body_config = None


def test_from_project_refuses_and_does_not_substitute_another_asset(monkeypatch):
    """T6: the fallback to LesPaul_body.dxf is gone, not merely blocked afterwards."""
    with pytest.raises(authority.ManufacturingAuthorityBlocked) as caught:
        LesPaulBodyGenerator.from_project(_State())
    assert caught.value.asset.endswith("LesPaul_CAM_Closed.dxf")

    # With the template absent, from_project must refuse rather than pick another file.
    monkeypatch.setattr(Path, "exists", lambda self: False)
    with pytest.raises(ValueError) as fallback:
        LesPaulBodyGenerator.from_project(_State())
    message = str(fallback.value)
    assert "unavailable" in message
    assert "LesPaul_body" not in message


def test_no_fallback_target_is_authorized_either():
    """Even if something did substitute it, LesPaul_body.dxf is recorded too."""
    alt = LES_PAUL.parent / "LesPaul_body.dxf"
    assert authority.resolve_manufacturing_authority(alt).state == authority.BLOCKED


# -----------------------------------------------------------------------------
# Through the route
# -----------------------------------------------------------------------------

@pytest.fixture
def authenticated(client, monkeypatch):
    """Real app, real route, real auth dependency override; project lookup stubbed."""
    import importlib

    from app.main import app
    from app.auth.deps import get_current_principal

    # The package re-exports an APIRouter under this name, so import the module itself.
    router_module = importlib.import_module("app.routers.cam.guitar.body_gcode_router")

    principal = type("P", (), {"user_id": "test-user", "roles": ["owner"], "sub": "test-user"})()
    app.dependency_overrides[get_current_principal] = lambda: principal
    monkeypatch.setattr(router_module, "_get_project_or_404", lambda *a, **k: object())
    monkeypatch.setattr(router_module, "_parse_design_state_or_422", lambda project: _State())
    yield client
    app.dependency_overrides.pop(get_current_principal, None)


def test_route_returns_a_deterministic_422_and_no_gcode(authenticated):
    """T11: route -> generator selection -> authority block -> client refusal."""
    response = authenticated.post(f"{ROUTE}?project_id={uuid.uuid4()}")
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "DXF_MANUFACTURING_AUTHORITY_BLOCKED"
    assert detail["asset"] == "body/dxf/electric/LesPaul_CAM_Closed.dxf"
    assert detail["manufacturing_authority"] == "BLOCKED"
    assert detail["disposition"] == "UNADJUDICATED"
    assert "exit_condition" in detail
    assert "G0" not in response.text and "M3" not in response.text  # no G-code escaped
    assert "instrument_geometry" not in response.text  # no filesystem path leaked
