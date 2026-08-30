"""Deterministic classification/counting tests for AGENT-PROGRAM-002A.

These tests cover ledger contract rules T01–T12. They do not invoke Grounding
Agent, do not recommend remediation, and do not create Agent 002.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from tools.agent_program.analyze_incidents import (
    FORBIDDEN_FIELDS,
    SCHEMA_VERSION,
    agent_002_necessity_inputs,
    count_recurrence,
    is_established_no,
    is_established_yes,
    load_incidents,
    recommendation_requires_authority_contract,
    recurrence_eligible,
    render_summary,
    uncovered_recurring_families,
    validate_incident_schema,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = (
    REPO_ROOT / "docs" / "governance" / "agents" / "agent_program_incidents_002a.json"
)
UTILITY_DIR = REPO_ROOT / "tools" / "agent_program"
CONTRACT_PATH = (
    REPO_ROOT / "docs" / "governance" / "agents" / "AGENT_002_AUTHORITY_CONTRACT_DRAFT.md"
)


def _ledger() -> dict:
    return load_incidents(LEDGER_PATH)


def test_t01_ledger_parses_with_expected_schema_version() -> None:
    data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION
    assert validate_incident_schema(data) == []


def test_t02_incident_ids_are_unique() -> None:
    data = _ledger()
    ids = [incident["incident_id"] for incident in data["incidents"]]
    assert ids
    assert len(ids) == len(set(ids))
    duplicate = copy.deepcopy(data)
    duplicate["incidents"].append(copy.deepcopy(duplicate["incidents"][0]))
    errors = validate_incident_schema(duplicate)
    assert any("duplicate incident_id" in error for error in errors)


def test_t03_evidence_required_for_recurrence() -> None:
    data = _ledger()
    for incident in data["incidents"]:
        if incident["independent_incident"]:
            assert incident["evidence_refs"], incident["incident_id"]
    bare = {
        "incident_id": "INC-NO-EVIDENCE",
        "failure_family": "stale_repository_reference",
        "independent_incident": True,
        "underlying_incident_id": "no-evidence",
        "evidence_refs": [],
    }
    assert recurrence_eligible(bare) is False
    assert count_recurrence([bare]) == {}


def test_t04_recurrence_is_independent() -> None:
    first = {
        "failure_family": "stale_repository_reference",
        "independent_incident": True,
        "underlying_incident_id": "same-event",
        "evidence_refs": [
            {
                "repository": "HanzoRazer/luthiers-toolbox",
                "locator": "ref-a",
            }
        ],
    }
    second = {
        **first,
        "evidence_refs": [
            {
                "repository": "HanzoRazer/luthiers-toolbox",
                "locator": "ref-b",
            }
        ],
    }
    assert count_recurrence([first, second]) == {"stale_repository_reference": 1}


def test_t05_grounding_coverage_cannot_alone_justify_agent_002() -> None:
    members = []
    for index in range(2):
        members.append(
            {
                "failure_family": "stale_repository_reference",
                "independent_incident": True,
                "underlying_incident_id": f"g-{index}",
                "grounding_would_detect": "YES",
                "deterministic_check_sufficient": "NO",
                "evidence_refs": [
                    {
                        "repository": "HanzoRazer/luthiers-toolbox",
                        "locator": f"g-{index}",
                    }
                ],
            }
        )
    assert count_recurrence(members)["stale_repository_reference"] == 2
    assert uncovered_recurring_families(members) == []
    assert agent_002_necessity_inputs(members)["necessity_test_can_pass"] is False


def test_t06_deterministic_alternative_respected() -> None:
    members = []
    for index in range(2):
        members.append(
            {
                "failure_family": "stale_repository_reference",
                "independent_incident": True,
                "underlying_incident_id": f"d-{index}",
                "grounding_would_detect": "PARTIAL",
                "deterministic_check_sufficient": "YES",
                "evidence_refs": [
                    {
                        "repository": "HanzoRazer/luthiers-toolbox",
                        "locator": f"d-{index}",
                    }
                ],
            }
        )
    assert uncovered_recurring_families(members) == []
    assert agent_002_necessity_inputs(members)["necessity_test_can_pass"] is False


def test_t07_unknown_does_not_become_no() -> None:
    assert is_established_no("UNKNOWN") is False
    assert is_established_yes("UNKNOWN") is False
    assert is_established_no("NO") is True
    assert is_established_yes("YES") is True
    mixed = [
        {
            "failure_family": "inherited_claim_epistemic_drift",
            "independent_incident": True,
            "underlying_incident_id": "u-1",
            "grounding_would_detect": "NO",
            "deterministic_check_sufficient": "UNKNOWN",
            "evidence_refs": [
                {"repository": "HanzoRazer/luthiers-toolbox", "locator": "u-1"}
            ],
        },
        {
            "failure_family": "inherited_claim_epistemic_drift",
            "independent_incident": True,
            "underlying_incident_id": "u-2",
            "grounding_would_detect": "NO",
            "deterministic_check_sufficient": "UNKNOWN",
            "evidence_refs": [
                {"repository": "HanzoRazer/luthiers-toolbox", "locator": "u-2"}
            ],
        },
    ]
    # UNKNOWN coverage is not treated as a completed deterministic alternative.
    assert uncovered_recurring_families(mixed) == ["inherited_claim_epistemic_drift"]


def test_t08_cross_repo_provenance_preserved() -> None:
    data = _ledger()
    for incident in data["incidents"]:
        assert incident["repository"]
        for ref in incident["evidence_refs"]:
            assert ref["repository"]
    broken = copy.deepcopy(data)
    broken["incidents"][0]["evidence_refs"][0]["repository"] = ""
    errors = validate_incident_schema(broken)
    assert any("repository identity" in error for error in errors)


def test_t09_no_remediation_fields() -> None:
    data = _ledger()
    dumped = json.dumps(data)
    for field in FORBIDDEN_FIELDS:
        assert field not in data
        assert f'"{field}"' not in dumped
        for incident in data["incidents"]:
            assert field not in incident
    tainted = copy.deepcopy(data)
    tainted["incidents"][0]["fix"] = "do not add this"
    errors = validate_incident_schema(tainted)
    assert any("forbidden remediation field" in error for error in errors)


def test_t10_conditional_authority_document() -> None:
    data = _ledger()
    decision = data["terminal_decision"]
    assert decision in {"NO_AGENT_002", "INSUFFICIENT_EVIDENCE"}
    assert recommendation_requires_authority_contract(decision) is False
    assert CONTRACT_PATH.exists() is False
    assert recommendation_requires_authority_contract("AGENT_002_JUSTIFIED") is True


def test_t11_authority_separation_if_contract_exists() -> None:
    if not CONTRACT_PATH.exists():
        pytest.skip("no Agent 002 draft; T11 applies only when that file exists")
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    assert "cannot mutate repository state" in text.lower() or (
        "Must not" in text and "mutat" in text.lower()
    )


def test_t12_no_orchestration_in_new_source() -> None:
    forbidden_names = {
        "dispatch_agent",
        "invoke_agent",
        "orchestrate",
        "assign_work",
        "run_grounding",
        "ground",
    }
    for path in UTILITY_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                assert node.name not in forbidden_names, path
            if isinstance(node, ast.ImportFrom):
                assert node.module != "tools.grounding_agent"
                assert not (node.module or "").startswith("tools.grounding_agent.")
        text = path.read_text(encoding="utf-8")
        assert "subprocess" not in text
        assert "gh pr" not in text
        assert "git commit" not in text


def test_live_ledger_does_not_satisfy_agent_002_necessity() -> None:
    data = _ledger()
    inputs = agent_002_necessity_inputs(data["incidents"])
    assert inputs["necessity_test_can_pass"] is False
    assert inputs["uncovered_recurring_families"] == []
    summary = render_summary(data)
    assert "INSUFFICIENT_EVIDENCE" in summary
    assert "authority_contract_required: false" in summary


def test_stale_family_in_live_ledger_is_recurrent_but_covered() -> None:
    data = _ledger()
    counts = count_recurrence(data["incidents"])
    assert counts.get("stale_repository_reference", 0) >= 2
    assert "stale_repository_reference" not in uncovered_recurring_families(
        data["incidents"]
    )


# ---------------------------------------------------------------------------
# Coverage-policy pins (review follow-up, PR #340)
#
# uncovered_recurring_families() encodes a policy choice, not just data
# handling. These pin the choice so it cannot drift silently into the more
# permissive per-member rule during a later refactor.
# ---------------------------------------------------------------------------


def _member(index: int, grounding: str, deterministic: str) -> dict:
    """A minimal recurrence-eligible incident in a single shared family."""
    return {
        "incident_id": f"PIN-{index}",
        "failure_family": "pinned_family",
        "independent_incident": True,
        "evidence_refs": [f"ref-{index}"],
        "underlying_incident_id": f"underlying-{index}",
        "grounding_would_detect": grounding,
        "deterministic_check_sufficient": deterministic,
    }


def test_mixed_axis_coverage_is_not_treated_as_covered() -> None:
    """Two members covered by *different* controls is UNCOVERED, by policy.

    The per-member alternative -- "covered when each member is covered by at
    least one control" -- would exclude this family. Per-axis unanimity keeps
    it, because neither control handles the family on its own.
    """
    members = [_member(1, "YES", "NO"), _member(2, "NO", "YES")]
    assert uncovered_recurring_families(members) == ["pinned_family"]


def test_per_axis_unanimity_covers_the_family() -> None:
    """One control covering every member does exclude the family."""
    assert uncovered_recurring_families(
        [_member(1, "YES", "NO"), _member(2, "YES", "NO")]
    ) == []
    assert uncovered_recurring_families(
        [_member(1, "NO", "YES"), _member(2, "NO", "YES")]
    ) == []


@pytest.mark.parametrize("soft_value", ["UNKNOWN", "PARTIAL"])
def test_soft_values_never_count_as_coverage(soft_value: str) -> None:
    """UNKNOWN and PARTIAL are not YES, so they cannot cover a family."""
    members = [_member(1, "YES", "NO"), _member(2, soft_value, "NO")]
    assert uncovered_recurring_families(members) == ["pinned_family"]


def test_necessity_inputs_are_internally_consistent() -> None:
    """necessity_test_can_pass must agree with the list it is derived from.

    Regression guard for the review finding that the two were computed by
    separate calls and could disagree if the function ever stopped being pure.
    """
    for members in (
        [_member(1, "NO", "NO"), _member(2, "NO", "NO")],
        [_member(1, "YES", "NO"), _member(2, "YES", "NO")],
    ):
        result = agent_002_necessity_inputs(members)
        assert result["necessity_test_can_pass"] is bool(
            result["uncovered_recurring_families"]
        )


def test_missing_control_field_does_not_read_as_coverage() -> None:
    """An absent field must not be coerced into a value that reads as non-YES-but-present.

    _all_established_yes previously str()-coerced, turning a missing field into
    the string "None". Behaviourally safe, but it absorbed a ledger defect that
    validate_incident_schema exists to surface.
    """
    broken = _member(1, "YES", "NO")
    del broken["grounding_would_detect"]
    assert uncovered_recurring_families([broken, _member(2, "YES", "NO")]) == [
        "pinned_family"
    ]
