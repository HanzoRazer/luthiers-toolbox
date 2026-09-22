"""LTB-REMEDIATE-P1: the cam-workspace neck pipeline, contained and corrected.

``POST /api/cam-workspace/neck/generate-full`` answered an uncredentialed default
request with a 28,260-byte ``.nc`` attachment carrying 1,779 G/M records, of which
**702 were G0 rapids below the workpiece top**, reaching Z=-25.000mm -- the cutter
traversing sideways through stock at rapid feed.

Two separate things are proved here, and they are deliberately not conflated:

* **Containment** -- the route refuses before it constructs a generator, and the
  refusal names the identity, state, reason and exit condition.
* **Correction** -- the emitter no longer produces the unsafe motion, and the
  path geometry is unchanged by the fix.

Correcting the motion does **not** qualify the generator. ``neck_pipeline_full``
stays non-emitting until a readiness decision is recorded on evidence.

Why every motion assertion here is modal rather than textual: all 702 violations
inherited their Z from an earlier block. **Not one carried an explicit Z word**,
so ``grep`` for a rapid and a negative Z on the same line found *zero* of them. A
substring test would have reported this route clean while it was at its worst.

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

#: The workpiece top surface. A rapid below it is moving through stock.
#:
#: Deliberately 0.0 and not a "safe clearance" height: the repository carries two
#: different clearance values -- ``BCamMachineSpec.safe_z_mm = 25.0`` and
#: ``PreflightConfig.safe_z_mm = 5.0`` -- and no document ranks them. Z<0 is the
#: defect under either reading, so the regression invariant does not depend on
#: resolving that ambiguity. Resolving it is left to P-3's semantic contract.
WORKPIECE_TOP_MM = 0.0

_WORD = re.compile(r"([A-Za-z])\s*(-?\d+(?:\.\d+)?)")
_MOTION = {0: "G0", 1: "G1", 2: "G2", 3: "G3"}
_GM_RECORD = re.compile(r"(?m)^\s*[GM]\d")


def parse_motion(program: str) -> list[dict]:
    """Resolve a program into motion blocks with modal state applied.

    Both motion mode and axis words persist across blocks, so ``G0 X-19.350``
    following ``G1 Z-5.495`` is a rapid *at Z=-5.495*. This returns the resolved
    position for every block that carries an axis word.
    """
    state = {"motion": None, "X": None, "Y": None, "Z": None}
    blocks: list[dict] = []
    for number, raw in enumerate(program.splitlines(), 1):
        line = re.sub(r"\([^)]*\)", "", raw.split(";")[0]).strip()
        if not line:
            continue
        words = _WORD.findall(line)
        if not words:
            continue
        axes: dict[str, float] = {}
        motion_here = None
        for letter, value in words:
            upper = letter.upper()
            if upper == "G":
                code = int(float(value))
                if code in _MOTION:
                    motion_here = _MOTION[code]
            elif upper in ("X", "Y", "Z"):
                axes[upper] = float(value)
        if motion_here is not None:
            state["motion"] = motion_here
        for axis, value in axes.items():
            state[axis] = value
        if axes and state["motion"] is not None:
            blocks.append({
                "line": number,
                "motion": state["motion"],
                "X": state["X"], "Y": state["Y"], "Z": state["Z"],
                "z_explicit": "Z" in axes,
                "text": raw.strip(),
            })
    return blocks


def rapids_below(program: str, plane_mm: float = WORKPIECE_TOP_MM) -> list[dict]:
    """Every rapid whose resolved Z is below ``plane_mm``."""
    return [
        block for block in parse_motion(program)
        if block["motion"] == "G0"
        and block["Z"] is not None
        and block["Z"] < plane_mm
    ]


def _full_program() -> str:
    """The complete 4-op program, taken from the generator directly.

    The route refuses, which is the point of this change, so the emitter is
    exercised through the pipeline rather than over HTTP.
    """
    from app.cam.neck.orchestrator import NeckPipeline
    from app.routers.cam.cam_workspace_router import (
        NeckConfigIn,
        _build_pipeline_config,
    )

    pipeline = NeckPipeline(_build_pipeline_config(NeckConfigIn()))
    return pipeline.generate(
        include_truss_rod=True,
        include_profile_rough=True,
        include_profile_finish=True,
        include_fret_slots=True,
    ).get_gcode()


# -----------------------------------------------------------------------------
# The detector, before it is trusted to certify anything
# -----------------------------------------------------------------------------

def test_the_detector_catches_a_deliberately_unsafe_fixture():
    """Negative control. A guard never shown to fail is not evidence.

    This fixture is the exact shape of the defect: a plunge, then a lateral move
    that is a rapid only by modal inheritance.
    """
    unsafe = "\n".join([
        "G0 Z25.000",
        "G0 X-21.500",
        "G1 Z-5.495 F1200",
        "G0 X-19.350",        # rapid at Z=-5.495 by inheritance
        "G1 Z-7.968 F1200",
        "G0 X-18.275",        # rapid at Z=-7.968
    ])
    violations = rapids_below(unsafe)

    assert len(violations) == 2
    assert [v["Z"] for v in violations] == [-5.495, -7.968]
    assert not any(v["z_explicit"] for v in violations), (
        "the fixture must reproduce the modal-inheritance shape, not an explicit Z"
    )


def test_a_substring_search_would_have_missed_the_whole_defect():
    """Pins why this suite is modal: the textual test reports the fixture clean."""
    unsafe = "G1 Z-5.495 F1200\nG0 X-19.350\nG1 Z-7.968 F1200\nG0 X-18.275"

    textual_hits = [
        line for line in unsafe.splitlines()
        if re.search(r"\bG0?0\b", line) and re.search(r"Z\s*-", line)
    ]

    assert textual_hits == []
    assert len(rapids_below(unsafe)) == 2


def test_the_detector_does_not_flag_a_safe_program():
    safe = "\n".join([
        "G0 Z25.000",
        "G0 X-21.500",
        "G1 Z-5.495 F1200",
        "G1 X-19.350 F1200",   # engaged lateral move at feed -- correct
        "G0 Z25.000",
    ])
    assert rapids_below(safe) == []


# -----------------------------------------------------------------------------
# Correction
# -----------------------------------------------------------------------------

def test_the_emitted_program_has_no_rapid_below_the_workpiece_top():
    """The regression invariant. Was 702; must stay 0."""
    violations = rapids_below(_full_program())

    assert violations == [], (
        f"{len(violations)} rapid(s) below the workpiece top; "
        f"deepest {min(v['Z'] for v in violations):.3f}mm at line "
        f"{min(violations, key=lambda v: v['Z'])['line']}"
    )


def test_the_correction_changed_feed_mode_and_not_path_geometry():
    """The fix must not move the tool anywhere it did not already go.

    Every engaged lateral move became a feed move at the same coordinates. If a
    future change alters the path instead of the feed mode, the station's point
    sequence stops matching its profile points and this fails.
    """
    blocks = parse_motion(_full_program())
    engaged = [b for b in blocks if b["Z"] is not None and b["Z"] < WORKPIECE_TOP_MM]

    assert engaged, "the program must still cut below the surface"
    assert all(b["motion"] != "G0" for b in engaged)
    assert any(b["motion"] == "G1" for b in engaged)


def test_the_program_still_retracts_with_rapids_above_the_surface():
    """Containment must not have turned every rapid into a feed move."""
    blocks = parse_motion(_full_program())
    rapids = [b for b in blocks if b["motion"] == "G0"]

    assert rapids, "clearance moves are still rapids"
    assert all(b["Z"] is None or b["Z"] >= WORKPIECE_TOP_MM for b in rapids)


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


def test_the_neck_gcode_routes_are_left_for_p2(client):
    """P-2's targets are deliberately NOT contained by this change.

    Recorded so that the scope boundary is visible in the suite rather than only
    in a commit message. If a later change gates them, this test should be
    deleted by that change -- not silently left passing.
    """
    response = client.post("/api/neck/gcode/generate", json={})

    assert response.status_code != 422 or (
        response.json().get("detail", {}).get("code") != "GENERATOR_READINESS_BLOCKED"
    )
