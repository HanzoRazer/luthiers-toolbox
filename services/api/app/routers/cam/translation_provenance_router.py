"""
Translation Artifact Provenance Router

CAM Dev Order 7F: Provenance introspection endpoints.

Provides read-only access to translation artifact provenance:
  - List all provenances
  - Get provenance by ID
  - Get provenances by artifact ID
  - Get provenance by lineage hash

No mutation endpoints. No lineage editing. Provenance is immutable.

7F invariants:
  - immutable: always true
  - execution_authorized: always false
  - machine_output_present: always false
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.cam.translation_artifact_provenance import (
    TranslationArtifactProvenance,
    TranslationArtifactProvenanceSummary,
    get_provenance,
    get_provenance_by_artifact,
    get_provenance_by_lineage_hash,
    list_provenances,
)


router = APIRouter(
    prefix="/api/cam/translation-provenance",
    tags=["CAM Translation Provenance"],
)


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class ProvenanceListResponse(BaseModel):
    """Response for listing provenances."""

    provenances: List[TranslationArtifactProvenance] = Field(
        ..., description="List of provenance records"
    )
    count: int = Field(..., description="Total count")

    # 7F Safety Assertions
    all_immutable: bool = Field(
        default=True,
        description="Always true — all provenances are immutable"
    )
    execution_authorized_count: int = Field(
        default=0,
        description="Always 0 — no execution authorized"
    )


class ProvenanceResponse(BaseModel):
    """Response for single provenance lookup."""

    provenance: TranslationArtifactProvenance = Field(
        ..., description="Provenance record"
    )

    # 7F Safety Assertions
    immutable: bool = Field(
        default=True,
        description="Always true — provenance is immutable"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always false — execution not authorized"
    )


class ProvenanceSummaryListResponse(BaseModel):
    """Response for listing provenance summaries."""

    summaries: List[TranslationArtifactProvenanceSummary] = Field(
        ..., description="List of provenance summaries"
    )
    count: int = Field(..., description="Total count")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=ProvenanceListResponse,
    summary="List all translation artifact provenances",
    description="Returns all registered provenance records from the in-memory index.",
)
def list_translation_provenances(
    limit: int = Query(default=100, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> ProvenanceListResponse:
    """List all registered provenances."""
    all_provenances = list_provenances()

    # Apply pagination
    paginated = all_provenances[offset : offset + limit]

    return ProvenanceListResponse(
        provenances=paginated,
        count=len(all_provenances),
        all_immutable=True,
        execution_authorized_count=0,
    )


@router.get(
    "/summaries",
    response_model=ProvenanceSummaryListResponse,
    summary="List provenance summaries",
    description="Returns lightweight summaries of all registered provenances.",
)
def list_provenance_summaries(
    limit: int = Query(default=100, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> ProvenanceSummaryListResponse:
    """List provenance summaries."""
    all_provenances = list_provenances()

    # Apply pagination and convert to summaries
    paginated = all_provenances[offset : offset + limit]
    summaries = [p.to_summary() for p in paginated]

    return ProvenanceSummaryListResponse(
        summaries=summaries,
        count=len(all_provenances),
    )


@router.get(
    "/{provenance_id}",
    response_model=ProvenanceResponse,
    summary="Get provenance by ID",
    description="Returns a single provenance record by its ID.",
)
def get_translation_provenance(
    provenance_id: str = Path(..., description="Provenance identifier"),
) -> ProvenanceResponse:
    """Get a specific provenance by ID."""
    provenance = get_provenance(provenance_id)

    if provenance is None:
        raise HTTPException(
            status_code=404,
            detail=f"Provenance '{provenance_id}' not found in index",
        )

    return ProvenanceResponse(
        provenance=provenance,
        immutable=True,
        execution_authorized=False,
    )


@router.get(
    "/by-artifact/{artifact_id}",
    response_model=ProvenanceListResponse,
    summary="Get provenances by artifact ID",
    description="""
Returns all provenances associated with an artifact ID.

Note: Same artifact may have multiple provenances from different
governance contexts (different policy snapshots, different evaluation times).
""",
)
def get_provenances_by_artifact(
    artifact_id: str = Path(..., description="Artifact identifier"),
) -> ProvenanceListResponse:
    """Get all provenances for an artifact."""
    provenances = get_provenance_by_artifact(artifact_id)

    return ProvenanceListResponse(
        provenances=provenances,
        count=len(provenances),
        all_immutable=True,
        execution_authorized_count=0,
    )


@router.get(
    "/by-lineage-hash/{lineage_hash}",
    response_model=ProvenanceResponse,
    summary="Get provenance by lineage hash",
    description="""
Returns provenance with the specified deterministic lineage hash.

Lineage hash is deterministic: same governance ancestry produces same hash.
""",
)
def get_provenance_by_hash(
    lineage_hash: str = Path(..., description="Deterministic lineage hash"),
) -> ProvenanceResponse:
    """Get provenance by deterministic lineage hash."""
    provenance = get_provenance_by_lineage_hash(lineage_hash)

    if provenance is None:
        raise HTTPException(
            status_code=404,
            detail=f"No provenance found with lineage hash '{lineage_hash}'",
        )

    return ProvenanceResponse(
        provenance=provenance,
        immutable=True,
        execution_authorized=False,
    )
