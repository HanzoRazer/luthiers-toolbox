"""
Rosette Snapshot Routes - Bundle 31.0.27 + H1 Hardening

API endpoints for rosette design snapshot export/import with RMOS run artifact persistence.

H1 Hardening:
- invalid snapshot_id → HTTP 400
- missing snapshot → HTTP 404
- SnapshotIdError exceptions handled cleanly
"""

from typing import Optional
from fastapi import APIRouter, HTTPException

from ..schemas.rosette_snapshot import (
    RosetteDesignSnapshot,
    ExportSnapshotRequest,
    ExportSnapshotResponse,
    ImportSnapshotRequest,
    ImportSnapshotResponse,
    ListSnapshotsResponse,
    SnapshotMetadata,
)
from ..schemas.snapshot_meta import SnapshotMetaPatch, BaselineToggleRequest
from ..services.rosette_snapshot_store import (
    save_snapshot,
    load_snapshot,
    delete_snapshot,
    list_snapshots,
    count_snapshots,
    compute_design_fingerprint,
    create_snapshot_id,
    set_baseline,
    get_baseline,
    SnapshotIdError,
)
from ..services.rosette_feasibility_scorer import (
    estimate_rosette_feasibility,
    MaterialSpec,
    ToolSpec,
)
from ...services.art_studio_run_service import create_art_studio_snapshot_run


router = APIRouter(prefix="/rosette/snapshots", tags=["art-studio", "snapshots"])


# Default material/tool for feasibility checks during export
default_material = MaterialSpec(
    material_id="default-ebony",
    name="Ebony",
    material_class="hardwood",
)
default_tool = ToolSpec(
    tool_id="default-vbit",
    diameter_mm=6.0,
    flutes=2,
    tool_material="carbide",
    stickout_mm=25.0,
)


@router.post("/export", response_model=ExportSnapshotResponse)
async def export_snapshot(req: ExportSnapshotRequest):
    """
    Export (save) a rosette design as a snapshot.

    Computes feasibility, persists the snapshot, and creates a RunArtifact for audit trail.
    """
    # Compute design fingerprint
    fingerprint = compute_design_fingerprint(req.design)

    # Optionally compute feasibility
    feasibility = None
    if req.include_feasibility:
        feasibility = estimate_rosette_feasibility(
            spec=req.design,
            default_material=default_material,
            default_tool=default_tool,
        )

    # Create snapshot
    snapshot_id = create_snapshot_id()
    snapshot = RosetteDesignSnapshot(
        snapshot_id=snapshot_id,
        design_fingerprint=fingerprint,
        design=req.design,
        feasibility=feasibility,
        metadata=SnapshotMetadata(
            name=req.name,
            description=req.description,
            tags=req.tags,
            source="manual",
        ),
    )

    # Save to disk (with error handling)
    try:
        save_snapshot(snapshot)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create RunArtifact for audit trail
    run_artifact = create_art_studio_snapshot_run(
        snapshot={
            "snapshot_id": snapshot_id,
            "name": req.name,
            "design_fingerprint": fingerprint,
            "feasibility": feasibility.model_dump() if feasibility else None,
        },
        tool_id=default_tool.tool_id,
        meta={"operation": "export"},
    )

    # Update snapshot with run_id
    snapshot.run_id = run_artifact.run_id
    try:
        save_snapshot(snapshot)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ExportSnapshotResponse(
        snapshot_id=snapshot_id,
        design_fingerprint=fingerprint,
        run_id=run_artifact.run_id,
        feasibility=feasibility,
    )


@router.post("/import", response_model=ImportSnapshotResponse)
async def import_snapshot(req: ImportSnapshotRequest):
    """
    Import a rosette design snapshot.

    Validates the snapshot, saves it, and creates a RunArtifact for audit trail.
    """
    snapshot = req.snapshot
    warnings = []

    # Validate snapshot_id format
    if not snapshot.snapshot_id:
        snapshot.snapshot_id = create_snapshot_id()
        warnings.append("Generated new snapshot_id for import")

    # Recompute fingerprint to verify integrity
    computed_fingerprint = compute_design_fingerprint(snapshot.design)
    if snapshot.design_fingerprint != computed_fingerprint:
        warnings.append(
            f"Design fingerprint mismatch: expected {snapshot.design_fingerprint}, "
            f"computed {computed_fingerprint}. Using computed fingerprint."
        )
        snapshot.design_fingerprint = computed_fingerprint

    # Update metadata source
    if snapshot.metadata is None:
        snapshot.metadata = SnapshotMetadata()
    snapshot.metadata.source = "import"

    # Save to disk (with error handling)
    try:
        save_snapshot(snapshot)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create RunArtifact for audit trail
    run_artifact = create_art_studio_snapshot_run(
        snapshot={
            "snapshot_id": snapshot.snapshot_id,
            "name": snapshot.metadata.name if snapshot.metadata else None,
            "design_fingerprint": snapshot.design_fingerprint,
            "feasibility": snapshot.feasibility.model_dump() if snapshot.feasibility else None,
        },
        tool_id=default_tool.tool_id,
        meta={"operation": "import"},
    )

    # Update snapshot with run_id
    snapshot.run_id = run_artifact.run_id
    try:
        save_snapshot(snapshot)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ImportSnapshotResponse(
        snapshot_id=snapshot.snapshot_id,
        design_fingerprint=snapshot.design_fingerprint,
        run_id=run_artifact.run_id,
        warnings=warnings,
    )


@router.get("/{snapshot_id}", response_model=RosetteDesignSnapshot)
async def get_snapshot(snapshot_id: str):
    """
    Get a snapshot by ID.
    """
    try:
        snapshot = load_snapshot(snapshot_id)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return snapshot


@router.delete("/{snapshot_id}")
async def remove_snapshot(snapshot_id: str):
    """
    Delete a snapshot by ID.
    """
    try:
        deleted = delete_snapshot(snapshot_id)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not deleted:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {"deleted": True, "snapshot_id": snapshot_id}


@router.put("/{snapshot_id}", response_model=RosetteDesignSnapshot)
async def update_snapshot_meta(snapshot_id: str, patch: SnapshotMetaPatch):
    """
    Update snapshot metadata (name, notes, tags).

    Only provided fields are updated.
    """
    try:
        snapshot = load_snapshot(snapshot_id)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Apply patch to metadata
    meta = snapshot.metadata
    if patch.name is not None:
        meta.name = patch.name
    if patch.notes is not None:
        meta.notes = patch.notes
    if patch.tags is not None:
        meta.tags = patch.tags

    # Save updated snapshot
    try:
        updated = save_snapshot(snapshot)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return updated


@router.post("/{snapshot_id}/baseline", response_model=RosetteDesignSnapshot)
async def toggle_baseline(snapshot_id: str, req: BaselineToggleRequest):
    """
    Set or clear the baseline flag for a snapshot.

    Only one snapshot can be baseline at a time. Setting baseline=True
    will clear the flag from any other snapshot.
    """
    try:
        updated = set_baseline(snapshot_id, req.baseline)
    except SnapshotIdError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if updated is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return updated


@router.get("/baseline", response_model=RosetteDesignSnapshot)
async def get_baseline_snapshot():
    """
    Get the current baseline snapshot.
    """
    baseline = get_baseline()
    if baseline is None:
        raise HTTPException(status_code=404, detail="No baseline set")
    return baseline


@router.get("/", response_model=ListSnapshotsResponse)
async def list_all_snapshots(
    limit: int = 50,
    offset: int = 0,
    tag: Optional[str] = None,
):
    """
    List all snapshots with optional filtering.
    """
    snapshots = list_snapshots(limit=limit, offset=offset, tag=tag)
    total = count_snapshots(tag=tag)

    return ListSnapshotsResponse(
        snapshots=snapshots,
        total=total,
    )
