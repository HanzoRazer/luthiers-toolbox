"""HEADSTOCK-TRANSITION-GCODE-SAFETY-001: contain POST /api/headstock/transition/gcode.

Containment, not qualification. The route must refuse before the generator runs,
return no program, and leave the generator, /dxf and /analysis unchanged.
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import re
from pathlib import Path

import pytest

from app.cam.generator_readiness import GeneratorReadiness, resolve_generator_readiness
from app.routers.neck import headstock_transition_export as hst

pytestmark = pytest.mark.allow_missing_request_id

API_ROOT = Path(__file__).resolve().parents[1]
SOURCE = API_ROOT / "app" / "routers" / "neck" / "headstock_transition_export.py"
INVENTORY = API_ROOT / "governance" / "manufacturing_output_inventory.json"
GCODE = "/api/headstock/transition/gcode"

# Default, flat, volute and scallop requests. The refusal must not depend on input.
REQUESTS = (
    {},
    {"headstock_type": "flat", "pitch_angle_deg": 0.0},
    {"volute_type": "gibson", "volute_height_mm": 4.0},
    {"volute_type": "scallop", "neck_depth_mm": 24.0, "ball_nose_mm": 6.35},
)

# SHA-256 of each function's source span (ast.get_source_segment, LF), taken on
# origin/main b5e61805 before containment (file blob 63a16e79). Only the
# /gcode handler may change.
UNCHANGED_SPANS = {
    "TransitionRequest": "1298a5621a55dcc293d2ae87f9495ddd8e015a791d726900a6f35fe57ebef096",
    "_hs_plane_z": "a80ef62759fd9f131d68b3c0ec5b0ffd0adc91098764b4dc08aee65892cff292",
    "_neck_z": "9d60235eac3fd2d88823566f7a4b768190f1d3d872a7e1f8b0744607b5f66198",
    "_blend_z": "f63b5431d31a9dc0ee29767912a287eafdd7e41d9e0e4b23459e584c7d7bce75",
    "_volute_z": "fb74856ba47df06145e0249fb124bd9606d26f89595ef368100ada7ddd9f3fd1",
    "_surface_z": "bfc311adb4fc7400aa4e38de524a32a0ca4aa2a7ca50cae124058747dde62ddb",
    "_region": "1f5b7d33c6a2a6a6b15cc18cf9dc6e086abe15d9e739df9488f87908c82cd0c5",
    "_thin_point_mm": "c247657fad82ae29e02c9529cfae41960ce49f381207e6f7723160479582b57b",
    "_shape_z": "821724f8ac1f184a62526cbc1cfec9f6c18cd12056d1fbd8c5a207b2b37ccb0d",
    "build_transition_dxf": "2d2a4a302890cc4f08325c43ae37ab5199fce32cf5ff004f3e578952c34c3193",
    "build_transition_gcode": "e96bc8928b966339567271b4006cf5694573c569429a59597891feb8b4ba4a0a",
    "transition_dxf": "3e8bcd6d558e00aac98ebebf6779827c3b2341e92451c6fae8d4d78656eaf1f3",
    "transition_analysis": "4be3be05c8261497521d1dbe7e9bba45fc14039d9c8963aca651e237bf532beb",
}

# /analysis response bodies recorded before containment.
ANALYSIS_BODIES = (
    ({}, "9a559abbb30f7c99b8646127eb61feffeb0db879af0a02a90bdf214360ffb7c5"),
    ({"volute_type": "gibson", "volute_height_mm": 4.0},
     "9ca73c8d39792670b1dc7877c1b04202e52ff5de77322f791265a4f8f31a60d7"),
)


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8").replace("\r\n", "\n")


def _function(name: str) -> ast.AST:
    for node in ast.parse(_source()).body:
        if getattr(node, "name", None) == name:
            return node
    raise AssertionError(f"{name} not found")


def _call_lines(fn: ast.AST, callee: str) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(fn)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == callee
    ]


@pytest.mark.parametrize("body", REQUESTS)
def test_gcode_refuses_with_stable_contract_and_no_program(client, body):
    response = client.post(GCODE, json=body)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["ok"] is False
    assert detail["error"] == "SAFETY_BLOCKED"
    assert detail["reason"] == "HEADSTOCK_TRANSITION_NOT_MANUFACTURING_QUALIFIED"
    assert detail["order_id"] == "HEADSTOCK-TRANSITION-GCODE-SAFETY-001"
    assert "content-disposition" not in response.headers
    assert "x-gcode-sha256" not in response.headers
    assert response.headers["content-type"].startswith("application/json")
    # No program body: the refusal may *describe* moves (readiness evidence), but
    # no line of the response is a G/M block, and no program terminator is sent.
    assert not re.search(r"(?m)^\s*[GM]\d", response.text)
    assert "M30" not in response.text


def test_generator_is_never_reached(client, monkeypatch):
    calls: list = []
    monkeypatch.setattr(hst, "build_transition_gcode", lambda r: calls.append(r) or "G21\nM30")

    statuses = [client.post(GCODE, json=body).status_code for body in REQUESTS]

    assert statuses == [409] * len(REQUESTS)
    assert calls == []


def test_refusal_precedes_generation_in_the_handler():
    handler = _function("transition_gcode")
    gate = _call_lines(handler, "require_generator_readiness")
    generate = _call_lines(handler, "build_transition_gcode")

    assert len(gate) == 1 and len(generate) == 1
    assert gate[0] < generate[0]


def test_readiness_key_does_not_permit_emission():
    call = next(
        node for node in ast.walk(_function("transition_gcode"))
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "require_generator_readiness"
    )

    assert ast.literal_eval(call.args[0]) == hst.READINESS_KEY == "headstock_transition_gcode"
    record = resolve_generator_readiness(hst.READINESS_KEY)
    assert record.readiness is GeneratorReadiness.BLOCKED
    assert record.permits_emission is False
    for finding in ("HST-01", "HST-02", "HST-03"):
        assert finding in " ".join(record.evidence)


def test_generator_and_sibling_routes_are_byte_identical():
    source = _source()
    spans = {}
    for node in ast.parse(source).body:
        if getattr(node, "name", None) in UNCHANGED_SPANS:
            segment = ast.get_source_segment(source, node)
            spans[node.name] = hashlib.sha256(segment.encode("utf-8")).hexdigest()

    assert spans == UNCHANGED_SPANS


@pytest.mark.parametrize(("body", "digest"), ANALYSIS_BODIES)
def test_analysis_is_unchanged(client, body, digest):
    response = client.post("/api/headstock/transition/analysis", json=body)

    assert response.status_code == 200
    assert hashlib.sha256(response.content).hexdigest() == digest


def test_dxf_behaviour_is_unchanged_including_its_existing_defect():
    """HST-06, pre-existing and out of scope: /dxf fails on origin/main.

    ``transition_dxf`` passes a BytesIO to ``doc.write``, which writes text, so
    every request raises before a response is built. Containment does not touch
    this handler (span pinned above). Update this test when HST-06 is repaired.
    """
    with pytest.raises(TypeError, match="bytes-like object is required"):
        asyncio.run(hst.transition_dxf(hst.TransitionRequest()))


def test_inventory_records_fail_closed_containment():
    rows = json.loads(INVENTORY.read_text(encoding="utf-8"))["rows"]
    row = next(item for item in rows if item["path"] == GCODE)

    assert row["containment"] == "FAIL_CLOSED"
    assert row["authority_layer"] == "readiness"
    assert row["authority_key"] == "headstock_transition_gcode"
    assert row["authority_order"] == "before_generation"
    assert row["classification"] == "CONFIRMED_EMITTER"
