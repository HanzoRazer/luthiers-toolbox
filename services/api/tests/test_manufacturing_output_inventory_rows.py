"""LTB-CF2-INVENTORY-001: classification, authority, and program detection.

Reads the committed inventory. Does not call a generator.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ci.manufacturing_output_classify import classify_route
from app.ci.manufacturing_output_routes import LiveRoute
from _manufacturing_output_testkit import program_records, records_in_json, records_in_program_text

pytestmark = pytest.mark.allow_missing_request_id

INVENTORY = Path(__file__).resolve().parents[1] / "governance" / "manufacturing_output_inventory.json"
PROBE_KEYS = {
    "/api/probe/boss/gcode/download_governed": "boss_probe_gcode",
    "/api/probe/corner/gcode/download_governed": "corner_probe_gcode",
    "/api/probe/pocket/gcode/download_governed": "pocket_probe_gcode",
    "/api/probe/surface_z/gcode/download_governed": "surface_z_probe_gcode",
    "/api/probe/vise_square/gcode/download_governed": "vise_square_probe_gcode",
}


def _document():
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def _row(method: str, path: str) -> dict:
    matches = [row for row in _document()["rows"] if row["method"] == method and row["path"] == path]
    assert len(matches) == 1
    return matches[0]


def _route(fn, method: str, path: str) -> LiveRoute:
    return LiveRoute(method, path, fn.__name__, fn, None, True, "APIRoute")


def _build_simple_retract_gcode(strategy: str) -> str:
    return f"G0 Z1 ({strategy})"


def _authorize_retract(**_kwargs):
    return None


def generate_neck_gcode(req):
    _readiness_gate("neck_gcode_generator")
    return NeckGCodeGenerator(req)


def NeckGCodeGenerator(req):
    return req


def _readiness_gate(_key):
    return None


def test_path_token_alone_is_not_an_emitter_and_unexamined_is_not_safe():
    # 21, 22, 23, 25
    def profiles():
        return {"profiles": []}

    row = classify_route(_route(profiles, "GET", "/api/neck/gcode/profiles"))
    assert row["classification"] == "UNEXAMINED"
    assert row["containment"] == "UNKNOWN"
    assert "not a safety claim" in row["notes"]
    assert " is safe" not in row["notes"].lower()
    listed = _row("GET", "/api/neck/gcode/profiles")
    assert listed["classification"] == "UNEXAMINED"
    assert _document()["rows"]
    assert all(item["classification"] != "NON_EMITTING" or item["evidence"] for item in _document()["rows"])
    assert sum(item["classification"] == "NON_EMITTING" for item in _document()["rows"]) == 0


def test_generate_outline_is_not_a_confirmed_emitter():
    # 24
    def preview(generator):
        return generator.generate_outline()

    row = classify_route(_route(preview, "POST", "/api/cam/guitar/acoustic/{style}/generate"))
    assert row["classification"] == "UNEXAMINED"
    assert row["classification"] != "CONFIRMED_EMITTER"


def test_authority_after_generation_is_not_fail_closed():
    # 26, 27, 43
    def late(strategy):
        text = _build_simple_retract_gcode(strategy)
        _authorize_retract(tool_id="retract:direct")
        return text

    row = classify_route(_route(late, "POST", "/api/cam/retract/late"))
    assert row["classification"] == "CONFIRMED_EMITTER"
    assert row["authority_order"] == "after_generation"
    assert row["containment"] == "LIVE_UNGOVERNED"
    assert row["evidence"]


def test_retract_tool_id_renders_the_strategy_placeholder():
    # 35, 44
    def retract_sample(strategy):
        _authorize_retract(tool_id=f"retract:{strategy}")
        return _build_simple_retract_gcode(strategy)

    row = classify_route(_route(retract_sample, "POST", "/api/cam/retract/sample"))
    assert row["authority_key"] == "retract:{strategy}"
    assert row["authority_order"] == "before_generation"
    assert row["containment"] == "FAIL_CLOSED"
    assert row["authority_layer"] == "manufacturing_output"


def test_neck_pipeline_and_generator_stay_distinct():
    # 29, 30, 31, 33
    full = _row("POST", "/api/cam-workspace/neck/generate-full")
    op = _row("POST", "/api/cam-workspace/neck/generate/{op}")
    generate = _row("POST", "/api/neck/gcode/generate")
    download = _row("POST", "/api/neck/gcode/download")
    assert full["implementation_symbol"].endswith("NeckPipeline")
    assert full["authority_key"] == "neck_pipeline_full"
    assert full["containment"] == "FAIL_CLOSED"
    assert op["implementation_symbol"] == full["implementation_symbol"]
    assert generate["implementation_symbol"].endswith("NeckGCodeGenerator")
    assert generate["authority_key"] == "neck_gcode_generator"
    assert generate["containment"] == "FAIL_CLOSED"
    assert generate["proof_status"] == "RUNTIME_PROVED"
    assert download["classification"] == "CONFIRMED_DELEGATE"
    assert download["delegates_to"] == "generate_neck_gcode"
    assert download["implementation_symbol"] == generate["implementation_symbol"]
    assert generate["implementation_symbol"] != full["implementation_symbol"]


def test_inline_guitar_neck_is_fail_closed_on_the_neck_key():
    # 32
    inline = _row("POST", "/api/cam/guitar/{model_id}/neck/gcode")
    assert inline["implementation_kind"] == "inline"
    assert inline["authority_key"] == "neck"
    assert inline["containment"] == "FAIL_CLOSED"
    assert inline["proof_status"] == "RUNTIME_PROVED"


def test_flying_v_paths_share_pocket_generator_and_the_same_key():
    # 34, 40
    for path in (
        "/api/cam/guitar/flying_v/toolpath/control_cavity",
        "/api/cam/guitar/flying_v/toolpath/neck_pocket",
        "/api/cam/guitar/flying_v/toolpath/pickup",
        "/api/cam/guitar/flying_v/body/gcode",
    ):
        row = _row("POST", path)
        assert row["implementation_symbol"] == "app.cam.flying_v.pocket_generator"
        assert row["authority_key"] == "flying_v_body"
        assert row["containment"] == "FAIL_CLOSED"


def test_retract_aliases_share_the_governed_authority_path():
    # 35
    simple = _row("POST", "/api/cam/retract/gcode")
    download = _row("POST", "/api/cam/retract/gcode/download")
    alias = _row("POST", "/api/cam/retract/gcode_governed")
    download_alias = _row("POST", "/api/cam/retract/gcode/download_governed")
    assert simple["containment"] == "FAIL_CLOSED"
    assert simple["authority_key"] == "retract:{strategy}"
    assert simple["authority_order"] == "before_generation"
    assert simple["proof_status"] == "RUNTIME_PROVED"
    assert download["authority_key"] == "retract:{strategy}"
    assert download["containment"] == "FAIL_CLOSED"
    assert alias["classification"] == "CONFIRMED_DELEGATE"
    assert alias["delegates_to"] == "generate_simple_retract_gcode"
    assert alias["authority_key"] == simple["authority_key"]
    assert alias["implementation_symbol"] == simple["implementation_symbol"]
    assert download_alias["delegates_to"] == "download_retract_gcode"
    assert download_alias["authority_key"] == download["authority_key"]
    assert download_alias["containment"] == "FAIL_CLOSED"


def test_polygon_and_geometry_drafts_stay_outside_the_governed_lane():
    # 36, 60
    governed = _row("POST", "/api/cam/polygon_offset_governed.nc")
    draft = _row("POST", "/api/cam/polygon_offset.nc")
    assert governed["authority_key"] == "cam_polygon_offset_nc"
    assert governed["containment"] == "FAIL_CLOSED"
    assert draft["containment"] == "LIVE_UNGOVERNED"
    assert draft["implementation_symbol"] == governed["implementation_symbol"]
    export = _row("POST", "/api/geometry/export_gcode_governed")
    export_draft = _row("POST", "/api/geometry/export_gcode")
    assert export["authority_key"] == "geometry_export_gcode"
    assert export["containment"] == "FAIL_CLOSED"
    assert export["implementation_kind"] == "postprocessor"
    assert export_draft["containment"] == "LIVE_UNGOVERNED"


def test_probe_downloads_use_distinct_tool_ids():
    # 37
    for path, key in PROBE_KEYS.items():
        row = _row("POST", path)
        assert row["authority_key"] == key
        assert row["containment"] == "FAIL_CLOSED"
        assert "probe_patterns" in row["implementation_symbol"]
    assert _row("POST", "/api/probe/boss/gcode")["containment"] == "LIVE_UNGOVERNED"
    assert len({_row("POST", path)["authority_key"] for path in PROBE_KEYS}) == 5


def test_guitar_body_routes_keep_their_readiness_keys():
    # 41, 42
    expected = (
        ("/api/cam/guitar/stratocaster/body/gcode", "stratocaster_body"),
        ("/api/cam/guitar/les_paul/body/gcode", "les_paul_body"),
        ("/api/cam/guitar/acoustic/{style}/body/gcode", "acoustic_body"),
        ("/api/cam/guitar/acoustic/{style}/soundhole/gcode", "acoustic_soundhole"),
        ("/api/cam/guitar/acoustic/{style}/binding/gcode", "acoustic_binding"),
    )
    for path, key in expected:
        row = _row("POST", path)
        assert row["authority_key"] == key
        assert row["authority_layer"] == "readiness"
        assert row["containment"] == "FAIL_CLOSED"


def test_readiness_keys_in_the_inventory_exist():
    # 38
    from app.cam.generator_readiness import GENERATOR_READINESS

    for row in _document()["rows"]:
        if row["authority_layer"] == "readiness" and row["authority_key"]:
            assert row["authority_key"] in GENERATOR_READINESS


def test_an_unknown_readiness_key_fails_validation():
    # 39
    from app.ci.manufacturing_output_inventory import check_inventory

    class Empty:
        routes = []

    document = {"base_sha": "x" * 40, "rows": [{
        "method": "POST",
        "path": "/missing",
        "handler": "missing",
        "authority_layer": "readiness",
        "authority_key": "not_a_real_generator",
        "classification": "UNEXAMINED",
        "containment": "UNKNOWN",
        "authority_order": "unknown",
        "implementation_kind": "unknown",
        "implementation_symbol": None,
        "delegates_to": None,
        "authentication": "unknown",
        "proof_status": "UNEXAMINED",
        "response_carrier": "none",
        "route_name": "",
        "source_file": "",
        "evidence": "",
        "notes": "UNEXAMINED is not a safety claim.",
    }]}
    # The row is also stale against an empty route list; the readiness error is the point.
    problems = check_inventory(document, Empty.routes)
    assert any("not_a_real_generator" in item for item in problems)


def test_program_detector_reads_commands_and_ignores_prose():
    # 45, 46, 47, 48, 49, 50
    from _manufacturing_output_testkit import first_statement_gate_key

    assert records_in_program_text("G0 X0 Y0\nG1 Z-1.0 F10\nM3\n") == ["G0", "G1", "M3"]
    prose = {
        "detail": {
            "reason": "G0 rapids and G1 feeds and M3 remain unqualified.",
            "evidence": ["G0 Z-1\nM3"],
            "message": "see G1",
            "exit_condition": "quote G0 until qualified",
        }
    }
    assert records_in_json(prose) == []
    raw = b'{"gcode": "G0 X0 Y0\\nG1 Z-1.0 F10\\nM3\\n"}'
    assert program_records("application/json", raw) == ["G0", "G1", "M3"]
    attachment = b'G0 X0\nG1 Z-1\n'
    assert program_records("text/plain", attachment) == ["G0", "G1"]
    source = (
        "def handler(req):\n"
        '    """G0 in a docstring is not the gate."""\n'
        '    _readiness_gate("neck")\n'
        "    return req\n"
    )
    assert first_statement_gate_key(source, "handler") == "neck"
    misordered = (
        "def handler(req):\n"
        "    program = build()\n"
        '    _readiness_gate("neck")\n'
        "    return program\n"
    )
    assert first_statement_gate_key(misordered, "handler") is None


def test_inventory_does_not_permit_and_keeps_drafts_ungoverned():
    # 60
    rows = _document()["rows"]
    assert all(row["containment"] != "PERMITTED_BY_AUTHORITY" for row in rows)
    assert _row("POST", "/api/probe/boss/gcode/download")["containment"] == "LIVE_UNGOVERNED"
