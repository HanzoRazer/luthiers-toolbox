"""Deterministic validation of the AGENT-PROGRAM-003 deferred-issue queue.

The queue is a *readiness* layer over the 002A incident census. This module
checks the properties that are easy to get subtly wrong by hand:

* an item reaching readiness on lead-only evidence;
* recurrence counted from repeated citations of one underlying event;
* an item marked superseded by a control that is not deployed;
* an item that quietly carries implementation authorization.

Four concepts are kept separate and are never collapsed into one another::

    evidence_status          how well supported is this item?
    census_status            was its incident basis part of the 002A census?
    state                    is it mature enough for an owner decision?
    implementation_authorized  has the owner authorized implementation?

Durable evidence recovered after the census closed stays classified as durable.
What it lacks is census membership, and that is what gates readiness.

It is read-only. It has no network, no Git invocation, and no write path, and
it never sets authorization. Enforced by ``tests/agent_program/``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

SCHEMA_VERSION = "agent_program_deferred_issues_v1"

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "order",
    "census_authority",
    "items",
)

REQUIRED_ITEM_FIELDS = (
    "id",
    "title",
    "state",
    "failure_family",
    "evidence_status",
    "census_status",
    "source_incidents",
    "independent_incident_count",
    "summary",
    "evidence_recovery",
    "evidence_recovery_result",
    "evidence_classes",
    "evidence_refs",
    "current_controls",
    "control_gap",
    "solution_class",
    "agent_required",
    "open_questions",
    "deployment_gates",
    "blocked_by",
    "related_items",
    "last_reviewed",
    "implementation_authorized",
)

STATES = frozenset(
    {
        "DISCOVERED",
        "EVIDENCED",
        "INVESTIGATED",
        "READY_FOR_DECISION",
        "BLOCKED",
        "SUPERSEDED_BY_CONTROL",
        "CLOSED",
    }
)

#: States this increment may assign. OWNER_AUTHORIZED is not a state at all.
ASSIGNABLE_STATES = frozenset(
    {"DISCOVERED", "EVIDENCED", "INVESTIGATED", "READY_FOR_DECISION", "BLOCKED"}
)

#: States that require durable, non-lead evidence.
EVIDENCE_REQUIRING_STATES = frozenset(
    {"EVIDENCED", "INVESTIGATED", "READY_FOR_DECISION"}
)

EVIDENCE_CLASSES = frozenset(
    {
        "RUNTIME_WITNESS",
        "GIT_STATE",
        "GITHUB_STATE",
        "COMMITTED_DOC",
        "COMMITTED_TEST",
        "CLOUD_AGENT_TRANSCRIPT",
        "OWNER_ATTESTATION",
        "INPUT_CONTRACT",
        "STATIC_CODE_INSPECTION",
        "LEAD_ONLY",
    }
)

DURABLE_EVIDENCE_CLASSES = EVIDENCE_CLASSES - {"LEAD_ONLY"}

SOLUTION_CLASSES = frozenset(
    {
        "EXISTING_CONTROL",
        "DETERMINISTIC_RULE",
        "DETERMINISTIC_UTILITY",
        "GROUNDING_EXTENSION",
        "POSSIBLE_AGENT",
        "PROCESS_ONLY",
        "UNRESOLVED",
    }
)

AGENT_REQUIRED = frozenset({"YES", "NO", "UNPROVEN"})

EVIDENCE_STATUS = frozenset({"DURABLE", "LEAD_ONLY", "NONE"})

#: Was the item's incident basis part of the canonical 002A census?
#: IN_CENSUS   - the basis is exactly what the census recorded (including "no incident")
#: POST_CENSUS - the item rests on incident evidence recovered after the census closed
CENSUS_STATUS = frozenset({"IN_CENSUS", "POST_CENSUS"})

RECOVERY = frozenset({"ATTEMPTED", "NOT_ATTEMPTED"})
RECOVERY_RESULT = frozenset({"FOUND", "NOT_FOUND"})

#: A queue tracks problems awaiting a decision. It never carries a payload.
FORBIDDEN_FIELDS = frozenset(
    {
        "patch",
        "code_change",
        "auto_execute",
        "assigned_agent",
        "merge_when",
        "deploy_now",
    }
)

#: Words that make a deployment gate an assertion about recurrence.
_RECURRENCE_MARKERS = ("recurrence", "independent incident", "independent census")

DEFAULT_QUEUE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "governance"
    / "agents"
    / "agent_program_deferred_issues.json"
)


class DeferredQueueError(ValueError):
    """The queue violates its contract."""


def load_queue(path: Optional[Path] = None) -> Dict[str, Any]:
    """Read the queue JSON. Does not validate."""
    target = Path(path) if path is not None else DEFAULT_QUEUE
    with open(target, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _durable_refs(item: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    refs = item.get("evidence_refs")
    if not isinstance(refs, list):
        return []
    return [
        ref
        for ref in refs
        if isinstance(ref, Mapping)
        and ref.get("evidence_class") in DURABLE_EVIDENCE_CLASSES
    ]


def has_durable_evidence(item: Mapping[str, Any]) -> bool:
    """True when at least one evidence reference is not ``LEAD_ONLY``."""
    return bool(_durable_refs(item))


def derive_evidence_status(item: Mapping[str, Any]) -> str:
    """How well supported is this item, judged only from its evidence refs.

    Independent of census membership and of readiness. Durable evidence stays
    durable whether or not the census has admitted it.
    """
    refs = item.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        return "NONE"
    return "DURABLE" if _durable_refs(item) else "LEAD_ONLY"


def is_lead_only(item: Mapping[str, Any]) -> bool:
    """True when every evidence reference is ``LEAD_ONLY``."""
    refs = item.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        return True
    return not has_durable_evidence(item)


def recurrence_is_established(item: Mapping[str, Any]) -> bool:
    """Recurrence needs at least two *independent* census incidents.

    Counting is by unique ``source_incidents`` id, so two references to one
    underlying event count once. Findings not yet ratified into the census
    cannot establish recurrence at all.
    """
    # Durable post-census evidence does not enter the canonical recurrence
    # calculation merely by being durable; it needs census admission first.
    if item.get("census_status") != "IN_CENSUS":
        return False
    incidents = item.get("source_incidents")
    if not isinstance(incidents, list):
        return False
    unique = {str(entry) for entry in incidents if entry}
    if len(unique) < 2:
        return False
    declared = item.get("independent_incident_count")
    if not isinstance(declared, int) or declared < len(unique):
        return False
    return True


def _gate_claims_recurrence(item: Mapping[str, Any]) -> bool:
    gates = item.get("deployment_gates")
    if not isinstance(gates, list):
        return False
    for gate in gates:
        text = str(gate).lower()
        if any(marker in text for marker in _RECURRENCE_MARKERS):
            return True
    return False


def readiness_gates_satisfied(item: Mapping[str, Any]) -> bool:
    """Whether an item may hold ``READY_FOR_DECISION``.

    Readiness means *sufficiently investigated for owner review*. It never
    means authorized to implement.
    """
    if item.get("implementation_authorized") is not False:
        return False
    # Evidence quality and census membership are separate gates. An item can
    # hold durable evidence and still not be ready, because readiness is
    # computed against the canonical census.
    if derive_evidence_status(item) != "DURABLE":
        return False
    if item.get("census_status") != "IN_CENSUS":
        return False
    if not isinstance(item.get("current_controls"), list):
        return False
    if not str(item.get("control_gap") or "").strip():
        return False
    if item.get("solution_class") not in SOLUTION_CLASSES:
        return False
    if _gate_claims_recurrence(item) and not recurrence_is_established(item):
        return False
    return True


def _item_errors(item: Mapping[str, Any], index: int) -> List[str]:
    errors: List[str] = []
    label = item.get("id") or f"items[{index}]"

    for field in REQUIRED_ITEM_FIELDS:
        if field not in item:
            errors.append(f"{label}: missing field {field!r}")

    for field in FORBIDDEN_FIELDS:
        if field in item:
            errors.append(f"{label}: forbidden remediation field {field!r}")

    state = item.get("state")
    if state not in STATES:
        errors.append(f"{label}: state={state!r} is not a permitted state")
    elif state not in ASSIGNABLE_STATES and state not in {
        "SUPERSEDED_BY_CONTROL",
        "CLOSED",
    }:
        errors.append(f"{label}: state={state!r} may not be assigned")

    declared_evidence = item.get("evidence_status")
    if declared_evidence not in EVIDENCE_STATUS:
        errors.append(f"{label}: evidence_status={declared_evidence!r} invalid")
    elif declared_evidence != derive_evidence_status(item):
        errors.append(
            f"{label}: evidence_status={declared_evidence!r} contradicts its "
            f"evidence_refs (derived {derive_evidence_status(item)!r})"
        )

    if item.get("census_status") not in CENSUS_STATUS:
        errors.append(f"{label}: census_status={item.get('census_status')!r} invalid")

    if item.get("solution_class") not in SOLUTION_CLASSES:
        errors.append(f"{label}: solution_class={item.get('solution_class')!r} invalid")

    agent_required = item.get("agent_required")
    if agent_required not in AGENT_REQUIRED:
        errors.append(f"{label}: agent_required={agent_required!r} invalid")
    elif agent_required == "YES" and not str(
        item.get("agent_required_basis") or ""
    ).strip():
        errors.append(
            f"{label}: agent_required=YES requires a documented "
            "agent_required_basis (deterministic-control analysis)"
        )

    if item.get("evidence_recovery") not in RECOVERY:
        errors.append(
            f"{label}: evidence_recovery={item.get('evidence_recovery')!r} invalid"
        )
    if item.get("evidence_recovery_result") not in RECOVERY_RESULT:
        errors.append(
            f"{label}: evidence_recovery_result="
            f"{item.get('evidence_recovery_result')!r} invalid"
        )

    classes = item.get("evidence_classes")
    if isinstance(classes, list):
        for entry in classes:
            if entry not in EVIDENCE_CLASSES:
                errors.append(f"{label}: evidence class {entry!r} is not in the vocabulary")
    else:
        errors.append(f"{label}: evidence_classes must be an array")

    refs = item.get("evidence_refs")
    if isinstance(refs, list):
        for position, ref in enumerate(refs):
            if not isinstance(ref, Mapping):
                errors.append(f"{label}: evidence_refs[{position}] must be an object")
                continue
            if ref.get("evidence_class") not in EVIDENCE_CLASSES:
                errors.append(
                    f"{label}: evidence_refs[{position}] evidence_class "
                    f"{ref.get('evidence_class')!r} is not in the vocabulary"
                )
            if not str(ref.get("locator") or "").strip():
                errors.append(f"{label}: evidence_refs[{position}] needs a locator")
            # DI-010: cross-repo evidence must name its source repository.
            if not str(ref.get("repository") or "").strip():
                errors.append(
                    f"{label}: evidence_refs[{position}] must record its source repository"
                )
    else:
        errors.append(f"{label}: evidence_refs must be an array")

    if item.get("implementation_authorized") is not False:
        errors.append(
            f"{label}: implementation_authorized must be false — this queue "
            "cannot grant implementation authority"
        )

    # DI-005 / DI-011: evidence is required above DISCOVERED, and lead-only
    # evidence never satisfies it.
    if state in EVIDENCE_REQUIRING_STATES and not has_durable_evidence(item):
        errors.append(
            f"{label}: state={state!r} requires at least one durable "
            "(non-LEAD_ONLY) evidence reference"
        )

    # DI-007 / DI-011: readiness is a gated conclusion, not a description.
    if state == "READY_FOR_DECISION" and not readiness_gates_satisfied(item):
        errors.append(
            f"{label}: READY_FOR_DECISION but the readiness gates are not satisfied"
        )

    # A control that is not deployed cannot supersede anything.
    if state == "SUPERSEDED_BY_CONTROL" and item.get("control_deployed") != "YES":
        errors.append(
            f"{label}: SUPERSEDED_BY_CONTROL requires control_deployed=YES"
        )

    if state == "BLOCKED":
        blocked_by = item.get("blocked_by")
        if not isinstance(blocked_by, list) or not blocked_by:
            errors.append(f"{label}: BLOCKED requires a non-empty blocked_by")

    # DI-015: prefer the cheapest sufficient control.
    if item.get("solution_class") == "POSSIBLE_AGENT" and not item.get("open_questions"):
        errors.append(
            f"{label}: POSSIBLE_AGENT requires an explicit unresolved reason "
            "in open_questions"
        )

    declared = item.get("independent_incident_count")
    incidents = item.get("source_incidents")
    if isinstance(declared, int) and isinstance(incidents, list):
        unique = {str(entry) for entry in incidents if entry}
        if declared > len(unique):
            errors.append(
                f"{label}: independent_incident_count={declared} exceeds "
                f"{len(unique)} unique source_incidents (DI-006: two references "
                "to one event count once)"
            )

    return errors


def validate_issue(item: Mapping[str, Any], index: int = 0) -> List[str]:
    """Return the contract errors for one item. Empty means usable."""
    return _item_errors(item, index)


def validate_queue(data: Mapping[str, Any]) -> List[str]:
    """Return every contract error in the queue. Empty means usable."""
    errors: List[str] = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"missing top-level field {field!r}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {SCHEMA_VERSION!r}; "
            f"observed {data.get('schema_version')!r}"
        )

    for field in FORBIDDEN_FIELDS:
        if field in data:
            errors.append(f"queue has forbidden remediation field {field!r}")

    items = data.get("items")
    if items is None:
        return errors
    if not isinstance(items, list):
        errors.append("items must be an array")
        return errors

    seen: Dict[str, int] = {}
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"items[{index}] must be an object")
            continue
        errors.extend(_item_errors(item, index))
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            if item_id in seen:
                errors.append(
                    f"duplicate id {item_id!r} (items[{seen[item_id]}] and items[{index}])"
                )
            else:
                seen[item_id] = index

    known = set(seen)
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            continue
        for related in item.get("related_items") or []:
            if related not in known:
                errors.append(
                    f"{item.get('id') or index}: related_items references "
                    f"unknown id {related!r}"
                )

    return errors


def _select(items: Iterable[Mapping[str, Any]], state: str) -> List[str]:
    return [str(item.get("id")) for item in items if item.get("state") == state]


def list_ready_for_decision(data: Mapping[str, Any]) -> List[str]:
    """Items sufficiently investigated for owner review.

    This is not a list of work to start. Authorization comes from a separate
    owner-approved Dev Order.
    """
    return _select(data.get("items") or [], "READY_FOR_DECISION")


def list_lead_only(data: Mapping[str, Any]) -> List[str]:
    """Items whose evidence is entirely lead-only."""
    return [
        str(item.get("id"))
        for item in data.get("items") or []
        if isinstance(item, Mapping) and is_lead_only(item)
    ]


def list_blocked(data: Mapping[str, Any]) -> List[str]:
    """Items whose progress depends on something not yet true."""
    return _select(data.get("items") or [], "BLOCKED")


def list_post_census(data: Mapping[str, Any]) -> List[str]:
    """Items resting on incident evidence recovered after the census closed.

    Their evidence may be perfectly durable. What they lack is census
    membership, which is what readiness is computed against.
    """
    return [
        str(item.get("id"))
        for item in data.get("items") or []
        if isinstance(item, Mapping)
        and item.get("census_status") == "POST_CENSUS"
    ]


def summarize_queue(data: Mapping[str, Any]) -> str:
    """Validate, then render a summary. Raises if the queue is unusable.

    Validity is only ever observed as *the summary rendering at all* — there is
    no mode that reports "valid" and stops.
    """
    errors = validate_queue(data)
    if errors:
        raise DeferredQueueError(
            "deferred-issue queue is invalid:\n  " + "\n  ".join(errors)
        )

    items = data.get("items") or []
    by_state: Dict[str, int] = {}
    for item in items:
        by_state[str(item.get("state"))] = by_state.get(str(item.get("state")), 0) + 1

    lines = [
        f"schema_version         : {data.get('schema_version')}",
        f"order                  : {data.get('order')}",
        f"census_authority       : {data.get('census_authority')}",
        f"implementation_authority: {data.get('implementation_authority')}",
        f"items                  : {len(items)}",
        "states                 : "
        + ", ".join(f"{state}={count}" for state, count in sorted(by_state.items())),
        f"ready_for_decision     : {list_ready_for_decision(data) or 'none'}",
        f"blocked                : {list_blocked(data) or 'none'}",
        f"lead_only              : {list_lead_only(data) or 'none'}",
        f"durable_evidence       : "
        + str([i.get("id") for i in items if derive_evidence_status(i) == "DURABLE"]),
        f"post_census            : {list_post_census(data) or 'none'}",
        f"authorized_items       : {[i.get('id') for i in items if i.get('implementation_authorized')] or 'none'}",
    ]
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate-deferred-issues",
        description=(
            "Read-only validation and summary of the AGENT-PROGRAM-003 "
            "deferred-issue queue."
        ),
    )
    parser.add_argument(
        "--queue",
        default=None,
        help="Path to the queue JSON (default: the committed queue).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        data = load_queue(Path(args.queue) if args.queue else None)
    except OSError as exc:
        print(f"could not read queue: {exc}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"queue is not valid JSON: {exc}")
        return 2

    try:
        print(summarize_queue(data))
    except DeferredQueueError as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
