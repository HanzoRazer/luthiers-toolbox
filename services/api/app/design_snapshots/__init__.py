"""Immutable LTB design snapshots pinned to an unverified CNC job id.

The mutable project save path is not this package. A snapshot copies a
serialized design and does not approve it.
"""
from .capture import capture_design_snapshot
from .contracts import (
    SCHEMA_ID,
    SCHEMA_VERSION,
    UNVERIFIED_EXTERNAL_REFERENCE,
    ActorReferenceV1,
    ArtifactReferenceV1,
    ExternalJobReferenceV1,
    GeneratorReferenceV1,
    LtbDesignSnapshotV1,
    LtbProjectReferenceV1,
    new_design_snapshot_id,
)
from .errors import (
    DesignSnapshotError,
    DesignSnapshotNotFound,
    DesignSnapshotRepositoryError,
    DuplicateDesignSnapshot,
)
from .repository import FileDesignSnapshotRepository

__all__ = [
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "UNVERIFIED_EXTERNAL_REFERENCE",
    "ActorReferenceV1",
    "ArtifactReferenceV1",
    "DesignSnapshotError",
    "DesignSnapshotNotFound",
    "DesignSnapshotRepositoryError",
    "DuplicateDesignSnapshot",
    "ExternalJobReferenceV1",
    "FileDesignSnapshotRepository",
    "GeneratorReferenceV1",
    "LtbDesignSnapshotV1",
    "LtbProjectReferenceV1",
    "capture_design_snapshot",
    "new_design_snapshot_id",
]
