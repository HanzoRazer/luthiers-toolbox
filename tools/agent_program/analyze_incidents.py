"""Deterministic, read-only incident-census helpers for AGENT-PROGRAM-002A.

Permitted: load, validate, group, count recurrence, summarize coverage, render.
Forbidden: git mutation, GitHub writes, incident mutation, agent decisions,
remediation recommendations, invoking Grounding or any other agent.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

SCHEMA_VERSION = "agent_program_incidents_002a_v1"

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "review_order",
    "terminal_decision",
    "incidents",
)

REQUIRED_INCIDENT_FIELDS = (
    "incident_id",
    "date",
    "program",
    "repository",
    "description",
    "failure_family",
    "active_lane_known",
    "live_repo_state_known",
    "claim_source_known",
    "claim_evidence_reacquired",
    "grounding_would_detect",
    "existing_ci_would_detect",
    "deterministic_check_sufficient",
    "escaped_existing_controls",
    "consequence",
    "recurrence_group",
    "evidence_refs",
    "classification_confidence",
    "independent_incident",
    "underlying_incident_id",
    "discovered_during_review",
    "epistemic_status",
)

TERNARY = frozenset({"YES", "NO", "UNKNOWN"})
PARTIAL_TERNARY = frozenset({"YES", "NO", "PARTIAL", "UNKNOWN"})
REACQUIRED = frozenset({"YES", "NO", "N/A"})
CONSEQUENCE = frozenset({"LOW", "MEDIUM", "HIGH"})
CONFIDENCE = frozenset({"HIGH", "MEDIUM", "LOW"})
EPISTEMIC = frozenset({"OBSERVED", "INFERRED", "UNRESOLVED"})
TERMINAL_DECISIONS = frozenset(
    {"AGENT_002_JUSTIFIED", "NO_AGENT_002", "INSUFFICIENT_EVIDENCE"}
)

FORBIDDEN_FIELDS = frozenset(
    {
        "fix",
        "patch",
        "implementation",
        "assigned_agent",
        "auto_remediate",
    }
)

DEFAULT_LEDGER = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "governance"
    / "agents"
    / "agent_program_incidents_002a.json"
)


class IncidentLedgerError(ValueError):
    """Raised when the incident ledger is not usable."""


def load_incidents(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the incident ledger JSON. Does not modify the file."""
    ledger_path = Path(path) if path is not None else DEFAULT_LEDGER
    with ledger_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise IncidentLedgerError("ledger root must be a JSON object")
    return data


def _field_errors(incident: Mapping[str, Any], index: int) -> List[str]:
    errors: List[str] = []
    prefix = f"incidents[{index}]"
    for field in REQUIRED_INCIDENT_FIELDS:
        if field not in incident:
            errors.append(f"{prefix} missing required field {field!r}")
    for field in FORBIDDEN_FIELDS:
        if field in incident:
            errors.append(f"{prefix} has forbidden remediation field {field!r}")
    if "incident_id" in incident and not incident["incident_id"]:
        errors.append(f"{prefix}.incident_id must be non-empty")
    if "repository" in incident and not incident["repository"]:
        errors.append(f"{prefix}.repository must identify a repository")
    enums = {
        "active_lane_known": TERNARY,
        "live_repo_state_known": TERNARY,
        "claim_source_known": TERNARY,
        "claim_evidence_reacquired": REACQUIRED,
        "grounding_would_detect": PARTIAL_TERNARY,
        "existing_ci_would_detect": PARTIAL_TERNARY,
        "deterministic_check_sufficient": TERNARY,
        "escaped_existing_controls": TERNARY,
        "consequence": CONSEQUENCE,
        "classification_confidence": CONFIDENCE,
        "epistemic_status": EPISTEMIC,
    }
    for field, allowed in enums.items():
        value = incident.get(field)
        if value is not None and value not in allowed:
            errors.append(f"{prefix}.{field}={value!r} is not one of {sorted(allowed)}")
    refs = incident.get("evidence_refs")
    if refs is not None:
        if not isinstance(refs, list):
            errors.append(f"{prefix}.evidence_refs must be an array")
        else:
            for r_index, ref in enumerate(refs):
                if not isinstance(ref, Mapping):
                    errors.append(f"{prefix}.evidence_refs[{r_index}] must be an object")
                    continue
                if not ref.get("repository"):
                    errors.append(
                        f"{prefix}.evidence_refs[{r_index}] must record repository identity"
                    )
                if not ref.get("locator"):
                    errors.append(
                        f"{prefix}.evidence_refs[{r_index}] must have a locator"
                    )
    for flag in ("independent_incident", "discovered_during_review"):
        if flag in incident and not isinstance(incident[flag], bool):
            errors.append(f"{prefix}.{flag} must be a boolean")
    return errors


def validate_incident_schema(data: Mapping[str, Any]) -> List[str]:
    """Return validation errors. An empty list means the ledger is usable."""
    errors: List[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"missing top-level field {field!r}")
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {SCHEMA_VERSION!r}; "
            f"observed {data.get('schema_version')!r}"
        )
    decision = data.get("terminal_decision")
    if decision is not None and decision not in TERMINAL_DECISIONS:
        errors.append(f"terminal_decision={decision!r} is not a permitted 002A decision")
    for field in FORBIDDEN_FIELDS:
        if field in data:
            errors.append(f"ledger has forbidden remediation field {field!r}")
    incidents = data.get("incidents")
    if incidents is None:
        return errors
    if not isinstance(incidents, list):
        errors.append("incidents must be an array")
        return errors
    seen_ids: Dict[str, int] = {}
    for index, incident in enumerate(incidents):
        if not isinstance(incident, Mapping):
            errors.append(f"incidents[{index}] must be an object")
            continue
        errors.extend(_field_errors(incident, index))
        incident_id = incident.get("incident_id")
        if isinstance(incident_id, str) and incident_id:
            if incident_id in seen_ids:
                errors.append(
                    f"duplicate incident_id {incident_id!r} "
                    f"(incidents[{seen_ids[incident_id]}] and incidents[{index}])"
                )
            else:
                seen_ids[incident_id] = index
    return errors


def is_established_no(value: str) -> bool:
    """UNKNOWN and PARTIAL are not NO. Only explicit NO is negative."""
    return value == "NO"


def is_established_yes(value: str) -> bool:
    """UNKNOWN and PARTIAL are not YES."""
    return value == "YES"


def _has_durable_evidence(incident: Mapping[str, Any]) -> bool:
    refs = incident.get("evidence_refs") or []
    return isinstance(refs, list) and len(refs) > 0


def recurrence_eligible(incident: Mapping[str, Any]) -> bool:
    """An incident counts toward recurrence only if independently evidenced."""
    return bool(
        incident.get("independent_incident") is True
        and _has_durable_evidence(incident)
        and incident.get("underlying_incident_id")
    )


def group_by_failure_family(
    incidents: Sequence[Mapping[str, Any]],
) -> Dict[str, List[Mapping[str, Any]]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for incident in incidents:
        grouped[str(incident.get("failure_family") or "unspecified")].append(incident)
    return dict(grouped)


def count_recurrence(incidents: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    """Count unique underlying incidents per family.

    Two evidence references to the same underlying_incident_id count as one.
    Incidents without durable evidence do not count.
    """
    seen: Dict[str, set] = defaultdict(set)
    for incident in incidents:
        if not recurrence_eligible(incident):
            continue
        family = str(incident.get("failure_family") or "unspecified")
        seen[family].add(str(incident["underlying_incident_id"]))
    return {family: len(ids) for family, ids in seen.items()}


def _all_established_yes(incidents: Iterable[Mapping[str, Any]], field: str) -> bool:
    values = [str(incident.get(field)) for incident in incidents]
    return bool(values) and all(is_established_yes(value) for value in values)


def uncovered_recurring_families(
    incidents: Sequence[Mapping[str, Any]],
) -> List[str]:
    """Families that could feed the Agent-002 necessity test.

    A family is excluded when every recurrence-eligible member is already
    detectable by Grounding, or every member has a sufficient deterministic
    check. UNKNOWN does not become NO, so mixed/unknown coverage keeps the
    family from being treated as fully covered.
    """
    counts = count_recurrence(incidents)
    grouped = group_by_failure_family(incidents)
    uncovered: List[str] = []
    for family, count in counts.items():
        if count < 2:
            continue
        members = [inc for inc in grouped[family] if recurrence_eligible(inc)]
        if _all_established_yes(members, "grounding_would_detect"):
            continue
        if _all_established_yes(members, "deterministic_check_sufficient"):
            continue
        uncovered.append(family)
    return sorted(uncovered)


def agent_002_necessity_inputs(incidents: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Structured inputs for the human necessity test. Not a decision."""
    return {
        "recurrence_counts": count_recurrence(incidents),
        "uncovered_recurring_families": uncovered_recurring_families(incidents),
        "necessity_test_can_pass": bool(uncovered_recurring_families(incidents)),
    }


def recommendation_requires_authority_contract(decision: str) -> bool:
    """T10: only AGENT_002_JUSTIFIED requires the draft contract file."""
    if decision not in TERMINAL_DECISIONS:
        raise IncidentLedgerError(f"unknown terminal decision {decision!r}")
    return decision == "AGENT_002_JUSTIFIED"


def summarize_control_coverage(
    incidents: Sequence[Mapping[str, Any]],
) -> Dict[str, Dict[str, int]]:
    fields = (
        "grounding_would_detect",
        "existing_ci_would_detect",
        "deterministic_check_sufficient",
        "escaped_existing_controls",
    )
    summary: Dict[str, Dict[str, int]] = {}
    for field in fields:
        counts: Dict[str, int] = defaultdict(int)
        for incident in incidents:
            counts[str(incident.get(field))] += 1
        summary[field] = dict(counts)
    return summary


def render_summary(data: Mapping[str, Any]) -> str:
    errors = validate_incident_schema(data)
    if errors:
        raise IncidentLedgerError("ledger invalid:\n" + "\n".join(errors))
    incidents = list(data["incidents"])
    lines = [
        f"schema_version: {data['schema_version']}",
        f"review_order: {data['review_order']}",
        f"terminal_decision: {data['terminal_decision']}",
        f"incidents: {len(incidents)}",
        "recurrence_counts:",
    ]
    counts = count_recurrence(incidents)
    if not counts:
        lines.append("  (none eligible)")
    for family, count in sorted(counts.items()):
        lines.append(f"  {family}: {count}")
    uncovered = uncovered_recurring_families(incidents)
    lines.append(
        "uncovered_recurring_families: "
        + (", ".join(uncovered) if uncovered else "(none)")
    )
    lines.append(
        "necessity_test_can_pass: "
        + str(bool(uncovered)).lower()
    )
    lines.append(
        "authority_contract_required: "
        + str(
            recommendation_requires_authority_contract(str(data["terminal_decision"]))
        ).lower()
    )
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only summary of the AGENT-PROGRAM-002A incident ledger."
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help="Path to agent_program_incidents_002a.json",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    data = load_incidents(args.ledger)
    print(render_summary(data), end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
