"""G2-MANUFACTURING-SPINE-001 — contract tests for the current-state registry validator.

Pure contract tests: every registry here is built in-code. No app boot, no
network, no git mutation. The validator checks *claims*; it does not discover
truth, so these tests pin what a claim must carry before it is accepted.

Cases 1-17 are numbered as in the dev order (§9).
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.manufacturing_spine.validate_current_state import (  # noqa: E402
    ORDER_ID,
    validate,
)

LEVELS = ("declared", "wired", "exercised", "effective", "consumed")


def ev(level, kind, ref="services/api/app/x.py:1", temporal="current", synthetic=False):
    return {"level": level, "kind": kind, "ref": ref, "temporal": temporal,
            "synthetic_probe": synthetic}


def row(cid="profiling", surface="manufacturing_capability", **ladder):
    """A row proven exactly as far as the YES flags given; rest UNKNOWN."""
    values = {lvl: ladder.get(lvl, "UNKNOWN") for lvl in LEVELS}
    kinds = {"declared": "registry", "wired": "route_table", "exercised": "runtime",
             "effective": "runtime", "consumed": "consumer_chain"}
    evidence = []
    for lvl in LEVELS:
        if values[lvl] in ("YES", "NO"):
            evidence.append(ev(lvl, kinds[lvl], synthetic=lvl in ("exercised", "effective")))
    maturity = "NONE"
    for lvl in LEVELS:
        if values[lvl] == "YES":
            maturity = lvl.upper()
        else:
            break
    r = {
        "capability_id": cid,
        "surface_kind": surface,
        "historical_disposition": "LIVE_UNGOVERNED_OUTPUT",
        "current_authority_disposition": "GOVERNED",
        "change_since_frozen": "UNCHANGED",
        **values,
        "maturity": maturity,
        "consumer": None,
        "evidence_refs": evidence,
        "limitations": [],
        "next_action": "adjudicate",
        "g2_bucket": "G2-DEFICIT" if surface == "manufacturing_capability" else "NOT-MANUFACTURING",
        "mvs_relevance": "UNKNOWN",
    }
    if values["consumed"] == "YES":
        r["consumer"] = {
            "entry": "packages/client/src/router/index.ts:128",
            "invocation": "packages/client/src/components/toolbox/X.vue:210 generate()",
            "route": "POST /api/cam/x/gcode",
            "result_use": "packages/client/src/components/toolbox/X.vue:240 download",
        }
    return r


def doc(*rows):
    return {
        "schema_version": "manufacturing_spine_current_state.v1",
        "order_id": ORDER_ID,
        "baseline_sha": "0" * 40,
        "historical_authority_map": "docs/audit/rmos_manufacturing_authority_map_001.md",
        "capabilities": list(rows),
    }


def errors_of(d, **kw):
    return validate(d, **kw)


def assert_ok(d, **kw):
    errs = errors_of(d, **kw)
    assert errs == [], errs


def assert_rejected(d, needle, **kw):
    errs = errors_of(d, **kw)
    assert any(needle in e for e in errs), f"expected an error containing {needle!r}, got {errs}"


# ------------------------------------------------------------ registry invariants

def test_01_valid_declared_row_passes():
    assert_ok(doc(row(declared="YES")))


def test_02_wired_without_declared_fails():
    r = row(declared="YES", wired="YES")
    r["declared"] = "UNKNOWN"
    r["maturity"] = "NONE"
    assert_rejected(doc(r), "wired=YES requires declared=YES")


def test_03_exercised_without_wired_fails():
    r = row(declared="YES", wired="YES", exercised="YES")
    r["wired"] = "NOT_OBTAINED_SAFELY"
    r["limitations"] = ["route not reachable"]
    r["maturity"] = "DECLARED"
    assert_rejected(doc(r), "exercised=YES requires wired=YES")


def test_04_effective_without_exercised_fails():
    r = row(declared="YES", wired="YES", exercised="YES", effective="YES")
    r["exercised"] = "UNKNOWN"
    r["maturity"] = "WIRED"
    assert_rejected(doc(r), "effective=YES requires exercised=YES")


def test_05_consumed_without_effective_fails():
    r = row(declared="YES", wired="YES", exercised="YES", effective="YES", consumed="YES")
    r["effective"] = "UNKNOWN"
    r["maturity"] = "EXERCISED"
    assert_rejected(doc(r), "consumed=YES requires effective=YES")


def test_06_consumed_without_exact_consumer_evidence_fails():
    r = row(declared="YES", wired="YES", exercised="YES", effective="YES", consumed="YES")
    r["consumer"]["result_use"] = ""
    assert_rejected(doc(r), "consumer.result_use")
    r2 = row(declared="YES", wired="YES", exercised="YES", effective="YES", consumed="YES")
    r2["consumer"] = None
    assert_rejected(doc(r2), "consumed=YES requires a consumer")


def test_07_yes_without_evidence_reference_fails():
    r = row(declared="YES", wired="YES")
    r["evidence_refs"] = [e for e in r["evidence_refs"] if e["level"] != "wired"]
    assert_rejected(doc(r), "wired=YES has no current evidence")


def test_08_unknown_is_accepted():
    assert_ok(doc(row()))  # every level UNKNOWN, maturity NONE


def test_09_not_obtained_safely_is_accepted_with_a_reason():
    r = row(declared="YES", wired="YES")
    r["exercised"] = "NOT_OBTAINED_SAFELY"
    r["limitations"] = ["witness would require a fabricated project context"]
    assert_ok(doc(r))


def test_09b_not_obtained_safely_without_a_reason_fails():
    r = row(declared="YES", wired="YES")
    r["exercised"] = "NOT_OBTAINED_SAFELY"
    assert_rejected(doc(r), "NOT_OBTAINED_SAFELY requires a limitation")


def test_10_duplicate_capability_id_fails():
    assert_rejected(doc(row("drilling", declared="YES"), row("drilling", declared="YES")),
                    "duplicate capability_id")


def test_11_invalid_maturity_value_fails():
    r = row(declared="YES")
    r["maturity"] = "MOSTLY_WORKS"
    assert_rejected(doc(r), "maturity")


def test_11b_maturity_must_equal_the_highest_proven_level():
    over = row(declared="YES")
    over["maturity"] = "WIRED"
    assert_rejected(doc(over), "maturity WIRED does not match")
    under = row(declared="YES", wired="YES")
    under["maturity"] = "DECLARED"
    assert_rejected(doc(under), "maturity DECLARED does not match")


def test_12_non_manufacturing_surface_cannot_satisfy_manufacturing_coverage():
    r = row("feeds-speeds", surface="advisory", declared="YES")
    r["g2_bucket"] = "G2-READY"
    assert_rejected(doc(r), "non-manufacturing surface")
    m = row("adaptive", declared="YES")
    m["g2_bucket"] = "NOT-MANUFACTURING"
    assert_rejected(doc(m), "manufacturing capability cannot be NOT-MANUFACTURING")


# ------------------------------------------------------------ evidence semantics

def _consumed_row(kind, synthetic=False):
    r = row(declared="YES", wired="YES", exercised="YES", effective="YES", consumed="YES")
    r["evidence_refs"] = [e for e in r["evidence_refs"] if e["level"] != "consumed"]
    r["evidence_refs"].append(ev("consumed", kind, synthetic=synthetic))
    return r


def test_13_frontend_source_string_alone_does_not_prove_consumed():
    assert_rejected(doc(_consumed_row("client_reference")), "consumed=YES requires consumer_chain")


def test_14_unit_test_alone_does_not_prove_consumed():
    assert_rejected(doc(_consumed_row("test")), "consumed=YES requires consumer_chain")


def test_15_runtime_call_alone_proves_at_most_effective():
    assert_rejected(doc(_consumed_row("runtime")), "consumed=YES requires consumer_chain")
    # ...while the same runtime evidence is sufficient for EFFECTIVE.
    assert_ok(doc(row(declared="YES", wired="YES", exercised="YES", effective="YES")))


def test_15b_synthetic_probe_can_never_prove_consumed():
    assert_rejected(doc(_consumed_row("consumer_chain", synthetic=True)), "SYNTHETIC_PROBE")


def test_16_workflow_to_route_to_artifact_chain_may_prove_consumed():
    assert_ok(doc(_consumed_row("consumer_chain")))


def test_17_historical_evidence_cannot_satisfy_current_evidence():
    r = row(declared="YES", wired="YES", exercised="YES")
    for e in r["evidence_refs"]:
        if e["level"] == "exercised":
            e["temporal"] = "historical"
    assert_rejected(doc(r), "exercised=YES has no current evidence")


def test_17b_historical_evidence_is_accepted_when_the_row_says_so():
    r = row(declared="YES", wired="YES", exercised="YES")
    for e in r["evidence_refs"]:
        e["temporal"] = "historical"
    r["classification_basis"] = "HISTORICAL"
    assert_ok(doc(r))


# ------------------------------------------------------------ implied rules

def test_no_requires_evidence_because_absence_is_not_no():
    r = row(declared="YES", wired="YES", exercised="YES")
    r["effective"] = "NO"
    assert_rejected(doc(r), "effective=NO has no current evidence")
    r["evidence_refs"].append(ev("effective", "runtime", synthetic=True))
    assert_ok(doc(r))


def test_order_identity_must_be_exact():
    d = doc(row(declared="YES"))
    d["order_id"] = "MANUFACTURING-SPINE-001"
    assert_rejected(d, "order_id")


def test_unknown_evidence_kind_fails():
    r = row(declared="YES")
    r["evidence_refs"][0]["kind"] = "vibes"
    assert_rejected(doc(r), "unknown evidence kind")


def test_capability_ids_must_come_from_the_identity_registry(tmp_path):
    identity = tmp_path / "registry.json"
    identity.write_text(json.dumps({"capabilities": [{"capability_id": "profiling"}]}), encoding="utf-8")
    assert_ok(doc(row("profiling", declared="YES")), identity_registry=str(identity))
    assert_rejected(doc(row("profile-milling", declared="YES")),
                    "not in the identity registry", identity_registry=str(identity))


def test_validator_does_not_mutate_its_input():
    d = doc(row(declared="YES", wired="YES"))
    before = copy.deepcopy(d)
    validate(d)
    assert d == before


def test_cli_exit_codes(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(doc(row(declared="YES"))), encoding="utf-8")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(doc(row("a", declared="YES"), row("a", declared="YES"))), encoding="utf-8")
    cmd = [sys.executable, "-m", "tools.manufacturing_spine.validate_current_state"]
    assert subprocess.run(cmd + [str(good)], cwd=_REPO_ROOT).returncode == 0
    assert subprocess.run(cmd + [str(bad)], cwd=_REPO_ROOT, capture_output=True).returncode == 1
