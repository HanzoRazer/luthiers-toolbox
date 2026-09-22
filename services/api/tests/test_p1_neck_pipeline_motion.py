"""LTB-REMEDIATE-P1: the neck profile emitter, corrected.

The profile-carving station loop alternated ``G1 Z<depth>`` with ``G0 X<next>``,
so every lateral stepover was a rapid with the cutter engaged -- 702 of them,
down to Z=-25.000mm.

What the correction claims, and no more: ordered tool positions and motion-block
count are unchanged; 720 moves were intentionally changed from rapid to
controlled-feed motion, eliminating all rapid travel below Z=0. Motion
semantics, speed and cycle time change by design.

**Scope.** This is a fail-closed and rapid-removal patch. Correcting the motion
does NOT qualify the generator for cutting. A second motion defect -- the
profile passes plunge at the tool's lateral feed rather than its plunge feed --
is recorded in the ``neck_pipeline_full`` exit condition and deliberately not
fixed here.

Why every assertion is modal rather than textual: all 702 violations inherited
their Z from an earlier block. **Not one carried an explicit Z word**, so a grep
for a rapid and a negative Z on the same line found *zero* of them. A substring
test would have reported this emitter clean while it was at its worst.

Read-only with respect to hardware: nothing here drives a machine.
"""
import re

import pytest

pytestmark = pytest.mark.allow_missing_request_id

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
#: The program declares its own operations, e.g. "( OP40: Neck Profile Rough )".
#: Scoping assertions by that header is more honest than guessing which moves the
#: profile passes emitted -- the other operations emit X-only feed moves too.
_OP_HEADER = re.compile(r"\(\s*(OP\d+):")
#: Each profile station opens with "( Station: Y = ... )".
_STATION_HEADER = re.compile(r"\(\s*Station:")
#: The two operations LTB-REMEDIATE-P1 changed.
PROFILE_OPS = ("OP40", "OP45")


def _decode_words(words) -> tuple:
    """One block's words -> (motion mode or None, axis words, feed or None)."""
    axes: dict[str, float] = {}
    motion_here = None
    feed_here = None
    for letter, value in words:
        upper = letter.upper()
        if upper == "G" and int(float(value)) in _MOTION:
            motion_here = _MOTION[int(float(value))]
        elif upper in ("X", "Y", "Z"):
            axes[upper] = float(value)
        elif upper == "F":
            feed_here = float(value)
    return motion_here, axes, feed_here


def _track_headers(raw: str, operation, station: int) -> tuple:
    """A station index is per operation; blocks before the first station are 0."""
    header = _OP_HEADER.search(raw)
    if header:
        return header.group(1), 0
    if _STATION_HEADER.search(raw):
        return operation, station + 1
    return operation, station


def parse_motion(program: str) -> list[dict]:
    """Resolve a program into motion blocks with modal state applied.

    Both motion mode and axis words persist across blocks, so ``G0 X-19.350``
    following ``G1 Z-5.495`` is a rapid *at Z=-5.495*. This returns the resolved
    position for every block that carries an axis word.
    """
    state = {"motion": None, "X": None, "Y": None, "Z": None, "F": None}
    blocks: list[dict] = []
    operation = None
    station = 0
    for number, raw in enumerate(program.splitlines(), 1):
        operation, station = _track_headers(raw, operation, station)
        words = _WORD.findall(re.sub(r"\([^)]*\)", "", raw.split(";")[0]))
        if not words:
            continue
        motion_here, axes, feed_here = _decode_words(words)
        if motion_here is not None:
            state["motion"] = motion_here
        if feed_here is not None:
            state["F"] = feed_here
        for axis, value in axes.items():
            state[axis] = value
        if axes and state["motion"] is not None:
            blocks.append({
                "line": number,
                "motion": state["motion"],
                "X": state["X"], "Y": state["Y"], "Z": state["Z"],
                "F": state["F"],
                "z_explicit": "Z" in axes,
                "f_explicit": feed_here is not None,
                "axes": sorted(axes),
                "operation": operation,
                "station": station,
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


def test_no_engaged_move_is_a_rapid():
    """Below the surface, every move is a feed move.

    This checks motion mode only. Whether the tool still visits the same places
    is a separate claim, proved independently by
    ``test_the_toolpath_visits_exactly_the_stations_profile_points``.
    """
    blocks = parse_motion(_full_program())
    engaged = [b for b in blocks if b["Z"] is not None and b["Z"] < WORKPIECE_TOP_MM]

    assert engaged, "the program must still cut below the surface"
    assert all(b["motion"] != "G0" for b in engaged)
    assert any(b["motion"] == "G1" for b in engaged)


def test_no_feed_move_executes_before_a_feed_is_established():
    """A G1 with no F in effect runs at whatever the control last held.

    That is a real hazard on a shared machine, and it is the first thing a
    rapid-to-feed conversion can get wrong.
    """
    without_feed = [
        block for block in parse_motion(_full_program())
        if block["motion"] == "G1" and block["F"] is None
    ]

    assert without_feed == [], (
        f"{len(without_feed)} feed move(s) with no feed established; "
        f"first at line {without_feed[0]['line'] if without_feed else '-'}"
    )


def test_converted_lateral_moves_carry_the_lateral_feed_not_the_plunge_feed():
    """The converted moves must cut at the tool's cutting feed.

    ``NeckToolSpec`` carries both ``feed_mm_min`` and ``plunge_mm_min``, and the
    plunge rate is roughly half. A conversion that silently adopted the plunge
    feed would be safe but wrong, and one that adopted a *higher* rate would be
    worse than the defect it replaced. Each converted move therefore carries an
    explicit F, and this pins which value it is.
    """
    from app.routers.cam.cam_workspace_router import (
        NeckConfigIn,
        _build_pipeline_config,
    )

    config = _build_pipeline_config(NeckConfigIn())
    rough, finish = config.tools.get(1), config.tools.get(3)

    lateral = [
        block for block in parse_motion(_full_program())
        if block["motion"] == "G1"
        and block["axes"] == ["X"]
        and block["operation"] in PROFILE_OPS
        and block["Z"] is not None
        and block["Z"] < WORKPIECE_TOP_MM
    ]

    assert lateral, "the profile passes must still cut laterally"
    assert all(block["f_explicit"] for block in lateral), (
        "every converted lateral move must state its own feed rather than inherit one"
    )

    feeds = {block["F"] for block in lateral}
    assert feeds <= {rough.feed_mm_min, finish.feed_mm_min}
    assert rough.plunge_mm_min not in feeds
    assert finish.plunge_mm_min not in feeds


def test_the_lateral_feed_is_not_faster_than_the_tool_allows():
    """No converted move may exceed its tool's declared cutting feed."""
    from app.routers.cam.cam_workspace_router import (
        NeckConfigIn,
        _build_pipeline_config,
    )

    config = _build_pipeline_config(NeckConfigIn())
    ceiling = max(tool.feed_mm_min for tool in config.tools.values())

    engaged_feeds = [
        block["F"] for block in parse_motion(_full_program())
        if block["motion"] == "G1"
        and block["Z"] is not None
        and block["Z"] < WORKPIECE_TOP_MM
        and block["F"] is not None
    ]

    assert engaged_feeds
    assert max(engaged_feeds) <= ceiling


def test_the_program_still_retracts_with_rapids_above_the_surface():
    """Containment must not have turned every rapid into a feed move."""
    blocks = parse_motion(_full_program())
    rapids = [b for b in blocks if b["motion"] == "G0"]

    assert rapids, "clearance moves are still rapids"
    assert all(b["Z"] is None or b["Z"] >= WORKPIECE_TOP_MM for b in rapids)


# -----------------------------------------------------------------------------
# Profile transitions -- the modal state where the defect actually lived
# -----------------------------------------------------------------------------

def _profile_pipeline():
    from app.cam.neck.orchestrator import NeckPipeline
    from app.routers.cam.cam_workspace_router import (
        NeckConfigIn,
        _build_pipeline_config,
    )

    return NeckPipeline(_build_pipeline_config(NeckConfigIn()))


def _split_stations(blocks):
    """Split the profile passes into stations and the transitions between them.

    A station runs from its header to its retract -- the first Z-only rapid
    after it has cut. Anything after that retract and before the next header
    (the post-loop clearance move, a tool change) is a *transition*, and is
    returned separately so it can be checked rather than silently dropped.
    """
    grouped: dict[tuple[str, int], list[dict]] = {}
    for block in blocks:
        if block["operation"] in PROFILE_OPS and block["station"]:
            grouped.setdefault((block["operation"], block["station"]), []).append(block)

    stations: dict[tuple[str, int], list[dict]] = {}
    transitions: list[dict] = []
    for key, run in grouped.items():
        cut = False
        for i, block in enumerate(run):
            cut = cut or block["motion"] == "G1"
            if cut and block["motion"] == "G0" and block["axes"] == ["Z"]:
                stations[key] = run[: i + 1]
                transitions.extend(run[i + 1:])
                break
        else:
            stations[key] = run   # no retract: left whole so the assertions fail on it
    return stations, transitions


def _stations_by_operation(blocks):
    return _split_stations(blocks)[0]


def test_modal_state_at_every_station_transition():
    """Assert the modal state across each station, not the text of any line.

    The defect was a transition error: after each plunge the next lateral move
    inherited the plunged Z while the motion mode said rapid. So each station
    is checked as a sequence of resolved states --

    * it opens with a rapid to the clearance height;
    * Y and the first X are positioned *at* clearance, as rapids;
    * from the first plunge until the retract, every block is a feed move with
      a feed in effect -- no rapid while engaged;
    * it closes with a rapid retract to a height at or above the surface.
    """
    pipeline = _profile_pipeline()
    safe_z = pipeline.profile_gen.safe_z_mm
    retract_z = pipeline.profile_gen.retract_z_mm
    assert retract_z >= WORKPIECE_TOP_MM

    stations, transitions = _split_stations(parse_motion(_full_program()))
    assert stations, "no profile stations found in the program"

    for (operation, index), blocks in stations.items():
        _assert_station_modal_state(f"{operation} station {index}", blocks, safe_z, retract_z)

    # Between stations and around tool changes: nothing may sit below the surface.
    assert transitions, "expected at least the post-loop clearance moves"
    below = [b["line"] for b in transitions if b["Z"] is not None and b["Z"] < WORKPIECE_TOP_MM]
    assert below == [], f"transition block(s) below the surface at {below}"


def _state(block) -> tuple:
    return block["motion"], block["axes"], block["Z"]


def _assert_station_modal_state(where, blocks, safe_z, retract_z):
    opening, y_move, first_x, *engaged, retract = blocks

    assert _state(opening) == ("G0", ["Z"], safe_z), where
    assert _state(y_move) == ("G0", ["Y"], safe_z), where
    assert _state(first_x) == ("G0", ["X"], safe_z), where

    assert engaged, f"{where}: no cutting moves"
    rapids = [b["line"] for b in engaged if b["motion"] != "G1"]
    assert rapids == [], f"{where}: rapid(s) between the first plunge and the retract at {rapids}"
    assert all(b["F"] is not None for b in engaged), where

    assert _state(retract) == ("G0", ["Z"], retract_z), where


def test_the_toolpath_visits_exactly_the_stations_profile_points():
    """The correction must not move the tool anywhere it did not already go.

    Expected positions are derived independently from the generator's own
    stations -- not from a snapshot of an earlier program -- and compared with
    the position the machine resolves to after every plunge. The roughing pass
    carries the finish allowance; the finishing pass does not.
    """
    pipeline = _profile_pipeline()
    stations = pipeline.profile_gen.generate_stations()
    allowance = pipeline.profile_gen.pc_config.finish_allowance_mm

    def emitted(value: float) -> float:
        return float(f"{value:.3f}")   # exactly what the emitter prints

    expected = {
        "OP40": [[(emitted(x), emitted(s.y_mm), emitted(z + allowance))
                  for x, z in s.profile_points] for s in stations],
        "OP45": [[(emitted(x), emitted(s.y_mm), emitted(z))
                  for x, z in s.profile_points] for s in stations],
    }

    grouped = _stations_by_operation(parse_motion(_full_program()))
    for operation in PROFILE_OPS:
        actual = [
            [(b["X"], b["Y"], b["Z"]) for b in blocks
             if b["motion"] == "G1" and b["axes"] == ["Z"]]
            for (op, _), blocks in sorted(grouped.items()) if op == operation
        ]
        assert actual == expected[operation], f"{operation}: toolpath diverged from its stations"
