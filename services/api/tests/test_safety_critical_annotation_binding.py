"""PROFILING-ROUTE-ANNOTATION-001 — @safety_critical FastAPI body binding.

``from __future__ import annotations`` stores parameter annotations as strings.
``@safety_critical`` wraps with ``functools.wraps``, so FastAPI used to resolve
those strings against ``app.core.safety`` globals, fail, and treat a Pydantic
model as a required query parameter (``422 loc=['query', 'req']``).

This module is itself compiled with postponed annotations so the reproduction
matches production routers. The decorator must leave FastAPI a *class*, not a
string, so JSON bodies bind.

RMOS note: restoring FastAPI binding is the decorator's documented contract
(preserve signature for DI). It does not add a feasibility evaluator. Sibling
G-code routes that were accidentally 422-unreachable become reachable again
as they were written; RMOS convergence of those lanes remains a separate HOLD.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.safety import is_safety_critical, safety_critical

# Mini-app TestClients have no RequestIdMiddleware. Signature-only tests
# do not use TestClient; the marker is harmless for them.
pytestmark = pytest.mark.allow_missing_request_id


class EchoRequest(BaseModel):
    """Minimal body model — same shape as ProfileRequest / BindingChannelRequest."""

    value: int


@safety_critical
def echo_endpoint(req: EchoRequest) -> dict:
    return {"value": req.value}


@safety_critical
def scalar_endpoint(strategy: str, current_z: float) -> dict:
    """Retract-shaped survivor: builtin scalars resolve in any module."""
    return {"strategy": strategy, "current_z": current_z}


def test_decorator_marks_wrapper() -> None:
    assert is_safety_critical(echo_endpoint)
    assert echo_endpoint._original_func is not echo_endpoint  # type: ignore[attr-defined]


def test_signature_annotations_are_evaluated_types_not_strings() -> None:
    """The defect: copied signature kept the string 'EchoRequest'."""
    raw = echo_endpoint._original_func.__annotations__["req"]  # type: ignore[attr-defined]
    assert raw == "EchoRequest" or raw is EchoRequest

    annotation = inspect.signature(echo_endpoint).parameters["req"].annotation
    assert annotation is EchoRequest
    assert not isinstance(annotation, str)


def test_wrapper_annotations_dict_is_evaluated() -> None:
    """FastAPI also consults __annotations__; strings there would re-break binding."""
    assert echo_endpoint.__annotations__["req"] is EchoRequest


def test_fastapi_binds_pydantic_body_not_query() -> None:
    app = FastAPI()
    app.post("/echo")(echo_endpoint)
    client = TestClient(app)

    missing = client.post("/echo")
    assert missing.status_code == 422
    locs = [tuple(err.get("loc", ())) for err in missing.json()["detail"]]
    assert all(loc[:1] != ("query",) for loc in locs), locs
    assert any(loc[:1] == ("body",) for loc in locs), locs

    ok = client.post("/echo", json={"value": 7})
    assert ok.status_code == 200, ok.text
    assert ok.json() == {"value": 7}


def test_openapi_declares_request_body_not_query_param() -> None:
    app = FastAPI()
    app.post("/echo")(echo_endpoint)
    spec = app.openapi()["paths"]["/echo"]["post"]
    assert "requestBody" in spec
    query_names = {
        param["name"] for param in spec.get("parameters", []) if param.get("in") == "query"
    }
    assert "req" not in query_names


def test_builtin_scalar_parameters_still_bind_as_query() -> None:
    """Retract /gcode survives because str/float are builtins — must stay query-bound."""
    app = FastAPI()
    app.post("/scalar")(scalar_endpoint)
    client = TestClient(app)

    r = client.post("/scalar", params={"strategy": "helical", "current_z": -2.5})
    assert r.status_code == 200, r.text
    assert r.json() == {"strategy": "helical", "current_z": -2.5}


def test_decorator_still_rethrows() -> None:
    @safety_critical
    def boom() -> None:
        raise RuntimeError("machine fault")

    try:
        boom()
    except RuntimeError as exc:
        assert str(exc) == "machine fault"
    else:
        raise AssertionError("safety_critical swallowed the exception")


def _assert_body_param_is_model(endpoint: object, param_name: str, model: type) -> None:
    annotation = inspect.signature(endpoint).parameters[param_name].annotation  # type: ignore[arg-type]
    assert annotation is model, (
        f"{getattr(endpoint, '__qualname__', endpoint)}.{param_name} "
        f"annotated as {annotation!r}, expected {model}"
    )


def test_profiling_gcode_signature_binds_profile_request() -> None:
    from app.cam.routers.profiling.profile_router import (
        ProfileRequest,
        generate_profile_gcode,
    )

    _assert_body_param_is_model(generate_profile_gcode, "req", ProfileRequest)


def test_binding_gcode_signatures_bind_request_models() -> None:
    from app.cam.routers.binding.binding_router import (
        BindingChannelRequest,
        PurflingLedgeRequest,
        generate_binding_channel_gcode,
        generate_purfling_ledge_gcode,
    )

    _assert_body_param_is_model(generate_binding_channel_gcode, "req", BindingChannelRequest)
    _assert_body_param_is_model(generate_purfling_ledge_gcode, "req", PurflingLedgeRequest)


def test_vcarve_production_signature_binds_request_model() -> None:
    from app.cam.routers.vcarve.production_router import (
        VCarveProductionRequest,
        generate_production_vcarve_gcode,
    )

    _assert_body_param_is_model(
        generate_production_vcarve_gcode, "req", VCarveProductionRequest
    )


def test_radius_dish_generate_gcode_signature_binds_request_model() -> None:
    from app.routers.radius_dish_router import RadiusDishRequest, generate_gcode

    _assert_body_param_is_model(generate_gcode, "req", RadiusDishRequest)


def test_feeds_speeds_signature_binds_request_model() -> None:
    from app.cam.routers.utility.optimization_router import (
        FeedsSpeedsRequest,
        calculate_feeds_speeds,
    )

    _assert_body_param_is_model(calculate_feeds_speeds, "body", FeedsSpeedsRequest)


_RECT = [
    {"x": 0.0, "y": 0.0},
    {"x": 80.0, "y": 0.0},
    {"x": 80.0, "y": 50.0},
    {"x": 0.0, "y": 50.0},
]


def test_profiling_gcode_accepts_json_body_and_emits_gcode() -> None:
    """End-to-end: the production route is no longer 422 loc=['query','req']."""
    from app.cam.routers.profiling.profile_router import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    missing = client.post("/gcode")
    assert missing.status_code == 422
    locs = [tuple(err.get("loc", ())) for err in missing.json()["detail"]]
    assert all(loc[:1] != ("query",) for loc in locs), locs

    ok = client.post("/gcode", json={"contour": _RECT})
    assert ok.status_code == 200, ok.text
    assert "G21" in ok.text
    assert ok.headers.get("x-pass-count")


def test_binding_channel_gcode_accepts_json_body_and_emits_gcode() -> None:
    from app.cam.routers.binding.binding_router import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    missing = client.post("/channel/gcode")
    assert missing.status_code == 422
    locs = [tuple(err.get("loc", ())) for err in missing.json()["detail"]]
    assert all(loc[:1] != ("query",) for loc in locs), locs

    ok = client.post("/channel/gcode", json={"body_outline": _RECT})
    assert ok.status_code == 200, ok.text
    assert "G21" in ok.text
