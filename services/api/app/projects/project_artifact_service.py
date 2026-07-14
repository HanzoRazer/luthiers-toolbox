# services/api/app/projects/project_artifact_service.py
"""
Project ↔ Manufacturing Artifact association (SPINE-004).

The canonical, single service for recording that an RMOS manufacturing run artifact
belongs to an instrument's engineering record. It is the one place all Project↔artifact
associations pass through (no inline project updates elsewhere).

Authority boundary (ADR-002 + the SPINE-004 Dev Order):
    - RMOS remains the SOLE owner of manufacturing artifacts (generation + persistence).
    - CAM remains the SOLE owner of manufacturing planning/computation.
    - The Project Spine records ASSOCIATION only. It stores a reference
      (``ProjectArtifactRef``) built from the *actual* persisted artifact — never a copy
      of the payload (no toolpaths / feasibility data are duplicated into the project).

This service does NOT generate artifacts. It reads an existing artifact
(``rmos.runs_v2.store_api.get_run``) and associates a reference. Association is append-only
and idempotent by ``run_id`` (mirrors the analyzer observation edge, SPINE-002).

Concurrency: ``associate_artifact_with_project`` is a read-modify-write of the whole
``Project.data`` blob. Callers that persist must first row-lock via
``service.lock_project_row_for_update`` (the router does) and are responsible for
``session.commit()``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    # RunArtifact is used only in type annotations below. The `from __future__ import
    # annotations` at the top of this module means all annotations are lazily-evaluated
    # strings at runtime, so this guard is sufficient — no runtime import is needed.
    from ..rmos.runs_v2.schemas import RunArtifact
from ..rmos.runs_v2.store_api import get_run
from ..schemas.instrument_project import InstrumentProjectData, ProjectArtifactRef
from .service import (
    ProjectStateUninitializedError,
    _utcnow_iso,
    apply_design_state_to_project,
    create_default_design_state,
    parse_design_state,
)

# Growth bound: cap the number of active (non-removed) artifact associations per project.
# Prevents unbounded append-only growth. Oldest non-production artifacts should be archived
# or removed before hitting this limit. 1000 is generous for any realistic instrument project.
MAX_MANUFACTURING_ARTIFACTS = 1000


class ArtifactNotFoundError(Exception):
    """The referenced RMOS run artifact does not exist. Associating a non-existent
    artifact is rejected rather than recording a dangling reference."""


class ArtifactProvenanceMismatchError(Exception):
    """A caller-supplied expected provenance value (tool_id / feasibility hash) does not
    match the actual persisted artifact — the caller is referring to a different artifact
    than it claims. Rejected rather than recording a misleading reference."""


class ArtifactAssociationConflictError(Exception):
    """A ``run_id`` is already associated but with *different* artifact provenance.

    Association is append-only + idempotent: re-associating the same run is a no-op.
    Because a reference is derived from the immutable, write-once artifact, this fires only
    if the stored provenance for a ``run_id`` has changed underneath us — a genuine
    integrity conflict, surfaced rather than silently overwritten."""


class CrossProjectAssociationError(Exception):
    """The artifact's ``source_project_id`` does not match the target project.

    RMOS artifacts don't carry project linkage, so the only guard against cross-project
    misassociation is a caller-supplied ``source_project_id`` assertion. If provided and
    it doesn't match, we reject rather than allowing a project to claim another project's
    manufacturing artifact."""


class ArtifactCapExceededError(Exception):
    """The project has reached the maximum number of active artifact associations.

    Prevents unbounded append-only growth. Remove or archive old associations before
    adding new ones."""


def _provenance_signature(ref: ProjectArtifactRef) -> tuple:
    """Artifact-derived identity of a reference, excluding project-side association
    metadata (``associated_at`` / ``project_revision``). Two references to the same
    immutable artifact share this signature — the basis for idempotency."""
    return (
        ref.run_id,
        ref.tool_id,
        ref.mode,
        ref.event_type,
        ref.status,
        ref.risk_level,
        ref.artifact_created_at,
        ref.feasibility_sha256,
        ref.toolpaths_sha256,
    )


def build_artifact_ref_from_run(
    artifact: RunArtifact,
    *,
    associated_at: str,
    project_revision: Optional[str] = None,
    source_project_id: Optional[str] = None,
) -> ProjectArtifactRef:
    """
    Map a persisted ``RunArtifact`` into a ``ProjectArtifactRef``.

    Every artifact-provenance field is read from the actual artifact — never fabricated.
    Only ``associated_at`` / ``project_revision`` / ``source_project_id`` are project-side
    association metadata. ``source_project_id`` is caller-asserted and guards against
    cross-project misassociation.
    """
    created_at = getattr(artifact, "created_at_utc", None)
    decision = getattr(artifact, "decision", None)
    hashes = getattr(artifact, "hashes", None)
    return ProjectArtifactRef(
        run_id=artifact.run_id,
        tool_id=getattr(artifact, "tool_id", None),
        mode=getattr(artifact, "mode", None),
        event_type=getattr(artifact, "event_type", None),
        status=str(artifact.status) if getattr(artifact, "status", None) is not None else None,
        risk_level=getattr(decision, "risk_level", None),
        artifact_created_at=created_at.isoformat() if created_at is not None else None,
        feasibility_sha256=getattr(hashes, "feasibility_sha256", None),
        toolpaths_sha256=getattr(hashes, "toolpaths_sha256", None),
        associated_at=associated_at,
        project_revision=project_revision,
        source_project_id=source_project_id,
    )


def validate_project_artifact(
    run_id: str,
    *,
    expected_tool_id: Optional[str] = None,
    expected_feasibility_sha256: Optional[str] = None,
) -> RunArtifact:
    """
    Fetch and validate the referenced RMOS artifact.

    Raises :class:`ArtifactNotFoundError` if no artifact with ``run_id`` exists, or
    :class:`ArtifactProvenanceMismatchError` if a supplied ``expected_*`` value does not
    match the persisted artifact. Returns the real ``RunArtifact`` on success.
    """
    if not run_id or not run_id.strip():
        raise ArtifactNotFoundError("run_id is required and must be non-empty.")

    artifact = get_run(run_id)
    if artifact is None:
        raise ArtifactNotFoundError(f"No manufacturing run artifact found for run_id '{run_id}'.")

    if expected_tool_id is not None and getattr(artifact, "tool_id", None) != expected_tool_id:
        raise ArtifactProvenanceMismatchError(
            f"run_id '{run_id}' has tool_id '{getattr(artifact, 'tool_id', None)}', "
            f"not the expected '{expected_tool_id}'."
        )

    if expected_feasibility_sha256 is not None:
        actual = getattr(getattr(artifact, "hashes", None), "feasibility_sha256", None)
        if actual != expected_feasibility_sha256:
            raise ArtifactProvenanceMismatchError(
                f"run_id '{run_id}' feasibility hash does not match the expected value."
            )

    return artifact


def merge_artifact_refs(
    existing_state: Optional[InstrumentProjectData],
    incoming: list[ProjectArtifactRef],
) -> list[ProjectArtifactRef]:
    """
    Append-only merge of artifact references, deduplicated by stable ``run_id``.

    Canonical single implementation of the SPINE-004 append-only association rule — used
    by both this service and ``PUT /design-state`` so all writers behave identically.
    Existing references are never mutated or replaced; an incoming reference whose
    ``run_id`` already exists is dropped (idempotent), preserving the original association
    timestamp and preventing data loss.
    """
    existing = list(existing_state.manufacturing_artifacts) if existing_state else []
    existing_ids = {ref.run_id for ref in existing}
    return existing + [ref for ref in incoming if ref.run_id not in existing_ids]


def _reject_artifact_conflicts(
    existing_state: Optional[InstrumentProjectData],
    incoming: list[ProjectArtifactRef],
) -> None:
    """Raise :class:`ArtifactAssociationConflictError` if an incoming ``run_id`` already
    exists with different artifact provenance. Idempotent re-association (same artifact)
    passes through — the comparison ignores project-side association metadata."""
    existing_by_id = {
        ref.run_id: ref
        for ref in (existing_state.manufacturing_artifacts if existing_state else [])
    }
    for ref in incoming:
        prior = existing_by_id.get(ref.run_id)
        if prior is not None and _provenance_signature(prior) != _provenance_signature(ref):
            raise ArtifactAssociationConflictError(
                f"run_id '{ref.run_id}' is already associated with a different artifact "
                "provenance; associations are append-only and must not overwrite the "
                "earlier reference."
            )


def _count_active_artifacts(state: Optional[InstrumentProjectData]) -> int:
    """Count non-removed artifact associations."""
    if not state:
        return 0
    return sum(1 for ref in state.manufacturing_artifacts if ref.removed_at is None)


def associate_artifact_with_project(
    project: Any,
    run_id: str,
    *,
    associated_at: Optional[str] = None,
    expected_tool_id: Optional[str] = None,
    expected_feasibility_sha256: Optional[str] = None,
    source_project_id: Optional[str] = None,
) -> InstrumentProjectData:
    """
    Associate an existing RMOS run artifact with a project's canonical record.

    Validates that the artifact exists (and matches any supplied expected provenance),
    then appends a reference to it built from the *actual* artifact. Append-only +
    idempotent by ``run_id``. Only ``manufacturing_artifacts`` is touched — spec /
    geometry / material / analyzer observations / manufacturing_state are unchanged.
    Records association, never artifact ownership, and promotes no authority.

    Cross-project guard: if ``source_project_id`` is provided, it must match the target
    project's ID. RMOS artifacts don't carry project linkage, so this caller-asserted
    field is the only guard against cross-project misassociation. Raises
    :class:`CrossProjectAssociationError` on mismatch.

    Growth bound: raises :class:`ArtifactCapExceededError` if the project already has
    ``MAX_MANUFACTURING_ARTIFACTS`` active (non-removed) associations.

    Fail-closed: a missing artifact raises :class:`ArtifactNotFoundError`; a project with
    neither design state nor a declared ``instrument_type`` raises
    :class:`ProjectStateUninitializedError` (no fabricated instrument type). Caller is
    responsible for row-locking and ``session.commit()``.
    """
    # Cross-project validation: if caller asserts source_project_id, it must match target
    if source_project_id is not None:
        project_id_str = str(project.id) if hasattr(project, "id") else None
        if project_id_str and source_project_id != project_id_str:
            raise CrossProjectAssociationError(
                f"Artifact's source_project_id '{source_project_id}' does not match target "
                f"project '{project_id_str}'. Cannot associate another project's artifact."
            )

    artifact = validate_project_artifact(
        run_id,
        expected_tool_id=expected_tool_id,
        expected_feasibility_sha256=expected_feasibility_sha256,
    )

    existing_state = parse_design_state(project.data)
    if existing_state is None:
        if not getattr(project, "instrument_type", None):
            raise ProjectStateUninitializedError(
                "project has no design state and no declared instrument_type; cannot seed a "
                "canonical home for the artifact reference without fabricating an instrument type."
            )
        existing_state = create_default_design_state(instrument_type=project.instrument_type)

    # Growth bound check (only for new associations, not idempotent re-associations)
    existing_ids = {ref.run_id for ref in existing_state.manufacturing_artifacts}
    if run_id not in existing_ids:
        active_count = _count_active_artifacts(existing_state)
        if active_count >= MAX_MANUFACTURING_ARTIFACTS:
            raise ArtifactCapExceededError(
                f"Project has {active_count} active artifact associations, which meets the "
                f"limit of {MAX_MANUFACTURING_ARTIFACTS}. Remove or archive old associations "
                "before adding new ones."
            )

    revision = (
        project.updated_at.isoformat()
        if getattr(project, "updated_at", None) is not None
        else None
    )
    ref = build_artifact_ref_from_run(
        artifact,
        associated_at=associated_at or _utcnow_iso(),
        project_revision=revision,
        source_project_id=source_project_id,
    )

    _reject_artifact_conflicts(existing_state, [ref])
    merged = merge_artifact_refs(existing_state, [ref])
    new_state = existing_state.model_copy(update={"manufacturing_artifacts": merged})
    apply_design_state_to_project(project, new_state)
    return new_state


def retrieve_project_artifacts(project: Any, *, include_removed: bool = False) -> list[ProjectArtifactRef]:
    """Return the project's associated artifact references (read-only). Empty list if the
    project has no design state yet.

    By default, only active (non-removed) associations are returned. Pass
    ``include_removed=True`` to include soft-removed associations (for audit).
    """
    state = parse_design_state(project.data)
    if not state:
        return []
    if include_removed:
        return list(state.manufacturing_artifacts)
    return [ref for ref in state.manufacturing_artifacts if ref.removed_at is None]


def dissociate_artifact_from_project(
    project: Any,
    run_id: str,
    *,
    removed_at: Optional[str] = None,
) -> InstrumentProjectData:
    """
    Soft-remove an artifact association from a project's canonical record.

    This is the correction/removal path for bad associations. The reference is NOT deleted
    (for audit trail); instead, ``removed_at`` is set to the current timestamp, and the
    reference is excluded from active queries.

    Raises ``ArtifactNotFoundError`` if no association exists for the given ``run_id``.
    Caller is responsible for row-locking and ``session.commit()``.
    """
    existing_state = parse_design_state(project.data)
    if existing_state is None:
        raise ArtifactNotFoundError(f"No artifact association found for run_id '{run_id}'.")

    # Find the association by run_id
    found = False
    updated_artifacts = []
    for ref in existing_state.manufacturing_artifacts:
        if ref.run_id == run_id:
            if ref.removed_at is not None:
                raise ArtifactNotFoundError(
                    f"Artifact association for run_id '{run_id}' was already removed."
                )
            # Soft-remove: set removed_at
            updated_ref = ref.model_copy(update={"removed_at": removed_at or _utcnow_iso()})
            updated_artifacts.append(updated_ref)
            found = True
        else:
            updated_artifacts.append(ref)

    if not found:
        raise ArtifactNotFoundError(f"No artifact association found for run_id '{run_id}'.")

    new_state = existing_state.model_copy(update={"manufacturing_artifacts": updated_artifacts})
    apply_design_state_to_project(project, new_state)
    return new_state
