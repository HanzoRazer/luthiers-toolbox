"""Contract tests for the AGENT-PROGRAM-003 deferred-issue queue (DI-001..DI-018).

These tests cover queue integrity and readiness logic only. They do not invoke
Grounding Agent, do not recommend remediation, and do not create any agent.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from tools.agent_program.validate_deferred_issues import (
    ASSIGNABLE_STATES,
    FORBIDDEN_FIELDS,
    SCHEMA_VERSION,
    SOLUTION_CLASSES,
    STATES,
    DeferredQueueError,
    has_durable_evidence,
    is_lead_only,
    list_blocked,
    list_lead_only,
    list_pending_census,
    list_ready_for_decision,
    load_queue,
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


def _queue() -> dict:
    return load_queue(QUEUE_PATH)


def _first(state: str) -> dict:
    for item in _queue()["items"]:
        if item["state"] == state:
            return item
    raise AssertionError(f"no live item in state {state}")


# --------------------------------------------------------------------------
# DI-001 — queue parses
# --------------------------------------------------------------------------


def test_di001_queue_parses_with_expected_schema_version() -> None:
    data = _queue()
    assert data["schema_version"] == SCHEMA_VERSION
    assert isinstance(data["items"], list)
    assert validate_queue(data) == []


def test_di001_live_queue_renders_a_summary() -> None:
    assert "implementation_authority" in summarize_queue(_queue())


# --------------------------------------------------------------------------
# DI-002 — unique IDs
# --------------------------------------------------------------------------


def test_di002_duplicate_ids_fail() -> None:
    data = _queue()
    data["items"].append(copy.deepcopy(data["items"][0]))
    errors = validate_queue(data)
    assert any("duplicate id" in error for error in errors)


def test_di002_live_ids_are_unique_and_namespaced() -> None:
    ids = [item["id"] for item in _queue()["items"]]
    assert len(ids) == len(set(ids))
    assert all(item.startswith("AP-DI-") for item in ids)


# --------------------------------------------------------------------------
# DI-003 — valid states only
# --------------------------------------------------------------------------


def test_di003_arbitrary_state_is_rejected() -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["state"] = "ALMOST_READY"
    assert any("is not a permitted state" in error for error in validate_issue(item))


def test_di003_owner_authorized_is_not_a_state() -> None:
    assert "OWNER_AUTHORIZED" not in STATES
    item = copy.deepcopy(_first("DISCOVERED"))
    item["state"] = "OWNER_AUTHORIZED"
    assert validate_issue(item)


def test_di003_live_states_are_all_assignable_by_this_increment() -> None:
    for item in _queue()["items"]:
        assert item["state"] in ASSIGNABLE_STATES, item["id"]


# --------------------------------------------------------------------------
# DI-004 — implementation authorization locked
# --------------------------------------------------------------------------


def test_di004_authorized_item_fails_validation() -> None:
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["implementation_authorized"] = True
    assert any("implementation_authorized must be false" in e for e in validate_issue(item))


def test_di004_every_live_item_is_unauthorized() -> None:
    for item in _queue()["items"]:
        assert item["implementation_authorized"] is False, item["id"]


def test_di004_authorization_is_never_a_readiness_outcome() -> None:
    """READY_FOR_DECISION means reviewable, never authorized."""
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    assert readiness_gates_satisfied(item) is True
    item["implementation_authorized"] = True
    assert readiness_gates_satisfied(item) is False


# --------------------------------------------------------------------------
# DI-005 — evidence required above DISCOVERED
# --------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["EVIDENCED", "INVESTIGATED", "READY_FOR_DECISION"])
def test_di005_states_above_discovered_require_durable_evidence(state: str) -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["state"] = state
    item["evidence_refs"] = []
    item["evidence_classes"] = []
    assert any("requires at least one durable" in e for e in validate_issue(item))


def test_di005_lead_only_evidence_does_not_satisfy_the_requirement() -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["state"] = "EVIDENCED"
    item["evidence_refs"] = [
        {
            "kind": "lead",
            "evidence_class": "LEAD_ONLY",
            "repository": "HanzoRazer/luthiers-toolbox",
            "locator": "a report with no recoverable source",
        }
    ]
    assert has_durable_evidence(item) is False
    assert any("requires at least one durable" in e for e in validate_issue(item))


def test_di005_discovered_may_stand_without_durable_evidence() -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["evidence_refs"] = [
        {
            "kind": "lead",
            "evidence_class": "LEAD_ONLY",
            "repository": "HanzoRazer/luthiers-toolbox",
            "locator": "unrecovered report",
        }
    ]
    assert validate_issue(item) == []


# --------------------------------------------------------------------------
# DI-006 — recurrence integrity
# --------------------------------------------------------------------------


def test_di006_two_references_to_one_event_count_once() -> None:
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["source_incidents"] = ["INC-002A-F1-001", "INC-002A-F1-001"]
    item["independent_incident_count"] = 2
    assert recurrence_is_established(item) is False
    assert any("exceeds 1 unique source_incidents" in e for e in validate_issue(item))


def test_di006_recurrence_needs_two_distinct_incidents() -> None:
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["source_incidents"] = ["INC-002A-F1-001"]
    item["independent_incident_count"] = 1
    assert recurrence_is_established(item) is False


def test_di006_live_counts_never_exceed_unique_incidents() -> None:
    for item in _queue()["items"]:
        unique = {entry for entry in item["source_incidents"] if entry}
        assert item["independent_incident_count"] <= len(unique), item["id"]


def test_di006_source_incidents_resolve_against_the_census() -> None:
    """The census is the one incident authority; ids must exist there."""
    census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    known = {incident["incident_id"] for incident in census["incidents"]}
    for item in _queue()["items"]:
        for incident_id in item["source_incidents"]:
            assert incident_id in known, f"{item['id']} cites unknown {incident_id}"


# --------------------------------------------------------------------------
# DI-007 / DI-011 — readiness rules
# --------------------------------------------------------------------------


def test_di007_readiness_fails_when_a_recurrence_gate_is_unmet() -> None:
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["source_incidents"] = ["INC-002A-F1-001"]
    item["independent_incident_count"] = 1
    item["deployment_gates"] = ["Recurrence established: two independent census incidents"]
    assert readiness_gates_satisfied(item) is False
    assert any("readiness gates are not satisfied" in e for e in validate_issue(item))


def test_di011_lead_only_item_cannot_become_ready() -> None:
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["evidence_refs"] = [
        {
            "kind": "lead",
            "evidence_class": "LEAD_ONLY",
            "repository": "HanzoRazer/luthiers-toolbox",
            "locator": "unrecovered report",
        }
    ]
    assert is_lead_only(item) is True
    assert readiness_gates_satisfied(item) is False


def test_readiness_requires_census_ratified_evidence() -> None:
    """A finding recovered after the census closed cannot reach readiness."""
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["census_status"] = "PENDING_CENSUS_AMENDMENT"
    assert readiness_gates_satisfied(item) is False


def test_readiness_requires_a_stated_control_gap() -> None:
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["control_gap"] = "   "
    assert readiness_gates_satisfied(item) is False


def test_live_pending_census_items_are_not_ready() -> None:
    data = _queue()
    assert set(list_pending_census(data)).isdisjoint(list_ready_for_decision(data))


# --------------------------------------------------------------------------
# DI-008 — agent-required cannot be guessed
# --------------------------------------------------------------------------


def test_di008_agent_required_vocabulary_is_bounded() -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["agent_required"] = "PROBABLY"
    assert any("agent_required=" in e for e in validate_issue(item))


def test_di008_agent_required_yes_needs_documented_basis() -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["agent_required"] = "YES"
    item["agent_required_basis"] = ""
    assert any("deterministic-control analysis" in e for e in validate_issue(item))


def test_di008_live_queue_asserts_no_agent_is_required() -> None:
    for item in _queue()["items"]:
        assert item["agent_required"] in {"NO", "UNPROVEN"}, item["id"]


# --------------------------------------------------------------------------
# DI-009 / DI-015 — solution class
# --------------------------------------------------------------------------


def test_di009_solution_class_is_bounded() -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["solution_class"] = "BUILD_A_ROBOT"
    assert any("solution_class=" in e for e in validate_issue(item))


def test_di009_live_solution_classes_are_in_vocabulary() -> None:
    for item in _queue()["items"]:
        assert item["solution_class"] in SOLUTION_CLASSES, item["id"]


def test_di015_possible_agent_requires_an_explicit_unresolved_reason() -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item["solution_class"] = "POSSIBLE_AGENT"
    item["open_questions"] = []
    assert any("explicit unresolved reason" in e for e in validate_issue(item))


def test_di015_no_live_item_is_elevated_to_possible_agent() -> None:
    for item in _queue()["items"]:
        assert item["solution_class"] != "POSSIBLE_AGENT", item["id"]


# --------------------------------------------------------------------------
# DI-010 — cross-repo provenance
# --------------------------------------------------------------------------


def test_di010_evidence_ref_without_a_repository_fails() -> None:
    item = copy.deepcopy(_first("READY_FOR_DECISION"))
    item["evidence_refs"][0].pop("repository")
    assert any("source repository" in e for e in validate_issue(item))


def test_di010_every_live_evidence_ref_names_its_repository() -> None:
    for item in _queue()["items"]:
        for ref in item["evidence_refs"]:
            assert ref.get("repository"), f"{item['id']}: {ref.get('locator')}"


# --------------------------------------------------------------------------
# DI-012 — closed history retained
# --------------------------------------------------------------------------


def test_di012_closed_and_superseded_remain_valid_states() -> None:
    assert {"CLOSED", "SUPERSEDED_BY_CONTROL"}.issubset(STATES)


def test_di012_supersession_requires_a_deployed_control() -> None:
    item = copy.deepcopy(_first("BLOCKED"))
    item["state"] = "SUPERSEDED_BY_CONTROL"
    assert item["control_deployed"] == "NO"
    assert any("requires control_deployed=YES" in e for e in validate_issue(item))


def test_di012_blocked_item_names_its_blocker() -> None:
    item = copy.deepcopy(_first("BLOCKED"))
    item["blocked_by"] = []
    assert any("BLOCKED requires a non-empty blocked_by" in e for e in validate_issue(item))


# --------------------------------------------------------------------------
# DI-013 / DI-014 — no payload, no orchestration
# --------------------------------------------------------------------------


@pytest.mark.parametrize("field", sorted(FORBIDDEN_FIELDS))
def test_di013_remediation_payload_fields_are_rejected(field: str) -> None:
    item = copy.deepcopy(_first("DISCOVERED"))
    item[field] = "anything"
    assert any(f"forbidden remediation field {field!r}" in e for e in validate_issue(item))


def test_di013_live_queue_carries_no_payload() -> None:
    data = _queue()
    for field in FORBIDDEN_FIELDS:
        assert field not in data
        for item in data["items"]:
            assert field not in item, item["id"]


def test_di014_no_orchestration_or_action_in_the_validator() -> None:
    forbidden_names = {
        "dispatch_agent",
        "invoke_agent",
        "orchestrate",
        "assign_work",
        "run_grounding",
        "ground",
        "authorize",
        "authorize_implementation",
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
    """The module opens files for reading only."""
    path = UTILITY_DIR / "validate_deferred_issues.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
            modes = [
                arg.value
                for arg in node.args[1:]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            ]
            modes += [
                kw.value.value
                for kw in node.keywords
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant)
            ]
            for mode in modes:
                assert mode == "r", f"non-read open mode {mode!r}"


# --------------------------------------------------------------------------
# Queue-level invariants
# --------------------------------------------------------------------------


def test_invalid_queue_raises_rather_than_summarizing_partially() -> None:
    data = _queue()
    data["items"][0]["implementation_authorized"] = True
    with pytest.raises(DeferredQueueError):
        summarize_queue(data)


def test_related_items_resolve_within_the_queue() -> None:
    data = _queue()
    known = {item["id"] for item in data["items"]}
    for item in data["items"]:
        for related in item["related_items"]:
            assert related in known, f"{item['id']} -> {related}"


def test_every_family_records_its_evidence_recovery_attempt() -> None:
    """A NOT_FOUND pass is a recorded result, not a silent omission."""
    for item in _queue()["items"]:
        assert item["evidence_recovery"] == "ATTEMPTED", item["id"]
        assert item["evidence_recovery_result"] in {"FOUND", "NOT_FOUND"}, item["id"]


def test_not_found_items_do_not_claim_durable_incidents() -> None:
    for item in _queue()["items"]:
        if item["evidence_recovery_result"] == "NOT_FOUND":
            assert item["independent_incident_count"] == 0, item["id"]


def test_live_lists_are_consistent_with_states() -> None:
    data = _queue()
    assert list_blocked(data) == [
        item["id"] for item in data["items"] if item["state"] == "BLOCKED"
    ]
    assert list_ready_for_decision(data) == [
        item["id"] for item in data["items"] if item["state"] == "READY_FOR_DECISION"
    ]
    assert set(list_lead_only(data)).issubset({item["id"] for item in data["items"]})
