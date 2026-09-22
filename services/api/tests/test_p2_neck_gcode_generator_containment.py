"""LTB-REMEDIATE-P2: NeckGCodeGenerator behind its own authority boundary.

``POST /api/neck/gcode/generate`` and ``/download`` answered an uncredentialed
default request with a 460-record program (G20, inch) -- byte-identical between
the two -- carrying 146 G0 rapids below the workpiece top, reaching
Z=-0.8371in (-21.26mm). Both reach ``NeckGCodeGenerator``.

There are three neck implementations, and each now has its own identity:

=============================================  ======================  ======================
route                                          implementation          readiness key
=============================================  ======================  ======================
``/api/cam/guitar/{model_id}/neck/gcode``      inline router code      ``neck``
``/api/neck/gcode/{generate,download}``        ``NeckGCodeGenerator``  ``neck_gcode_generator``
``/api/cam-workspace/neck/generate{,-full}``   ``NeckPipeline``        ``neck_pipeline_full``
=============================================  ======================  ======================

**Scope.** This contains the two routes. It does NOT correct the toolpath, does
NOT consolidate the implementations, and claims NO functional equivalence
between them. ``neck_gcode_generator`` stays non-emitting.

Read-only with respect to hardware: nothing here drives a machine.
"""
import inspect
import re

import pytest
from fastapi import APIRouter

from app.cam.generator_readiness import (
    GENERATOR_READINESS,
    GeneratorReadiness,
    resolve_generator_readiness,
)

pytestmark = pytest.mark.allow_missing_request_id

ROUTE_KEY = "neck_gcode_generator"
GENERATE = "/api/neck/gcode/generate"
DOWNLOAD = "/api/neck/gcode/download"
BOTH = [GENERATE, DOWNLOAD]

#: The POST routes on the neck gcode router that emit a program. Declared, so
#: that adding, renaming or removing one fails the inventory until classified.
DECLARED_EMITTING = {"/gcode/generate", "/gcode/download"}

_GM_RECORD = re.compile(r"(?m)^\s*[GM]\d")
_GATE_CALL = re.compile(r'_readiness_gate\(\s*"([^"]+)"\s*\)')


def _router_module():
    import app.routers.neck.gcode_router as module

    return module


def gate_violations(router: APIRouter, declared: set, key: str) -> list[str]:
    """Every way ``router`` falls short of full containment under ``key``.

    Kept as a function of an arbitrary router, not of the real one, so the
    negative controls below can prove it reports what it claims to.
    """
    problems: list[str] = []
    posts = {
        route.path: route.endpoint
        for route in router.routes
        if "POST" in (getattr(route, "methods", None) or set())
    }
    for path in sorted(set(posts) - declared):
        problems.append(f"undeclared POST route {path}")
    for path in sorted(declared - set(posts)):
        problems.append(f"declared route missing: {path}")
    for path in sorted(set(posts) & declared):
        gates = _GATE_CALL.findall(inspect.getsource(posts[path]))
        if gates != [key]:
            problems.append(f"{path} gates {gates or 'nothing'}, expected [{key!r}]")
    return problems


def _walk(routes, prefix=""):
    """Live routing graph, nested routers included -- not the OpenAPI schema."""
    for route in routes:
        if type(route).__name__ == "_IncludedRouter":
            context = getattr(route, "include_context", None)
            original = getattr(route, "original_router", None)
            if original is not None:
                yield from _walk(original.routes, prefix + (getattr(context, "prefix", "") or ""))
            continue
        if getattr(route, "path", None) is not None:
            yield prefix + route.path, getattr(route, "methods", None) or set()


# -----------------------------------------------------------------------------
# Containment
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("route", BOTH)
def test_both_routes_refuse_under_the_same_identity(client, route):
    response = client.post(route, json={})
    detail = response.json()["detail"]

    assert response.status_code == 422
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["route"] == ROUTE_KEY
    assert detail["generator_readiness"] == GeneratorReadiness.BLOCKED.value
    assert detail["reason"].strip() and detail["exit_condition"].strip()
    assert detail["evidence"]


def test_generate_and_download_refuse_identically(client):
    """Delegation must not produce a different refusal on either route."""
    assert (
        client.post(GENERATE, json={}).json()
        == client.post(DOWNLOAD, json={}).json()
    )


@pytest.mark.parametrize("route", BOTH)
def test_no_program_reaches_either_response(client, route):
    response = client.post(route, json={})

    assert _GM_RECORD.search(response.text) is None
    assert "attachment" not in (response.headers.get("content-disposition") or "")
    assert response.headers["content-type"].startswith("application/json")


@pytest.mark.parametrize("route", BOTH)
def test_the_generator_is_never_constructed_after_a_refusal(monkeypatch, client, route):
    module = _router_module()
    constructed: list[str] = []

    def _exploding(*args, **kwargs):
        constructed.append("NeckGCodeGenerator")
        raise AssertionError("generator constructed after readiness refused")

    monkeypatch.setattr(module, "NeckGCodeGenerator", _exploding)

    assert client.post(route, json={}).status_code == 422
    assert constructed == []


def test_download_cannot_bypass_the_containment(monkeypatch, client):
    """Download must refuse on its own, not only because it delegates.

    The delegated function is replaced by one that would happily return a
    program. If ``/download`` relied on ``generate_neck_gcode`` to refuse, it
    would now serve that program; it must refuse first instead.
    """
    module = _router_module()
    called: list[str] = []

    def _emitting(req):
        called.append("generate_neck_gcode")
        raise AssertionError("download delegated before its own gate refused")

    monkeypatch.setattr(module, "generate_neck_gcode", _emitting)

    response = client.post(DOWNLOAD, json={})

    assert response.status_code == 422
    assert response.json()["detail"]["route"] == ROUTE_KEY
    assert called == []


def test_the_gate_precedes_input_parsing(client):
    """An unparseable style or profile must not be reached, let alone defaulted."""
    body = {"headstock_style": "not-a-style", "profile": "not-a-profile", "preset": "nope"}
    for route in BOTH:
        response = client.post(route, json=body)
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "GENERATOR_READINESS_BLOCKED"


def test_no_artifact_is_written_after_a_refusal(tmp_path, monkeypatch, client):
    monkeypatch.chdir(tmp_path)

    for route in BOTH:
        assert client.post(route, json={}).status_code == 422

    written = [
        path for path in tmp_path.rglob("*")
        if path.is_file() and path.suffix.lower() in {".nc", ".tap", ".gcode", ".ngc"}
    ]
    assert written == []


# -----------------------------------------------------------------------------
# Identity
# -----------------------------------------------------------------------------

def test_the_generator_has_its_own_identity():
    record = GENERATOR_READINESS[ROUTE_KEY]

    assert record.readiness is GeneratorReadiness.BLOCKED
    assert record.permits_emission is False
    assert "NeckGCodeGenerator" in record.reason


def test_the_generator_is_not_attached_to_the_old_neck_record():
    """The ``neck`` record describes inline router code, and must stay so.

    Its gate appears exactly once in this module -- in the project-driven
    guitar route -- and neither NeckGCodeGenerator route uses it.
    """
    source = inspect.getsource(_router_module())
    keys = _GATE_CALL.findall(source)

    assert keys.count("neck") == 1
    assert keys.count(ROUTE_KEY) == 2
    for handler in ("generate_neck_gcode", "download_neck_gcode"):
        handler_source = inspect.getsource(getattr(_router_module(), handler))
        assert _GATE_CALL.findall(handler_source) == [ROUTE_KEY], handler


def test_the_three_neck_identities_are_distinct(client):
    """Each implementation refuses under its own key, never another's."""
    assert client.post(GENERATE, json={}).json()["detail"]["route"] == ROUTE_KEY
    assert (
        client.post("/api/cam-workspace/neck/generate-full", json={}).json()["detail"]["route"]
        == "neck_pipeline_full"
    )
    assert GENERATOR_READINESS["neck"].readiness is GeneratorReadiness.REVIEW_REQUIRED
    assert len({ROUTE_KEY, "neck_pipeline_full", "neck"}) == 3


def test_a_missing_record_fails_closed_as_unknown():
    without = {k: v for k, v in GENERATOR_READINESS.items() if k != ROUTE_KEY}
    resolved = resolve_generator_readiness(ROUTE_KEY, registry=without)

    assert resolved.readiness is GeneratorReadiness.UNKNOWN
    assert resolved.permits_emission is False


# -----------------------------------------------------------------------------
# Inventory -- and proof that the inventory can fail
# -----------------------------------------------------------------------------

def test_the_neck_gcode_router_is_fully_contained():
    assert gate_violations(_router_module().router, DECLARED_EMITTING, ROUTE_KEY) == []


def test_the_live_app_serves_exactly_the_declared_routes():
    """Discovered from the live routing graph, nested routers included.

    Not from OpenAPI: a route excluded from the schema still answers requests.
    """
    from app.main import app

    served = {
        path for path, methods in _walk(app.routes)
        if path.startswith("/api/neck/gcode/") and "POST" in methods
    }
    assert served == {"/api/neck" + path for path in DECLARED_EMITTING}


def _synthetic_router(extra_handler=None, drop=None):
    """A copy of the real router's POST routes, optionally altered."""
    real = _router_module().router
    router = APIRouter()
    for route in real.routes:
        if "POST" not in (getattr(route, "methods", None) or set()) or route.path == drop:
            continue
        router.add_api_route(route.path, route.endpoint, methods=["POST"])
    if extra_handler is not None:
        router.add_api_route("/gcode/extra", extra_handler, methods=["POST"])
    return router


def test_the_guard_fails_on_an_added_ungated_route():
    """Negative control. A guard never shown to fail certifies nothing."""
    def ungated_neck_program():
        return {"gcode": "G0 Z1\nG1 Z-1 F10"}

    problems = gate_violations(
        _synthetic_router(extra_handler=ungated_neck_program), DECLARED_EMITTING, ROUTE_KEY
    )
    assert problems == ["undeclared POST route /gcode/extra"]


def test_the_guard_fails_when_a_route_is_removed_or_renamed():
    problems = gate_violations(
        _synthetic_router(drop="/gcode/download"), DECLARED_EMITTING, ROUTE_KEY
    )
    assert problems == ["declared route missing: /gcode/download"]


def test_the_guard_fails_when_a_route_is_gated_under_the_wrong_key():
    problems = gate_violations(_router_module().router, DECLARED_EMITTING, "neck")
    assert len(problems) == 2
    assert all("expected ['neck']" in problem for problem in problems)
