"""
LTB-R12-002 — reproductions of the four gaps in the landed R12 converter.

**These land RED.** Every test here fails against the base this order declares,
`main` @ `22e6768` (PR #381), and each is committed before its fix. A regression test
written after its fix proves only that the code matches itself.

D2: a defect asserted from reading is PROPOSED; one reproduced against the declared
base is CONFIRMED. All four are CONFIRMED.

  G1  elevated LWPOLYLINE -> TypeError inside add_polyline2d -> HTTP 500, unhandled
  G2  reserved layer `0` / style `Standard` skipped, so layer 0's colour is dropped
  G3  convert_file writes the destination before verifying it
  G4  TEXT's default style is missed after a round trip, so `Standard` never syncs

G1 is exercised **through the endpoint**, not the module: the 500 is the defect. A
module-level TypeError test would pass once the module raised something tidier while
callers still got a stack trace.
"""
from __future__ import annotations

import base64
import io
import tempfile
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from app.cam import r12_convert  # noqa: E402
from app.cam.r12_convert import FidelityError, convert_document, convert_file  # noqa: E402

ENDPOINT = "/api/dxf/preflight/auto_fix"


@pytest.fixture
def client():
    """Local to this module, matching test_dxf_preflight_endpoint_smoke.py."""
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


def _post(client, doc, filename="gap.dxf"):
    """Serialise a document the way a caller would and post it for R12 conversion."""
    buffer = io.StringIO()
    doc.write(buffer)
    payload = base64.b64encode(buffer.getvalue().encode("cp1252")).decode("utf-8")
    return client.post(ENDPOINT, json={
        "dxf_base64": payload, "filename": filename, "fixes": ["convert_to_r12"],
    })


def _reopen(data):
    raw = base64.b64decode(data["fixed_dxf_base64"])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf", mode="wb") as handle:
        handle.write(raw)
        path = handle.name
    return ezdxf.readfile(path)


# --------------------------------------------------------------------------- G1


def _elevated_contour():
    doc = ezdxf.new("R2000")
    doc.layers.add("BODY_OUTLINE")
    doc.modelspace().add_lwpolyline(
        [(0.0, 0.0), (100.0, 0.0), (100.0, 60.0), (0.0, 60.0)],
        close=True,
        dxfattribs={"layer": "BODY_OUTLINE", "elevation": 5.0},
    )
    return doc


def test_g1_elevated_contour_converts_through_the_endpoint(client):
    """CONFIRMED against 22e6768: HTTP 500, unhandled TypeError.

    `add_polyline2d` is handed the LWPOLYLINE's float elevation where it expects a
    point, so it raises `object of type 'float' has no len()`. Nothing catches it, so
    the caller receives a stack trace rather than a named refusal.
    """
    response = _post(client, _elevated_contour(), "elevated.dxf")
    assert response.status_code == 200, (
        f"elevated contour must convert, not 500: {response.text[:300]}"
    )

    saved = _reopen(response.json())
    polylines = [e for e in saved.modelspace() if e.dxftype() == "POLYLINE"]
    assert len(polylines) == 1, [e.dxftype() for e in saved.modelspace()]
    assert polylines[0].dxf.layer == "BODY_OUTLINE"


def test_g1_elevation_survives_as_a_point_not_a_float():
    """The elevation itself must arrive, not merely stop crashing."""
    target, _ = convert_document(_elevated_contour(), "R12")
    polyline = [e for e in target.modelspace() if e.dxftype() == "POLYLINE"][0]
    elevation = polyline.dxf.elevation
    assert not isinstance(elevation, float), (
        "R12 POLYLINE.elevation is a point; a bare float is what crashes the writer"
    )
    assert round(elevation.z, 6) == 5.0, elevation


# --------------------------------------------------------------------------- G2


def test_g2_reserved_layer_zero_carries_its_colour():
    """CONFIRMED against 22e6768: layer 0's colour 5 arrives as 7.

    `_carry` treats a name already in the target as `already_present` and skips it.
    Every document defines layer `0`, so a source that sets its colour loses it.
    """
    doc = ezdxf.new("R2000")
    doc.layers.get("0").dxf.color = 5
    doc.modelspace().add_line((0, 0), (10, 10), dxfattribs={"layer": "0"})

    target, report = convert_document(doc, "R12")
    assert target.layers.get("0").dxf.color == 5, (
        f"layer 0 colour dropped; report says {report['layers'].get('0')}"
    )


def test_g2_non_reserved_layer_colour_still_survives():
    """Regression guard, not an investigation.

    The loss is reserved-specific: measured against 22e6768, `CUSTOM` colour 3
    survives while `0` colour 5 does not. This keeps the working half working.
    """
    doc = ezdxf.new("R2000")
    doc.layers.add("CUSTOM").dxf.color = 3
    doc.modelspace().add_line((0, 0), (10, 10), dxfattribs={"layer": "CUSTOM"})

    target, _ = convert_document(doc, "R12")
    assert target.layers.get("CUSTOM").dxf.color == 3


# --------------------------------------------------------------------------- G3


def test_g3_failed_verification_leaves_the_destination_untouched(tmp_path, monkeypatch):
    """CONFIRMED against 22e6768: the destination is written before it is verified.

    `convert_file` calls `saveas(out_path)` and only then `verify_saved_file`. A
    verification failure therefore leaves the caller's existing file already
    overwritten by output that was just judged unfit.
    """
    source = tmp_path / "source.dxf"
    doc = ezdxf.new("R2000")
    doc.layers.add("BODY_OUTLINE")
    doc.modelspace().add_lwpolyline(
        [(0, 0), (10, 0), (10, 10)], close=True, dxfattribs={"layer": "BODY_OUTLINE"})
    doc.saveas(str(source))

    destination = tmp_path / "existing.dxf"
    destination.write_bytes(b"PRE-EXISTING CONTENT THAT MUST SURVIVE A FAILED CONVERSION\n")
    before = destination.read_bytes()

    def _always_fails(*args, **kwargs):
        raise FidelityError("forced failure: the publish order is what is under test")

    monkeypatch.setattr(r12_convert, "verify_saved_file", _always_fails)

    with pytest.raises(FidelityError):
        convert_file(source, destination)

    assert destination.read_bytes() == before, (
        "a failed verification destroyed the destination; publication must follow "
        "verification, not precede it"
    )
    assert not list(tmp_path.glob("*.tmp")), "no temporary file may be left behind"


# --------------------------------------------------------------------------- G4


def test_g4_default_text_style_is_synchronised():
    """CONFIRMED against 22e6768: `Standard` is never synchronised.

    Two causes compound. The style name is collected with `hasattr("style")`, which a
    TEXT using the default does not report; and `Standard` exists in the target, so
    `_carry` would skip it as `already_present` anyway. A document that customises its
    default style silently converts with the target's font.
    """
    doc = ezdxf.new("R2000")
    doc.styles.get("Standard").dxf.font = "arial.ttf"
    doc.layers.add("ANNOTATION")
    doc.modelspace().add_text(
        "cut depth 6mm",
        dxfattribs={"layer": "ANNOTATION", "insert": (1, 1), "height": 2.5},
    )

    target, _ = convert_document(doc, "R12")
    assert target.styles.get("Standard").dxf.font == "arial.ttf", (
        "the source's default style font was not carried"
    )
