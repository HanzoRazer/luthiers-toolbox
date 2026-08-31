"""Contract tests for the AGENT-PROGRAM-003 deferred-issue queue.

Covers the queue-integrity and readiness rules DI-001..DI-015. DI-016 and
DI-017 are the Grounding and Agent Program regression suites, and DI-018 is the
governance / CBSP21 gate; all three run outside this module, so they are named
here only to say where they live.

Two kinds of test live here, deliberately separated:

* **Contract tests** mutate a synthetic item from :func:`valid_item` and assert
  the validator's response. They never read the live queue, so a legitimate
  edit to the queue cannot turn a contract test red, and a contract test can
  never quietly stop exercising its rule because the live data moved.
* **Live-queue tests** assert invariants that must hold for *any* valid queue.
  They deliberately do not assume the queue contains an item in a particular
  state, or any particular spread of states.

They do not invoke Grounding Agent, do not recommend remediation, and do not
create any agent.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
from typing import Any, Dict

import pytest

from tools.agent_program.validate_deferred_issues import (
    ASSIGNABLE_STATES,
    CENSUS_STATUS,
    EVIDENCE_STATUS,
    FORBIDDEN_FIELDS,
    REQUIRES_RECURRENCE_FIELD,
    SCHEMA_VERSION,
    SOLUTION_CLASSES,
    STATES,
    DeferredQueueError,
    derive_evidence_status,
    gates_require_recurrence,
    has_durable_evidence,
    is_lead_only,
    list_blocked,
    list_lead_only,
    list_post_census,
    list_ready_for_decision,
    load_queue,
    readiness_failures,
    readiness_gates_satisfied,
    recurrence_is_established,
    summarize_queue,
    validate_issue,
    validate_queue,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = (
    REPO_ROOT / "docs" / "governance" / "agents" / "agent_program_deferred_issues.json"
)
UTILITY_DIR = REPO_ROOT / "tools" / "agent_program"
CENSUS_PATH = (
    REPO_ROOT / "docs" / "governance" / "agents" / "agent_program_incidents_002a.json"
)

#: Retirement states. Reaching one is not promotion toward authorization, so
#: they are permitted alongside the promotion ladder in ASSIGNABLE_STATES.
RETIREMENT_STATES = frozenset({"SUPERSEDED_BY_CONTROL", "CLOSED"})

DURABLE_REF = {
    "kind": "committed_doc",
    "evidence_class": "COMMITTED_DOC",
    "repository": "HanzoRazer/luthiers-toolbox",
    "locator": "docs/example.md:1",
    "note": "synthetic",
}

LEAD_REF = {
    "kind": "lead",
    "evidence_class": "LEAD_ONLY",
    "repository": "HanzoRazer/luthiers-toolbox",
    "locator": "a report with no recoverable source",
    "note": "synthetic",
}


def valid_item(**overrides: Any) -> Dict[str, Any]:
    """A minimal item that satisfies every contract rule, including readiness.

    Contract tests start here and break exactly one thing, so each assertion
    isolates the rule under test.
    """
    item: Dict[str, Any] = {
        "id": "AP-DI-900",
        "title": "Synthetic contract fixture",
        "state": "READY_FOR_DECISION",
        "failure_family": "synthetic_family",
        "evidence_status": "DURABLE",
        "census_status": "IN_CENSUS",
        "gates_require_recurrence": True,
        "source_incidents": ["INC-002A-F1-001", "INC-002A-F1-002"],
        "independent_incident_count": 2,
        "summary": "A synthetic item used only by the contract tests.",
        "evidence_recovery": "ATTEMPTED",
        "evidence_recovery_result": "FOUND",
        "evidence_classes": ["COMMITTED_DOC"],
        "evidence_refs": [copy.deepcopy(DURABLE_REF)],
        "current_controls": ["a control"],
        "control_gap": "a stated gap",
        "solution_class": "DETERMINISTIC_RULE",
        "agent_required": "NO",
        "agent_required_basis": "a deterministic rule suffices",
        "open_questions": [],
        "deployment_gates": ["Recurrence established: two independent census incidents"],
        "blocked_by": [],
        "related_items": [],
        "last_reviewed": "2026-08-31",
        "implementation_authorized": False,
    }
    item.update(overrides)
    return item


def _queue() -> dict:
    return load_queue(QUEUE_PATH)


# ==========================================================================
# Contract tests — synthetic input only
# ==========================================================================


def test_the_fixture_itself_is_valid_and_ready() -> None:
    """Guards every test below: if this breaks, the others prove nothing."""
    item = valid_item()
    assert validate_issue(item) == []
    assert readiness_failures(item) == []
    assert readiness_gates_satisfied(item) is True


# -------------------------------------------------------------------------
# DI-001 / DI-002 — parses, unique ids
# -------------------------------------------------------------------------


def test_di001_queue_parses_with_expected_schema_version() -> None:
    data = _queue()
    assert data["schema_version"] == SCHEMA_VERSION
    assert isinstance(data["items"], list)
    assert validate_queue(data) == []


def test_di002_duplicate_ids_fail() -> None:
    data = {
        "schema_version": SCHEMA_VERSION,
        "order": "AGENT-PROGRAM-003",
        "census_authority": "x.json",
        "items": [valid_item(), valid_item()],
    }
    assert any("duplicate id" in e for e in validate_queue(data))


# -------------------------------------------------------------------------
# DI-003 — valid states only
# -------------------------------------------------------------------------


def test_di003_arbitrary_state_is_rejected() -> None:
    errors = validate_issue(valid_item(state="ALMOST_READY"))
    assert any("is not a permitted state" in e for e in errors)


def test_di003_owner_authorized_is_not_a_state() -> None:
    assert "OWNER_AUTHORIZED" not in STATES
    assert validate_issue(valid_item(state="OWNER_AUTHORIZED"))


# -------------------------------------------------------------------------
# DI-004 — implementation authorization locked
# -------------------------------------------------------------------------


def test_di004_authorized_item_fails_validation() -> None:
    errors = validate_issue(valid_item(implementation_authorized=True))
    assert any("implementation_authorized must be false" in e for e in errors)


def test_di004_authorization_is_never_a_readiness_outcome() -> None:
    failures = readiness_failures(valid_item(implementation_authorized=True))
    assert any("never implies authorization" in f for f in failures)


# -------------------------------------------------------------------------
# DI-005 / DI-011 — evidence required above DISCOVERED; leads never suffice
# -------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["EVIDENCED", "INVESTIGATED", "READY_FOR_DECISION"])
def test_di005_states_above_discovered_require_durable_evidence(state: str) -> None:
    item = valid_item(state=state, evidence_status="NONE", evidence_refs=[], evidence_classes=[])
    assert any("requires at least one durable" in e for e in validate_issue(item))


def test_di005_lead_only_evidence_does_not_satisfy_the_requirement() -> None:
    item = valid_item(
        state="EVIDENCED", evidence_status="LEAD_ONLY",
        evidence_refs=[copy.deepcopy(LEAD_REF)], evidence_classes=["LEAD_ONLY"],
    )
    assert has_durable_evidence(item) is False
    assert any("requires at least one durable" in e for e in validate_issue(item))


def test_di005_discovered_may_stand_on_lead_only_evidence() -> None:
    item = valid_item(
        state="DISCOVERED", evidence_status="LEAD_ONLY",
        evidence_refs=[copy.deepcopy(LEAD_REF)], evidence_classes=["LEAD_ONLY"],
        gates_require_recurrence=False, deployment_gates=["a durable incident"],
    )
    assert validate_issue(item) == []


def test_di011_lead_only_item_cannot_become_ready() -> None:
    item = valid_item(
        evidence_status="LEAD_ONLY", evidence_refs=[copy.deepcopy(LEAD_REF)],
        evidence_classes=["LEAD_ONLY"],
    )
    assert is_lead_only(item) is True
    assert any("not DURABLE" in f for f in readiness_failures(item))


# -------------------------------------------------------------------------
# DI-006 / DI-007 — recurrence integrity
# -------------------------------------------------------------------------


def test_di006_two_references_to_one_event_count_once() -> None:
    item = valid_item(
        source_incidents=["INC-002A-F1-001", "INC-002A-F1-001"],
        independent_incident_count=2,
    )
    assert recurrence_is_established(item) is False
    assert any("exceeds 1 unique source_incidents" in e for e in validate_issue(item))


def test_di006_recurrence_needs_two_distinct_incidents() -> None:
    item = valid_item(source_incidents=["INC-002A-F1-001"], independent_incident_count=1)
    assert recurrence_is_established(item) is False


def test_di007_readiness_fails_when_a_declared_recurrence_gate_is_unmet() -> None:
    item = valid_item(
        gates_require_recurrence=True,
        source_incidents=["INC-002A-F1-001"],
        independent_incident_count=1,
    )
    failures = [f for f in readiness_failures(item) if "gates_require_recurrence" in f]
    assert failures
    assert any("only 1 unique census incident" in f for f in failures)


@pytest.mark.parametrize(
    "mutation, expected",
    [
        ({"census_status": "POST_CENSUS"}, "not census-admitted"),
        (
            {"source_incidents": ["INC-002A-F1-001"], "independent_incident_count": 1},
            "only 1 unique census incident",
        ),
        ({"independent_incident_count": 1}, "does not cover the 2 unique"),
    ],
)
def test_recurrence_failure_names_the_actual_cause(mutation, expected) -> None:
    """Three different causes must not collapse into one generic message."""
    failures = [
        f for f in readiness_failures(valid_item(**mutation))
        if "gates_require_recurrence" in f
    ]
    assert failures, mutation
    assert any(expected in f for f in failures), failures


def test_recurrence_bar_is_declared_not_inferred_from_gate_prose() -> None:
    """Prose mentioning recurrence must not silently impose the bar, and prose
    omitting the word must not silently lift a bar that was intended."""
    lenient = valid_item(
        gates_require_recurrence=False,
        deployment_gates=["No recurrence is required for this item"],
        source_incidents=["INC-002A-F1-001"],
        independent_incident_count=1,
    )
    assert gates_require_recurrence(lenient) is False
    assert readiness_failures(lenient) == []

    strict = valid_item(
        gates_require_recurrence=True,
        deployment_gates=["Two separate durably evidenced events"],
        source_incidents=["INC-002A-F1-001"],
        independent_incident_count=1,
    )
    assert gates_require_recurrence(strict) is True
    assert readiness_failures(strict)


def test_recurrence_bar_must_be_declared_explicitly() -> None:
    item = valid_item()
    del item[REQUIRES_RECURRENCE_FIELD]
    assert any("must be declared explicitly" in e for e in validate_issue(item))


# -------------------------------------------------------------------------
# Readiness reporting — names every failing gate
# -------------------------------------------------------------------------


def test_readiness_requires_census_membership_not_merely_durable_evidence() -> None:
    item = valid_item(census_status="POST_CENSUS")
    assert derive_evidence_status(item) == "DURABLE"
    assert any("not IN_CENSUS" in f for f in readiness_failures(item))


def test_post_census_items_cannot_establish_recurrence() -> None:
    assert recurrence_is_established(valid_item()) is True
    assert recurrence_is_established(valid_item(census_status="POST_CENSUS")) is False


def test_readiness_requires_a_stated_control_gap() -> None:
    assert any("control_gap is empty" in f for f in readiness_failures(valid_item(control_gap="   ")))


def test_readiness_reports_every_failing_gate_not_just_the_first() -> None:
    """A maintainer editing by hand should see the whole picture in one run."""
    item = valid_item(
        census_status="POST_CENSUS",
        control_gap="",
        evidence_status="LEAD_ONLY",
        evidence_refs=[copy.deepcopy(LEAD_REF)],
        evidence_classes=["LEAD_ONLY"],
    )
    failures = readiness_failures(item)
    assert len(failures) >= 3
    assert any("evidence_status" in f for f in failures)
    assert any("census_status" in f for f in failures)
    assert any("control_gap" in f for f in failures)


def test_validation_error_names_the_failing_readiness_gate() -> None:
    errors = validate_issue(valid_item(census_status="POST_CENSUS"))
    readiness_errors = [e for e in errors if "READY_FOR_DECISION but" in e]
    assert readiness_errors
    assert any("not IN_CENSUS" in e for e in readiness_errors)
    # the bare, unhelpful form must not reappear
    assert not any(e.endswith("the readiness gates are not satisfied") for e in errors)


# -------------------------------------------------------------------------
# DI-008 / DI-009 / DI-015 — bounded vocabularies, cheapest control first
# -------------------------------------------------------------------------


def test_di008_agent_required_vocabulary_is_bounded() -> None:
    assert any("agent_required=" in e for e in validate_issue(valid_item(agent_required="PROBABLY")))


def test_di008_agent_required_yes_needs_documented_basis() -> None:
    item = valid_item(agent_required="YES", agent_required_basis="")
    assert any("deterministic-control analysis" in e for e in validate_issue(item))


def test_di009_solution_class_is_bounded() -> None:
    assert any("solution_class=" in e for e in validate_issue(valid_item(solution_class="A_ROBOT")))


def test_di015_possible_agent_requires_an_explicit_unresolved_reason() -> None:
    item = valid_item(solution_class="POSSIBLE_AGENT", open_questions=[])
    assert any("explicit unresolved reason" in e for e in validate_issue(item))


def test_evidence_status_vocabulary_is_bounded() -> None:
    assert any("evidence_status=" in e for e in validate_issue(valid_item(evidence_status="OKAY")))


def test_declared_evidence_status_must_match_the_refs() -> None:
    assert any("contradicts its" in e for e in validate_issue(valid_item(evidence_status="LEAD_ONLY")))


# -------------------------------------------------------------------------
# DI-010 / DI-012 / DI-013 — provenance, retirement, no payload
# -------------------------------------------------------------------------


def test_di010_evidence_ref_without_a_repository_fails() -> None:
    ref = copy.deepcopy(DURABLE_REF)
    del ref["repository"]
    assert any("source repository" in e for e in validate_issue(valid_item(evidence_refs=[ref])))


def test_di012_closed_and_superseded_remain_valid_states() -> None:
    assert RETIREMENT_STATES.issubset(STATES)


def test_di012_supersession_requires_a_deployed_control() -> None:
    item = valid_item(state="SUPERSEDED_BY_CONTROL", control_deployed="NO")
    assert any("requires control_deployed=YES" in e for e in validate_issue(item))
    ok = valid_item(state="SUPERSEDED_BY_CONTROL", control_deployed="YES")
    assert validate_issue(ok) == []


def test_di012_blocked_item_names_its_blocker() -> None:
    item = valid_item(state="BLOCKED", blocked_by=[])
    assert any("BLOCKED requires a non-empty blocked_by" in e for e in validate_issue(item))


@pytest.mark.parametrize("field", sorted(FORBIDDEN_FIELDS))
def test_di013_remediation_payload_fields_are_rejected(field: str) -> None:
    item = valid_item()
    item[field] = "anything"
    assert any(f"forbidden remediation field {field!r}" in e for e in validate_issue(item))


# -------------------------------------------------------------------------
# DI-014 — no orchestration, no write path
# -------------------------------------------------------------------------


def test_di014_no_orchestration_or_action_in_the_validator() -> None:
    forbidden_names = {
        "dispatch_agent", "invoke_agent", "orchestrate", "assign_work",
        "run_grounding", "ground", "authorize", "authorize_implementation",
    }
    path = UTILITY_DIR / "validate_deferred_issues.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            assert node.name not in forbidden_names, node.name
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("tools.grounding_agent")
    text = path.read_text(encoding="utf-8")
    for banned in ("urllib", "requests", "socket"):
        assert banned not in text


def test_di014_validator_never_writes() -> None:
    path = UTILITY_DIR / "validate_deferred_issues.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
            modes = [
                a.value for a in node.args[1:]
                if isinstance(a, ast.Constant) and isinstance(a.value, str)
            ]
            modes += [
                kw.value.value for kw in node.keywords
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant)
            ]
            for mode in modes:
                assert mode == "r", f"non-read open mode {mode!r}"


def test_invalid_queue_raises_rather_than_summarizing_partially() -> None:
    data = _queue()
    data["items"][0]["implementation_authorized"] = True
    with pytest.raises(DeferredQueueError):
        summarize_queue(data)


# ==========================================================================
# Live-queue invariants — shape-independent
# ==========================================================================


def test_live_queue_is_valid() -> None:
    assert validate_queue(_queue()) == []


def test_live_ids_are_unique_and_namespaced() -> None:
    ids = [i["id"] for i in _queue()["items"]]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("AP-DI-") for i in ids)


def test_live_states_are_promotion_ladder_or_witnessed_retirement() -> None:
    permitted = ASSIGNABLE_STATES | RETIREMENT_STATES
    for item in _queue()["items"]:
        assert item["state"] in permitted, item["id"]
        if item["state"] in RETIREMENT_STATES:
            assert item.get("control_deployed") == "YES", (
                f"{item['id']} retired without a deployed control"
            )


def test_no_live_item_is_authorized() -> None:
    for item in _queue()["items"]:
        assert item["implementation_authorized"] is False, item["id"]


def test_live_vocabularies_are_bounded() -> None:
    for item in _queue()["items"]:
        assert item["evidence_status"] in EVIDENCE_STATUS, item["id"]
        assert item["census_status"] in CENSUS_STATUS, item["id"]
        assert item["solution_class"] in SOLUTION_CLASSES, item["id"]
        assert item["agent_required"] in {"NO", "UNPROVEN", "YES"}, item["id"]
        assert isinstance(item[REQUIRES_RECURRENCE_FIELD], bool), item["id"]


def test_live_declared_evidence_status_matches_refs() -> None:
    for item in _queue()["items"]:
        assert item["evidence_status"] == derive_evidence_status(item), item["id"]


def test_live_ready_items_actually_satisfy_the_gates() -> None:
    for item in _queue()["items"]:
        if item["state"] == "READY_FOR_DECISION":
            assert readiness_failures(item) == [], item["id"]


def test_live_post_census_items_are_never_ready() -> None:
    data = _queue()
    assert set(list_post_census(data)).isdisjoint(list_ready_for_decision(data))


def test_live_post_census_evidence_stays_truthfully_classified() -> None:
    """The ruling: durable post-census evidence is not relabelled LEAD_ONLY."""
    for item in _queue()["items"]:
        if item["census_status"] == "POST_CENSUS" and item["evidence_refs"]:
            assert item["evidence_status"] == derive_evidence_status(item), item["id"]


def test_di006_live_counts_never_exceed_unique_incidents() -> None:
    for item in _queue()["items"]:
        unique = {e for e in item["source_incidents"] if e}
        assert item["independent_incident_count"] <= len(unique), item["id"]


def test_di006_source_incidents_resolve_against_the_census() -> None:
    """The census is the one incident authority; ids must exist there."""
    census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    known = {incident["incident_id"] for incident in census["incidents"]}
    for item in _queue()["items"]:
        for incident_id in item["source_incidents"]:
            assert incident_id in known, f"{item['id']} cites unknown {incident_id}"


def test_di010_every_live_evidence_ref_names_its_repository() -> None:
    for item in _queue()["items"]:
        for ref in item["evidence_refs"]:
            assert ref.get("repository"), f"{item['id']}: {ref.get('locator')}"


def test_di013_live_queue_carries_no_payload() -> None:
    data = _queue()
    for field in FORBIDDEN_FIELDS:
        assert field not in data
        for item in data["items"]:
            assert field not in item, item["id"]


def test_live_every_family_records_its_evidence_recovery_attempt() -> None:
    for item in _queue()["items"]:
        assert item["evidence_recovery"] == "ATTEMPTED", item["id"]
        assert item["evidence_recovery_result"] in {"FOUND", "NOT_FOUND"}, item["id"]


def test_live_not_found_items_do_not_claim_durable_incidents() -> None:
    for item in _queue()["items"]:
        if item["evidence_recovery_result"] == "NOT_FOUND":
            assert item["independent_incident_count"] == 0, item["id"]


def test_live_related_items_resolve_within_the_queue() -> None:
    data = _queue()
    known = {i["id"] for i in data["items"]}
    for item in data["items"]:
        for related in item["related_items"]:
            assert related in known, f"{item['id']} -> {related}"


def test_live_lists_agree_with_states() -> None:
    data = _queue()
    assert list_blocked(data) == [i["id"] for i in data["items"] if i["state"] == "BLOCKED"]
    assert list_ready_for_decision(data) == [
        i["id"] for i in data["items"] if i["state"] == "READY_FOR_DECISION"
    ]
    assert set(list_lead_only(data)).issubset({i["id"] for i in data["items"]})


def test_live_summary_renders() -> None:
    assert "implementation_authority" in summarize_queue(_queue())
