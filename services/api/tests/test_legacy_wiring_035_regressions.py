"""Regression guards for the three production defects found by Investigation 035.

Investigation 035 (LEGACY-WIRING-001B) is evidence, and it lives in the
Consolidation Lab. These are the production guards for what it found. Each test
pins the specific property that was wrong, not merely that a route answers.

That distinction is the point. ``test_polygon_offset_endpoint_smoke.py`` already
asserted 200 and "G" in the body for /api/cam/polygon_offset.nc, and it passed
throughout the period the wrong engine served that URL -- its assertions could
not tell two G-code generators apart. A guard that cannot fail on the defect it
is meant to catch is not a guard.
"""
import io
import re

import ezdxf
import pytest
from fastapi.testclient import TestClient

from app.main import app

SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0], [0.0, 0.0]]
TINY_GCODE = "G21\nG90\nG0 X0 Y0 Z5\nG1 X10 Y0 F300\nG1 X10 Y10\nM30\n"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _first_pass_step(gcode):
    """Distance between the first two rapid positioning X moves = pass inset."""
    xs = [float(m) for m in re.findall(r"G0 X([\d.]+)", gcode)[:2]]
    return round(xs[0] - xs[1], 3) if len(xs) == 2 else None


# ---------------------------------------------------------------------------
# S3 -- POST /api/cam/polygon_offset.nc was served by the N17 utility handler,
# which reads stepover as absolute millimetres. Both live consumers send the
# governed fraction convention, so a 0.4 stepover produced 0.4 mm passes where
# 0.4 x 6.0 = 2.4 mm was intended: a 6x denser toolpath, at HTTP 200, with
# plausible-looking G-code. Machining path.
# ---------------------------------------------------------------------------

def test_s3_polygon_offset_nc_applies_stepover_as_fraction_of_tool_dia(client):
    """The headline guard: stepover 0.4 with a 6 mm tool must step 2.4 mm."""
    response = client.post(
        "/api/cam/polygon_offset.nc",
        json={"polygon": SQUARE, "tool_dia": 6.0, "stepover": 0.4,
              "link_mode": "arc", "units": "mm"},
    )
    assert response.status_code == 200

    step = _first_pass_step(response.text)
    assert step == pytest.approx(2.4, abs=0.01), (
        "pass inset {} mm; expected tool_dia * stepover = 2.4 mm. "
        "A step of 0.4 means stepover was read as millimetres -- the N17 "
        "utility handler is shadowing the governed engine again.".format(step)
    )


def test_s3_polygon_offset_nc_is_served_by_the_governed_draft_lane(client):
    """Ownership, stated directly. Only the governed router sets this header."""
    response = client.post(
        "/api/cam/polygon_offset.nc",
        json={"polygon": SQUARE, "tool_dia": 6.0, "stepover": 0.4},
    )
    assert response.status_code == 200
    assert response.headers.get("X-ToolBox-Lane") == "draft"
    assert "N17 Polygon Offset" not in response.text


def test_s3_preview_and_nc_agree_on_the_step(client):
    """The user-visible defect: OffsetLab previewed one path, downloaded another.

    Both consumers preview against /polygon_offset.preview, which was always
    governed-only. If the two endpoints disagree on ``step``, the UI lies.
    """
    body = {"polygon": SQUARE, "tool_dia": 6.0, "stepover": 0.4, "units": "mm"}
    preview = client.post("/api/cam/polygon_offset.preview", json=body)
    nc = client.post("/api/cam/polygon_offset.nc", json=body)
    assert preview.status_code == 200 and nc.status_code == 200
    assert preview.json()["step"] == pytest.approx(_first_pass_step(nc.text), abs=0.01)


def test_s3_n17_utility_engine_is_still_reachable(client):
    """The N17 implementation was renamed, not deleted."""
    response = client.post(
        "/api/cam/polygon_offset_n17.nc",
        json={"polygon": SQUARE, "tool_dia": 6.0, "stepover": 0.4},
    )
    assert response.status_code == 200
    assert "N17 Polygon Offset" in response.text
    # Its own convention is preserved: stepover really is millimetres here.
    assert _first_pass_step(response.text) == pytest.approx(0.4, abs=0.01)


# ---------------------------------------------------------------------------
# S1 -- five frontend call sites posted to /api/cam/simulate_gcode, which is not
# mounted. The simulator lives under the /api/cam/sim prefix, and the callers
# split across TWO contracts: four send JSON, one sends multipart.
# ---------------------------------------------------------------------------

def test_s1_json_simulation_entrypoint_is_mounted(client):
    """The URL the four JSON call sites now use."""
    response = client.post("/api/cam/sim/gcode", json={"gcode": TINY_GCODE})
    assert response.status_code == 200
    assert "moves" in response.json()


def test_s1_upload_simulation_entrypoint_is_mounted(client):
    """The URL the one multipart call site now uses.

    Repointing every caller at /api/cam/sim/gcode would have 422'd this one:
    it sends a file, not a JSON body.
    """
    response = client.post(
        "/api/cam/sim/upload",
        files={"file": ("part.nc", io.BytesIO(TINY_GCODE.encode()), "text/plain")},
        data={"units": "mm"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_s1_dead_frontend_url_is_still_absent(client):
    """Documents the 404 rather than papering over it with an alias.

    If a future change mounts this path, the two contracts above are the reason
    a single alias would be the wrong fix.
    """
    dead = client.post("/api/cam/simulate_gcode", json={"gcode": TINY_GCODE})
    assert dead.status_code == 404


# ---------------------------------------------------------------------------
# S4 -- both legacy DXF export endpoints returned 500. try_build_with_ezdxf
# raised instead of returning None, which severed the ASCII R12 fallback its
# callers depend on.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path,payload",
    [
        ("/exports/polyline_dxf",
         {"polyline": {"points": [[0, 0], [100, 0], [100, 50], [0, 50]]}}),
        ("/exports/biarc_dxf",
         {"p0": [0, 0], "t0": [1, 0], "p1": [50, 30], "t1": [0, 1]}),
    ],
)
def test_s4_legacy_dxf_exports_return_readable_r12(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 200, "{} -> {}".format(path, response.status_code)

    doc = ezdxf.read(io.StringIO(response.content.decode("utf-8", errors="ignore")))
    assert doc.dxfversion == "AC1009", "free-tier exports must stay R12"
    assert list(doc.modelspace()), "DXF parsed but contains no entities"
    # LWPOLYLINE is invalid in R12 and was the second of the two faults here.
    assert not any(e.dxftype() == "LWPOLYLINE" for e in doc.modelspace())


def test_s4_ezdxf_helper_returns_none_instead_of_raising():
    """The fallback contract itself, tested directly.

    Callers do ``ez = try_build_with_ezdxf(...)`` then fall back when it is
    None. They cannot fall back from an exception. This is the property WP-1's
    narrowing broke, and it is the one worth pinning.
    """
    from app.exports.dxf_helpers import try_build_with_ezdxf

    result = try_build_with_ezdxf(
        [("polyline", {"points": [(0, 0), (1, 1)], "comment": "x"})]
    )
    assert result is None or isinstance(result, bytes)


def test_s4_comment_header_call_is_well_formed():
    """ezdxf CustomVars.append(tag, value) takes two args; a tuple raises."""
    from app.util.dxf_compat import create_document

    doc = create_document(version="R12")
    doc.header.custom_vars.append("COMMENT", "investigation-035")
    assert doc.header.custom_vars.get("COMMENT") == "investigation-035"
