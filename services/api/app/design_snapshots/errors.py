"""Errors for the design-snapshot library. No route raises these."""
from __future__ import annotations


class DesignSnapshotError(ValueError):
    """The snapshot contract refused a value."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class DesignSnapshotRepositoryError(RuntimeError):
    """The store could not accept or reread a snapshot."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class DuplicateDesignSnapshot(DesignSnapshotRepositoryError):
    """This snapshot id is already stored with different bytes."""

    def __init__(self, snapshot_id: str) -> None:
        super().__init__(snapshot_id, code="DUPLICATE_SNAPSHOT")
        self.snapshot_id = snapshot_id


class DesignSnapshotNotFound(DesignSnapshotRepositoryError):
    """No file is stored under this snapshot id."""

    def __init__(self, snapshot_id: str) -> None:
        super().__init__(snapshot_id, code="NOT_FOUND")
        self.snapshot_id = snapshot_id
