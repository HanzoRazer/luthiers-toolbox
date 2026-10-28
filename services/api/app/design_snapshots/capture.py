"""Capture a design snapshot from an already-serialized project state.

The caller supplies the dict produced by the current project serializer.
This module does not import that serializer, open a route, or call a network.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Mapping

from .contracts import (
    ArtifactReferenceV1,
    GeneratorReferenceV1,
    LtbDesignSnapshotV1,
    make_design_snapshot,
    new_design_snapshot_id,
)


def capture_design_snapshot(
    *,
    project_id: str,
    job_id: str,
    design_state: Mapping[str, object],
    captured_at: datetime,
    captured_by: str,
    design_snapshot_id: str | None = None,
    id_factory: Callable[[], str] | None = None,
    artifact_refs: tuple[ArtifactReferenceV1, ...] = (),
    generator_refs: tuple[GeneratorReferenceV1, ...] = (),
) -> LtbDesignSnapshotV1:
    """Copy ``design_state`` into a new snapshot. The input mapping is not mutated."""
    if design_snapshot_id is None:
        design_snapshot_id = (id_factory or new_design_snapshot_id)()
    return make_design_snapshot(
        design_snapshot_id=design_snapshot_id,
        job_id=job_id,
        project_id=project_id,
        design_payload=design_state,
        captured_at=captured_at,
        captured_by=captured_by,
        artifact_refs=artifact_refs,
        generator_refs=generator_refs,
    )
