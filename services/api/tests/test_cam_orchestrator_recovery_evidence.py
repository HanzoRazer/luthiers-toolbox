"""CAM-ORCHESTRATOR-RECOVERY-EVIDENCE-001: the evidence, and the tool that measured it.

Two kinds of test live here:

* **Parser unit tests** on synthetic G-code -- the investigation parser is only
  trustworthy if it can fail. Each case names the mistake it guards against.
* **Evidence-integrity tests** on the committed records -- the recorded hashes,
  the 702 baseline and the disposition must agree across every record.

The full replay programs are not committed. ``replay/regenerate_programs.py``
rebuilds them from pinned history and checks their hashes and ``metrics.json``;
that needs full Git history, so it is not run here.

Pure offline text analysis; nothing here imports the application or drives a
machine. Runtime is dominated by the repository's API-test setup, so the cases
are table-driven and related checks share one test.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "scripts" / "investigations" / "neck_gcode_motion_metrics.py"
BUNDLE = REPO_ROOT / "docs" / "investigations" / "cam-orchestrator-recovery_2026-10-14"
RESULTS = BUNDLE / "replay" / "results"

GENERATED_ARMS = ("A_pre_p1", "B_live", "D_bundle_as_shipped", "E_bundle_on_pre_p1")


def _load_tool():
    spec = importlib.util.spec_from_file_location("neck_gcode_motion_metrics", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mm = _load_tool()


def analyse(*lines: str) -> dict:
    return mm.analyse("\n".join(lines) + "\n", plane_z=0.0)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
# Parser
# -----------------------------------------------------------------------------

def test_malformed_or_absent_gcode_is_refused():
    cases = [
        ("", "empty program"),
        ("   \n\n", "empty program"),
        ("( only a comment )\n%\n", "no executable blocks"),
        ("G0 X1 ?? Z2\n", "unparseable"),
        ("G0 X1 ( never closed\n", "unclosed comment"),
        ("G0 X1 )\n", "no open comment"),
        ("X1 Y2\n", "axis words before any motion mode"),
    ]
    for text, reason in cases:
        with pytest.raises(mm.MalformedProgram, match=reason):
            mm.analyse(text, plane_z=0.0)


def test_cli_refuses_bad_input_and_has_no_default_plane(tmp_path):
    out = tmp_path / "m.json"
    missing = mm.main(["--plane-z", "0", "--out", str(out), f"X={tmp_path / 'nope.nc'}"])
    bad = tmp_path / "bad.nc"
    bad.write_text("G0 X1 ??\n", encoding="utf-8")
    malformed = mm.main(["--plane-z", "0", "--out", str(out), f"X={bad}"])
    assert (missing, malformed) == (2, 3)
    assert not out.exists(), "a refused run must not write a report"
    with pytest.raises(SystemExit):
        mm.main(["--out", str(out), f"X={tmp_path / 'a.nc'}"])


def test_modal_motion_is_counted_correctly():
    cases = [
        # The pre-P1 defect shape: no Z word on the rapid line at all.
        ("rapid inherits depth from an earlier feed block",
         ["G1 Z-5.495 F1200", "G0 X-19.350", "G1 Z-7.968", "G0 X-18.275"],
         {"g0_below_plane": 2, "g0_xy_below_plane": 2}),
        ("motion mode is modal: X alone after G0 is still a rapid",
         ["G0 Z5", "G1 Z-2 F300", "G0 X1", "X2", "X3"],
         {"g0_xy_below_plane": 3}),
        ("a Z retract is not travel at depth",
         ["G1 Z-5 F300", "G0 Z25", "G0 X10 Y10"],
         {"g0_below_plane": 0, "g0_xy_below_plane": 0, "g0_z_only_heights": {"25.000": 1}}),
        ("a safe program counts zero",
         ["G0 Z25", "G0 X-21.5", "G1 Z-5 F300", "G1 X-19.35 F1200", "G0 Z25"],
         {"g0_below_plane": 0, "g0_at_or_below_plane": 0}),
        ("the plane itself is counted separately from below it",
         ["G1 Z0 F300", "G0 X5"],
         {"g0_below_plane": 0, "g0_at_or_below_plane": 1}),
    ]
    for name, lines, expected in cases:
        m = analyse(*lines)
        assert {k: m[k] for k in expected} == expected, name


def test_tool_changes_and_spindle_state_are_tracked():
    [tc] = analyse("G0 Z25", "M5", "T2 M6", "G43 H2", "S20000 M3", "G4 P2.0", "G0 Z25")["tool_changes"]
    assert (tc["tool"], tc["z_at_change"], tc["spindle_at_change"]) == (2, 25.0, "off")
    assert tc["g43_before_next_motion"] is True

    flags = [
        ("change with the spindle running", ["G0 Z25", "S18000 M3", "T1 M6", "G0 Z25"],
         "tool_changes_with_spindle_on"),
        ("change without G43", ["G0 Z25", "M5", "T1 M6", "G0 X1"], "tool_changes_without_g43"),
        ("change before any Z word is unknown, not safe", ["M5", "T2 M6", "G43 H2", "G0 Z25"],
         "tool_changes_without_known_retract"),
    ]
    for name, lines, key in flags:
        assert analyse(*lines)[key] == 1, name

    for code, state in (("M3", "cw"), ("M4", "ccw"), ("M5", "off")):
        m = analyse("G0 Z25", "S1000 M3", code, "T1 M6", "G43 H1", "G0 Z25")
        assert m["tool_changes"][0]["spindle_at_change"] == state, code


def test_text_that_must_not_change_the_answer():
    m = analyse("G0 Z25", "( G0 X1 Z-5 M6 M3 )", "; G0 X1 Z-5 M6", "G0 X0")
    assert (m["g0_below_plane"], m["tool_change_count"]) == (0, 0), "comments created commands"

    assert analyse("( Scale length: 647.70mm (25.500in) )", "G0 Z25")["nested_comment_lines"] == 1

    plain = analyse("G1 Z-5 F300", "G0 X1", "G0 Z25")
    noisy = analyse("N10 G1Z-5F300", "  N20   G0   X1  ", "N30 G0 Z25   ")
    keys = ("g0_moves", "g0_below_plane", "g0_xy_below_plane", "g0_z_only_heights")
    assert {k: plain[k] for k in keys} == {k: noisy[k] for k in keys}, "line numbers changed metrics"


def test_the_cli_report_is_deterministic(tmp_path):
    program = tmp_path / "p.nc"
    program.write_text("G0 Z25\nM5\nT2 M6\nG43 H2\nG1 Z-5 F300\nG0 X1\nG0 Z25\n", encoding="utf-8")
    out_a, out_b = tmp_path / "a.json", tmp_path / "b.json"
    assert mm.main(["--plane-z", "0.0", "--out", str(out_a), f"P={program}"]) == 0
    assert mm.main(["--plane-z", "0.0", "--out", str(out_b), f"P={program}"]) == 0
    assert out_a.read_bytes() == out_b.read_bytes()


# -----------------------------------------------------------------------------
# Evidence integrity
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def evidence() -> dict:
    return _json(BUNDLE / "EVIDENCE.json")


@pytest.fixture(scope="module")
def metrics() -> dict:
    return _json(RESULTS / "metrics.json")


def test_every_record_pins_the_same_program_hash(evidence, metrics):
    """EVIDENCE.json, metrics.json and each arm record agree; no two arms share a program."""
    for arm in GENERATED_ARMS:
        record = _json(RESULTS / f"{arm}.json")
        assert record["arm"] == arm
        recorded = {evidence["arms"][arm]["program_sha256"], metrics["arms"][arm]["sha256"],
                    record["gcode_sha256"]}
        assert len(recorded) == 1, f"{arm}: records disagree on the program hash: {recorded}"
    hashes = [evidence["arms"][a]["program_sha256"] for a in GENERATED_ARMS]
    assert len(set(hashes)) == len(hashes), "two arms share a program hash"
    metrics_sha = hashlib.sha256((RESULTS / "metrics.json").read_bytes()).hexdigest()
    assert evidence["artifacts"]["replay_metrics"]["sha256"] == metrics_sha


def test_evidence_metrics_agree_with_the_report(evidence, metrics):
    for arm in GENERATED_ARMS:
        for key, value in evidence["arms"][arm]["metrics"].items():
            assert metrics["arms"][arm][key] == value, f"{arm}.{key}"


def test_the_full_programs_are_not_committed():
    """Executable G-code stays out of the public tree; excerpts and hashes are the record."""
    programs = [p.name for p in BUNDLE.rglob("*") if p.suffix in {".nc", ".gcode", ".ngc", ".tap", ".evidence"}]
    assert programs == []


def test_excerpts_are_pinned_to_the_recorded_programs(metrics):
    excerpts = (RESULTS / "EXCERPTS.md").read_text(encoding="utf-8")
    for arm in GENERATED_ARMS:
        m = metrics["arms"][arm]
        section = excerpts.split(f"## {arm}\n", 1)[1].split("\n## ", 1)[0]
        assert m["sha256"] in section, f"{arm}: excerpt not pinned to its program"
        for line in m["first_violation_lines"][:1] + [tc["line"] for tc in m["tool_changes"]]:
            assert f"(line {line}):" in section, f"{arm}: no excerpt for line {line}"


def test_the_baseline_is_702_not_780_and_the_candidate_duplicates_tool_changes(metrics):
    def arm(name: str) -> dict:
        return metrics["arms"][name]

    assert arm("A_pre_p1")["g0_xy_below_plane"] == 702, "the repeatable historical count"
    assert arm("B_live")["g0_xy_below_plane"] == 0
    assert arm("E_bundle_on_pre_p1")["g0_xy_below_plane"] == 702, "the archived orchestrator never touched the defect"
    assert (arm("B_live")["tool_change_count"], arm("D_bundle_as_shipped")["tool_change_count"]) == (4, 8)


def test_the_disposition_is_the_ruling(evidence):
    arm = evidence["arms"]["C_archived_on_live"]
    assert (arm["status"], arm["error_type"]) == ("NOT_RUNNABLE", "AttributeError")
    assert "dwell_after_spindle_ms" in arm["error"]
    assert evidence["disposition"] == {
        "rapid_at_depth_defect": "SUPERSEDED",
        "archived_as_written": "INCOMPATIBLE_WITH_CURRENT_RUNTIME",
        "forward_port": "DO_NOT_FORWARD_PORT",
        "ruled_by": "owner, 2026-10-14",
    }
    assert evidence["production_behavior_changed"] is False
    assert evidence["manufacturing_approved"] is False


#: Phrases that would claim authority this evidence does not have.
_AUTHORITY_CLAIMS = re.compile(
    r"\b(is|are|now) (production[- ]authori[sz]ed|manufacturing[- ]approved|approved for "
    r"(production|manufacturing|machining))\b",
    re.IGNORECASE,
)

#: A denial ("Nothing here is manufacturing-approved") is the opposite of a claim.
_NEGATION = re.compile(r"\b(not|no|nothing|never|none)\b|n't\b", re.IGNORECASE)


def claims_authority(line: str) -> bool:
    """True when a line affirms authority; negated statements in the same sentence do not count.

    A lint for the obvious phrasings, not a proof that no document overclaims.
    """
    for match in _AUTHORITY_CLAIMS.finditer(line):
        sentence_start = max(line.rfind(".", 0, match.start()), line.rfind(";", 0, match.start())) + 1
        if not _NEGATION.search(line[sentence_start:match.start()]):
            return True
    return False


def test_the_authority_detector_separates_claims_from_denials():
    cases = [
        ("The archived orchestrator is production-authorized.", True),
        ("Evidence only. The replay program is now approved for machining.", True),
        ("Nothing here is manufacturing-approved.", False),
        ("This is not production-authorized.", False),
        ("Nothing here is approved. The candidate is production-authorized.", True),
    ]
    for line, expected in cases:
        assert claims_authority(line) is expected, line


def test_evidence_documents_keep_the_owner_rulings():
    """No authority claims; CL-RED was a typo (owner, 2026-10-14); no collision record exists."""
    authority, cl_red, collision = [], [], []
    for path in sorted(BUNDLE.rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            where = f"{path.name}:{number}"
            if claims_authority(line):
                authority.append(f"{where}: {line.strip()}")
            if "CL-RED" in line and not re.search(r"typo|\bnot\b|erratum", line, re.IGNORECASE):
                cl_red.append(where)
            if re.search(r"namespace[- ]collision", line, re.IGNORECASE) and not _NEGATION.search(line):
                collision.append(where)
    assert authority == [], authority
    assert cl_red == [], f"CL-RED used as a recovery object: {cl_red}"
    assert collision == [], f"loss attributed to a namespace collision: {collision}"
