"""CAM-ORCHESTRATOR-RECOVERY-EVIDENCE-001: the evidence, and the tool that measured it.

Two kinds of test live here:

* **Parser unit tests** on synthetic G-code -- the investigation parser is only
  trustworthy if it can fail. Each test names the mistake it guards against.
* **Evidence-integrity tests** on the committed replay programs -- the recorded
  hashes, the 702 baseline, and the disposition must agree with the files.

Nothing here imports the application or drives a machine. Pure text, fast.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "scripts" / "investigations" / "neck_gcode_motion_metrics.py"
BUNDLE = REPO_ROOT / "docs" / "investigations" / "cam-orchestrator-recovery_2026-10-14"
RESULTS = BUNDLE / "replay" / "results"
EVIDENCE = BUNDLE / "EVIDENCE.json"

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


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# -----------------------------------------------------------------------------
# Parser: refusal
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("text, reason", [
    ("", "empty program"),
    ("   \n\n", "empty program"),
    ("( only a comment )\n%\n", "no executable blocks"),
    ("G0 X1 ?? Z2\n", "unparseable"),
    ("G0 X1 ( never closed\n", "unclosed comment"),
    ("G0 X1 )\n", "no open comment"),
    ("X1 Y2\n", "axis words before any motion mode"),
])
def test_malformed_or_absent_gcode_is_refused(text, reason):
    with pytest.raises(mm.MalformedProgram, match=reason):
        mm.analyse(text, plane_z=0.0)


def test_cli_refuses_missing_file_and_malformed_input(tmp_path):
    out = tmp_path / "m.json"
    missing = mm.main(["--plane-z", "0", "--out", str(out), f"X={tmp_path / 'nope.nc'}"])
    bad = tmp_path / "bad.nc"
    bad.write_text("G0 X1 ??\n", encoding="utf-8")
    malformed = mm.main(["--plane-z", "0", "--out", str(out), f"X={bad}"])
    assert (missing, malformed) == (2, 3)
    assert not out.exists(), "a refused run must not write a report"


def test_cli_has_no_default_plane(tmp_path):
    with pytest.raises(SystemExit):
        mm.main(["--out", str(tmp_path / "m.json"), f"X={tmp_path / 'a.nc'}"])


# -----------------------------------------------------------------------------
# Parser: modal motion
# -----------------------------------------------------------------------------

def test_a_rapid_inherits_its_depth_from_an_earlier_feed_block():
    """The pre-P1 defect shape: no Z word on the rapid line at all."""
    m = analyse("G1 Z-5.495 F1200", "G0 X-19.350", "G1 Z-7.968", "G0 X-18.275")
    assert m["g0_below_plane"] == 2
    assert m["g0_xy_below_plane"] == 2


def test_motion_mode_is_modal_too():
    """``X`` alone after ``G0`` is still a rapid."""
    m = analyse("G0 Z5", "G1 Z-2 F300", "G0 X1", "X2", "X3")
    assert m["g0_xy_below_plane"] == 3


def test_a_z_retract_is_not_counted_as_travel_at_depth():
    m = analyse("G1 Z-5 F300", "G0 Z25", "G0 X10 Y10")
    assert m["g0_below_plane"] == 0
    assert m["g0_xy_below_plane"] == 0
    assert m["g0_z_only_heights"] == {"25.000": 1}


def test_a_safe_program_counts_zero():
    m = analyse("G0 Z25", "G0 X-21.5", "G1 Z-5 F300", "G1 X-19.35 F1200", "G0 Z25")
    assert (m["g0_below_plane"], m["g0_at_or_below_plane"]) == (0, 0)


def test_the_plane_itself_is_counted_separately_from_below_it():
    m = analyse("G1 Z0 F300", "G0 X5")
    assert (m["g0_below_plane"], m["g0_at_or_below_plane"]) == (0, 1)


# -----------------------------------------------------------------------------
# Parser: tool changes and spindle
# -----------------------------------------------------------------------------

def test_tool_change_sequence_is_detected():
    m = analyse("G0 Z25", "M5", "T2 M6", "G43 H2", "S20000 M3", "G4 P2.0", "G0 Z25")
    [tc] = m["tool_changes"]
    assert (tc["tool"], tc["z_at_change"], tc["spindle_at_change"]) == (2, 25.0, "off")
    assert tc["g43_before_next_motion"] is True


def test_a_change_with_the_spindle_running_is_flagged():
    m = analyse("G0 Z25", "S18000 M3", "T1 M6", "G0 Z25")
    assert m["tool_changes_with_spindle_on"] == 1


def test_a_change_without_g43_is_flagged():
    m = analyse("G0 Z25", "M5", "T1 M6", "G0 X1")
    assert m["tool_changes_without_g43"] == 1


def test_a_change_before_any_z_word_is_unknown_not_safe():
    m = analyse("M5", "T2 M6", "G43 H2", "G0 Z25")
    assert m["tool_changes_without_known_retract"] == 1


@pytest.mark.parametrize("code, state", [("M3", "cw"), ("M4", "ccw"), ("M5", "off")])
def test_spindle_state_is_tracked(code, state):
    m = analyse("G0 Z25", "S1000 M3", code, "T1 M6", "G43 H1", "G0 Z25")
    assert m["tool_changes"][0]["spindle_at_change"] == state


# -----------------------------------------------------------------------------
# Parser: text that must not change the answer
# -----------------------------------------------------------------------------

def test_comments_do_not_create_commands():
    m = analyse("G0 Z25", "( G0 X1 Z-5 M6 M3 )", "; G0 X1 Z-5 M6", "G0 X0")
    assert (m["g0_below_plane"], m["tool_change_count"]) == (0, 0)


def test_nested_comments_are_stripped_and_reported():
    m = analyse("( Scale length: 647.70mm (25.500in) )", "G0 Z25")
    assert m["nested_comment_lines"] == 1


def test_line_numbers_and_whitespace_do_not_change_metrics():
    plain = analyse("G1 Z-5 F300", "G0 X1", "G0 Z25")
    noisy = analyse("N10 G1Z-5F300", "  N20   G0   X1  ", "N30 G0 Z25   ")
    keys = ("g0_moves", "g0_below_plane", "g0_xy_below_plane", "g0_z_only_heights")
    assert {k: plain[k] for k in keys} == {k: noisy[k] for k in keys}


# -----------------------------------------------------------------------------
# Evidence integrity
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def evidence() -> dict:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def metrics() -> dict:
    return json.loads((RESULTS / "metrics.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("arm", GENERATED_ARMS)
def test_recorded_program_hashes_match_the_files(arm, evidence, metrics):
    actual = _sha(RESULTS / f"{arm}.gcode.txt")
    assert evidence["arms"][arm]["program_sha256"] == actual
    assert metrics["arms"][arm]["sha256"] == actual


def test_recorded_metrics_hash_matches_the_file(evidence):
    assert evidence["artifacts"]["replay_metrics"]["sha256"] == _sha(RESULTS / "metrics.json")


def test_arms_cannot_be_silently_swapped(evidence):
    """Every arm's program is distinct, and each is pinned to its own name."""
    hashes = [evidence["arms"][a]["program_sha256"] for a in GENERATED_ARMS]
    assert len(set(hashes)) == len(hashes)
    for arm in GENERATED_ARMS:
        record = json.loads((RESULTS / f"{arm}.json").read_text(encoding="utf-8"))
        assert record["arm"] == arm
        assert record["gcode_file"] == f"{arm}.gcode.txt"


def test_metrics_are_deterministic_and_reproduce_the_committed_report(tmp_path):
    out_a, out_b = tmp_path / "a.json", tmp_path / "b.json"
    arms = [f"{a}={RESULTS / f'{a}.gcode.txt'}" for a in GENERATED_ARMS]
    assert mm.main(["--plane-z", "0.0", "--out", str(out_a), *arms]) == 0
    assert mm.main(["--plane-z", "0.0", "--out", str(out_b), *arms]) == 0
    assert out_a.read_bytes() == out_b.read_bytes()
    regenerated = json.loads(out_a.read_text(encoding="utf-8"))
    committed = json.loads((RESULTS / "metrics.json").read_text(encoding="utf-8"))
    for arm in GENERATED_ARMS:
        regenerated["arms"][arm].pop("source")
        committed["arms"][arm].pop("source")
    assert regenerated == committed


def test_the_baseline_is_702_not_780():
    """The repeatable historical count, measured from the committed programs."""
    def count(arm):
        text = (RESULTS / f"{arm}.gcode.txt").read_text(encoding="utf-8")
        return mm.analyse(text, plane_z=0.0)["g0_xy_below_plane"]

    assert count("A_pre_p1") == 702
    assert count("B_live") == 0
    assert count("E_bundle_on_pre_p1") == 702, "the archived orchestrator never touched the defect"


def test_the_archived_bundle_duplicates_tool_changes():
    def changes(arm):
        text = (RESULTS / f"{arm}.gcode.txt").read_text(encoding="utf-8")
        return mm.analyse(text, plane_z=0.0)["tool_change_count"]

    assert (changes("B_live"), changes("D_bundle_as_shipped")) == (4, 8)


def test_the_archived_orchestrator_is_recorded_as_not_runnable(evidence):
    arm = evidence["arms"]["C_archived_on_live"]
    assert arm["status"] == "NOT_RUNNABLE"
    assert arm["error_type"] == "AttributeError"
    assert "dwell_after_spindle_ms" in arm["error"]


def test_the_disposition_is_the_ruling(evidence):
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
    """True when a line affirms authority; negated statements in the same sentence do not count."""
    for match in _AUTHORITY_CLAIMS.finditer(line):
        sentence_start = max(line.rfind(".", 0, match.start()), line.rfind(";", 0, match.start())) + 1
        if not _NEGATION.search(line[sentence_start:match.start()]):
            return True
    return False


def test_no_evidence_document_claims_production_authority():
    offenders = []
    for path in sorted(BUNDLE.rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if claims_authority(line):
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert offenders == []


@pytest.mark.parametrize("line, expected", [
    ("The archived orchestrator is production-authorized.", True),
    ("Evidence only. The replay program is now approved for machining.", True),
    ("Nothing here is manufacturing-approved.", False),
    ("This is not production-authorized.", False),
    ("Nothing here is approved. The candidate is production-authorized.", True),
])
def test_the_authority_detector_separates_claims_from_denials(line, expected):
    assert claims_authority(line) is expected


#: Paths this evidence PR may touch. Anything else is a production change.
_ALLOWED = (
    "docs/investigations/cam-orchestrator-recovery_2026-10-14/",
    "docs/investigations/march-2026-consolidation-recovery-census/",
    "scripts/investigations/",
    "services/api/tests/test_cam_orchestrator_recovery_evidence.py",
    ".cbsp21/patches/",
)


def test_no_production_application_file_changed():
    try:
        base = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "HEAD", "origin/main"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        changed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--name-only", base, "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"NOT_RUN: no origin/main to diff against ({exc}); CBSP21 coverage gate enforces scope in CI")
    if not any(p.startswith(_ALLOWED[0]) for p in changed):
        pytest.skip("NOT_RUN: HEAD is not the evidence branch")
    outside = [p for p in changed if not p.startswith(_ALLOWED)]
    assert outside == [], f"evidence PR touched non-evidence paths: {outside}"
