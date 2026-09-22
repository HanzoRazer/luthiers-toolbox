"""LTB-REMEDIATE-P1: the cam-workspace neck routes, contained.

``POST /api/cam-workspace/neck/generate-full`` answered an uncredentialed default
request with a 28,260-byte ``.nc`` attachment carrying 702 G0 rapids below the
workpiece top. This module proves the containment: both routes that reach
``NeckPipeline`` refuse before a generator is constructed, and the refusal names
the identity, state, reason and exit condition.

**Scope.** This is a fail-closed and rapid-removal patch. It is NOT a
qualification of the generator for cutting: ``neck_pipeline_full`` stays
non-emitting until a readiness decision is recorded on evidence.

The motion correction is proved separately, in
``test_p1_neck_pipeline_motion.py``. The two were one module until it crossed
the 500-line ratchet; they answer different questions anyway -- what the route
may return, and what the emitter produces.

Read-only with respect to hardware: nothing here drives a machine.
"""
import re

import pytest

from app.cam.generator_readiness import (
    GENERATOR_READINESS,
    GeneratorReadiness,
)

pytestmark = pytest.mark.allow_missing_request_id

ROUTE_KEY = "neck_pipeline_full"
FULL_ROUTE = "/api/cam-workspace/neck/generate-full"
OP_ROUTE = "/api/cam-workspace/neck/generate/profile_rough"

_GM_RECORD = re.compile(r"(?m)^\s*[GM]\d")


# -----------------------------------------------------------------------------
# Containment
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("route", [FULL_ROUTE, OP_ROUTE])
def test_the_route_refuses_while_readiness_is_non_emitting(client, route):
    response = client.post(route, json={})

    assert response.status_code == 422
    assert GENERATOR_READINESS[ROUTE_KEY].permits_emission is False


@pytest.mark.parametrize("route", [FULL_ROUTE, OP_ROUTE])
def test_the_refusal_names_identity_state_reason_and_exit_condition(client, route):
    detail = client.post(route, json={}).json()["detail"]

    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["route"] == ROUTE_KEY
    assert detail["generator_readiness"] == GeneratorReadiness.BLOCKED.value
    assert detail["reason"].strip()
    assert detail["exit_condition"].strip()
    assert detail["evidence"], "a refusal without evidence is an assertion"


@pytest.mark.parametrize("route", [FULL_ROUTE, OP_ROUTE])
def test_no_program_records_reach_the_response(client, route):
    response = client.post(route, json={})

    assert _GM_RECORD.search(response.text) is None
    assert "attachment" not in (response.headers.get("content-disposition") or "")
    assert response.headers["content-type"].startswith("application/json")


def test_the_refusal_discloses_no_filesystem_path(client):
    detail = client.post(FULL_ROUTE, json={}).json()["detail"]
    blob = repr(detail)

    assert ":\\" not in blob
    assert "/services/api/" not in blob


def test_an_unknown_operation_is_refused_without_disclosing_valid_ops(client):
    """The gate precedes op validation, so a contained route stays opaque."""
    response = client.post("/api/cam-workspace/neck/generate/not_an_op", json={})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "GENERATOR_READINESS_BLOCKED"


# -----------------------------------------------------------------------------
# Gate ordering -- the part that is easy to get wrong and silent when wrong
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("route", [FULL_ROUTE, OP_ROUTE])
def test_the_generator_is_never_constructed_after_a_refusal(monkeypatch, client, route):
    """Authority must precede generator use, not merely discard its output."""
    import app.routers.cam.cam_workspace_router as router_module

    constructed: list[str] = []

    def _exploding_pipeline(*args, **kwargs):
        constructed.append("NeckPipeline")
        raise AssertionError("generator constructed after readiness refused")

    monkeypatch.setattr(router_module, "NeckPipeline", _exploding_pipeline)

    response = client.post(route, json={})

    assert response.status_code == 422
    assert constructed == []


def test_the_gate_precedes_the_pipeline_availability_check(monkeypatch, client):
    """An import failure must not be able to mask the refusal with a 503."""
    import app.routers.cam.cam_workspace_router as router_module

    monkeypatch.setattr(router_module, "PIPELINE_AVAILABLE", False)

    response = client.post(FULL_ROUTE, json={})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "GENERATOR_READINESS_BLOCKED"


def test_no_artifact_is_written_after_a_refusal(tmp_path, monkeypatch, client):
    """Refusal must leave no .nc/.tap behind, anywhere the handler could write."""
    monkeypatch.chdir(tmp_path)

    assert client.post(FULL_ROUTE, json={}).status_code == 422
    assert client.post(OP_ROUTE, json={}).status_code == 422

    written = [
        path for path in tmp_path.rglob("*")
        if path.is_file() and path.suffix.lower() in {".nc", ".tap", ".gcode", ".ngc"}
    ]
    assert written == []


# -----------------------------------------------------------------------------
# Identity -- omission and renaming must fail, not open the route
# -----------------------------------------------------------------------------

def test_the_pipeline_route_has_its_own_identity(client):
    """It must not be folded into the ``neck`` record, which governs other code.

    ``neck`` describes the inline handler behind
    ``/api/cam/guitar/{model_id}/neck/gcode``, which constructs no generator.
    This route reaches ``NeckPipeline``. One record cannot truthfully describe
    both, and reusing it would repeat the CF-1 identity error rather than fix it.
    """
    assert ROUTE_KEY in GENERATOR_READINESS
    assert ROUTE_KEY != "neck"
    assert GENERATOR_READINESS[ROUTE_KEY].readiness is GeneratorReadiness.BLOCKED
    assert GENERATOR_READINESS["neck"].readiness is GeneratorReadiness.REVIEW_REQUIRED


def test_renaming_or_removing_the_record_fails_closed(client):
    """Deleting the record must refuse harder, never open the route."""
    from app.cam import generator_readiness as gr

    without = {k: v for k, v in GENERATOR_READINESS.items() if k != ROUTE_KEY}
    resolved = gr.resolve_generator_readiness(ROUTE_KEY, registry=without)

    assert resolved.readiness is GeneratorReadiness.UNKNOWN
    assert resolved.permits_emission is False


def test_both_pipeline_routes_are_gated_under_the_same_identity():
    """A second door to one generator is the defect, not a second finding."""
    import inspect

    import app.routers.cam.cam_workspace_router as router_module

    source = inspect.getsource(router_module)
    gated = re.findall(r'_readiness_gate\(\s*"([^"]+)"\s*\)', source)

    assert gated == [ROUTE_KEY, ROUTE_KEY], (
        "both /neck/generate/{op} and /neck/generate-full must be gated, "
        f"under one identity; found {gated}"
    )


def test_every_gcode_route_on_this_router_is_gated():
    """Adding an ungated G-code route to this router must fail here.

    Discovery is by decorator, not by OpenAPI, so a route excluded from the
    schema is still counted.
    """
    import inspect

    import app.routers.cam.cam_workspace_router as router_module

    source = inspect.getsource(router_module)
    emitting = re.findall(r'@router\.post\(\s*"(/neck/generate[^"]*)"', source)

    assert sorted(emitting) == sorted(["/neck/generate/{op}", "/neck/generate-full"])
    assert source.count("_readiness_gate(") == len(emitting)


# -----------------------------------------------------------------------------
# Blast radius
# -----------------------------------------------------------------------------

def test_the_other_readiness_records_are_untouched():
    assert GENERATOR_READINESS["stratocaster_body"].readiness is GeneratorReadiness.BLOCKED
    assert (
        GENERATOR_READINESS["les_paul_body"].readiness
        is GeneratorReadiness.GOVERNED_BY_ASSET_AUTHORITY
    )
    assert GENERATOR_READINESS["flying_v_body"].readiness is GeneratorReadiness.REVIEW_REQUIRED


def test_containment_did_not_couple_this_router_to_the_asset_layer():
    """P-1 must not quietly widen the asset gate to reach this route.

    Tested against parsed imports, not module text -- the same discipline the
    existing ``test_readiness_module_does_not_import_dxf_authority`` uses, and
    for the same reason: prose that names the asset layer is not a coupling.
    The readiness module itself is already covered there; this covers the router
    that P-1 edited.
    """
    import ast
    import inspect

    import app.routers.cam.cam_workspace_router as router_module

    tree = ast.parse(inspect.getsource(router_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")

    offenders = {m for m in imported if "dxf_authority" in m or "instrument_geometry" in m}
    assert not offenders, f"cam_workspace_router now imports the asset layer: {offenders}"
