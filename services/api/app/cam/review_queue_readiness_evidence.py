"""
Review queue architecture readiness — evidence adapter.

Converts current review-queue declarations into typed evidence. Deliberately separate from
the evaluator: this module knows about the repository, the evaluator knows about policy, and
neither knows the other's concerns.

**Inspection is performed with ``ast`` over source files, never by importing the modules
under assessment.** Two reasons, and the second is the deeper one:

1. *Dependency boundary.* This code runs inside the repository's dependency-free required
   check. The models it assesses (``ReviewQueueItem``, ``ReviewDecisionRecord``) are
   Pydantic, so importing them would drag Pydantic into a job that installs no packages.
2. *Honesty.* The question is what the subsystem **declares**, which is a property of the
   source. Importing would additionally execute module-level code and make the result
   depend on the runtime environment — turning a static claim into a partly dynamic one.

Two rules govern everything here:

- **Never infer behaviour from a name.** That a module is called ``*_registry`` says nothing
  about whether it persists. Evidence is read from declared structure — an annotated field,
  a module-level assignment — not from what something is called.
- **Absence and unverifiability are different findings.** ``present=False`` is a positive
  claim of confirmed absence and requires having successfully parsed the source. If a source
  cannot be read or parsed, **no evidence is emitted**, and the evaluator reports
  UNRESOLVED rather than inventing a verdict.

This module executes no production workflow, mutates nothing, and performs only read-only
file access.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Optional, Set, Tuple

from .review_queue_readiness import ReadinessEvidence
from .review_queue_readiness_requirements import (
    EVIDENCE_ATTRIBUTABLE_IDENTITY,
    EVIDENCE_CREATION_TIMESTAMP,
    EVIDENCE_DURABLE_PERSISTENCE,
    EVIDENCE_NOTIFICATION_DELIVERY,
)

_CAM_DIR = Path(__file__).resolve().parent

_ITEM_REL = "services/api/app/cam/review_queue_item.py"
_DECISION_REL = "services/api/app/cam/review_decision_record.py"
_REGISTRY_REL = "services/api/app/cam/review_queue_registry.py"

# Module-level names that would indicate durable backing if declared.
_DURABLE_MARKERS = ("ENGINE", "SESSION", "STORE", "DB", "ADAPTER", "BACKEND")
# Module-level names that would indicate a delivery mechanism if declared.
_DELIVERY_MARKERS = ("NOTIFIER", "WEBHOOK", "PUBLISHER", "EVENT_BUS", "DISPATCHER")


def _parse(filename: str) -> Optional[ast.Module]:
    """Parse a cam module by filename. Returns None if unreadable or unparseable.

    Returning None matters: it propagates as *no evidence*, which the evaluator reports as
    UNRESOLVED. A parse failure must never masquerade as confirmed absence.
    """
    path = _CAM_DIR / filename
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return None


def _class_annotated_fields(tree: ast.Module, class_name: str) -> Set[str]:
    """Annotated field names declared directly on a class."""
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
    return set()


def _module_level_names(tree: ast.Module) -> Set[str]:
    """Names assigned at module level, annotated or plain."""
    names: Set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def _dict_annotated_module_names(tree: ast.Module) -> Set[str]:
    """Module-level names annotated as a Dict — i.e. in-memory mapping storage."""
    names: Set[str] = set()
    for node in tree.body:
        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)):
            continue
        annotation = ast.unparse(node.annotation) if node.annotation else ""
        if annotation.startswith("Dict[") or annotation.startswith("dict["):
            names.add(node.target.id)
    return names


def _collect_persistence_evidence() -> Optional[ReadinessEvidence]:
    """Is a durable persistence adapter declared for the review queue?

    Determined from the registry's declared storage, not its filename.
    """
    tree = _parse("review_queue_registry.py")
    if tree is None:
        return None

    module_names = _module_level_names(tree)
    declared_durable = sorted(n for n in _DURABLE_MARKERS if n in module_names)
    if declared_durable:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_DURABLE_PERSISTENCE,
            present=True,
            source=_REGISTRY_REL,
            detail=f"Durable backing declared: {', '.join(declared_durable)}.",
        )

    dict_indexes = sorted(_dict_annotated_module_names(tree))
    return ReadinessEvidence(
        evidence_kind=EVIDENCE_DURABLE_PERSISTENCE,
        present=False,
        source=_REGISTRY_REL,
        detail=(
            "Queue is backed by module-level in-memory mappings"
            + (f" ({', '.join(dict_indexes)})" if dict_indexes else "")
            + "; no durable adapter is declared. Registry code existing is not persistence."
        ),
    )


def _collect_identity_evidence() -> Optional[ReadinessEvidence]:
    """Is review actor identity bound to something attributable?

    A declared actor field is necessary but not sufficient — whether authentication is
    *enforced* is a runtime property. The requirement is HYBRID, so a present declaration
    still yields UNRESOLVED rather than SATISFIED.
    """
    decision_tree = _parse("review_decision_record.py")
    item_tree = _parse("review_queue_item.py")
    if decision_tree is None or item_tree is None:
        return None

    decision_fields = _class_annotated_fields(decision_tree, "ReviewDecisionRecord")
    item_fields = _class_annotated_fields(item_tree, "ReviewQueueItem")

    if "reviewer_ref" in decision_fields:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_ATTRIBUTABLE_IDENTITY,
            present=True,
            source=_DECISION_REL,
            detail=(
                "ReviewDecisionRecord declares reviewer_ref. Whether it resolves to an "
                "authenticated account, and whether that is enforced on the request path, "
                "cannot be established by static inspection."
            ),
        )

    return ReadinessEvidence(
        evidence_kind=EVIDENCE_ATTRIBUTABLE_IDENTITY,
        present=False,
        source=_ITEM_REL,
        detail=(
            "No attributable actor reference declared"
            + (
                "; assigned_role is a free-text string that names no account."
                if "assigned_role" in item_fields
                else "."
            )
        ),
    )


def _collect_timestamp_evidence() -> Optional[ReadinessEvidence]:
    """Do queue items and decision records declare creation timestamps?

    8F recorded this as a gap in 2026-05; it has since closed. The check is retained so the
    property stays verified rather than assumed.
    """
    item_tree = _parse("review_queue_item.py")
    decision_tree = _parse("review_decision_record.py")
    if item_tree is None or decision_tree is None:
        return None

    item_has = "created_at" in _class_annotated_fields(item_tree, "ReviewQueueItem")
    decision_has = "created_at" in _class_annotated_fields(
        decision_tree, "ReviewDecisionRecord"
    )

    if item_has and decision_has:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_CREATION_TIMESTAMP,
            present=True,
            source=f"{_ITEM_REL}; {_DECISION_REL}",
            detail=(
                "created_at declared on both ReviewQueueItem and ReviewDecisionRecord. "
                "The historical 8F timestamp gap is closed."
            ),
        )

    missing: List[str] = []
    if not item_has:
        missing.append("ReviewQueueItem")
    if not decision_has:
        missing.append("ReviewDecisionRecord")
    return ReadinessEvidence(
        evidence_kind=EVIDENCE_CREATION_TIMESTAMP,
        present=False,
        source=f"{_ITEM_REL}; {_DECISION_REL}",
        detail=f"created_at not declared on: {', '.join(missing)}.",
    )


def _collect_notification_evidence() -> Optional[ReadinessEvidence]:
    """Is any delivery mechanism declared for queue changes?"""
    tree = _parse("review_queue_registry.py")
    if tree is None:
        return None

    module_names = _module_level_names(tree)
    declared = sorted(n for n in _DELIVERY_MARKERS if n in module_names)
    if declared:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_NOTIFICATION_DELIVERY,
            present=True,
            source=_REGISTRY_REL,
            detail=f"Delivery mechanism declared: {', '.join(declared)}.",
        )

    return ReadinessEvidence(
        evidence_kind=EVIDENCE_NOTIFICATION_DELIVERY,
        present=False,
        source=_REGISTRY_REL,
        detail=(
            "No notifier, webhook, publisher, event bus or dispatcher is declared on the "
            "review-queue modules. Queue changes are not communicated externally."
        ),
    )


def collect_readiness_evidence() -> Tuple[ReadinessEvidence, ...]:
    """Build typed evidence from current authoritative declarations.

    Deterministic ordering. No mutation, no network, no imports of the assessed modules.
    Every item carries a citable source. Collectors returning None are omitted, which the
    evaluator reports as UNRESOLVED rather than as absence.
    """
    collected = (
        _collect_persistence_evidence(),
        _collect_identity_evidence(),
        _collect_timestamp_evidence(),
        _collect_notification_evidence(),
    )
    return tuple(item for item in collected if item is not None)
