"""String Master integration router — proxies to sg-agentd for practice sessions.

The sg-agentd daemon wraps the zt_band practice pattern engine.
When deployed on the Smart Guitar's Pi 5 Music Brain, this router proxies
HTTP requests to the local sg-agentd service.

For development, sg-agentd can run locally or requests can fall back to
stub responses.

Endpoints:
    GET  /api/string-master/exercises    - List available exercises
    POST /api/string-master/generate     - Generate a new clip bundle
    GET  /api/string-master/bundles/{id} - Retrieve a clip bundle
    GET  /api/string-master/tags         - List all tags
    GET  /api/string-master/zones        - Zone theory data
    GET  /api/string-master/health       - Health check
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/string-master", tags=["String Master"])

# sg-agentd configuration
SG_AGENTD_HOST = os.getenv("SG_AGENTD_HOST", "127.0.0.1")
SG_AGENTD_PORT = int(os.getenv("SG_AGENTD_PORT", "8420"))
SG_AGENTD_BASE = f"http://{SG_AGENTD_HOST}:{SG_AGENTD_PORT}"
SG_AGENTD_TIMEOUT = float(os.getenv("SG_AGENTD_TIMEOUT", "10.0"))


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    """Request to generate a new clip bundle."""
    exercise_id: Optional[str] = Field(None, description="Exercise ID to use")
    tempo_bpm: int = Field(120, ge=40, le=300, description="Tempo in BPM")
    bars: int = Field(8, ge=1, le=32, description="Number of bars")
    key: str = Field("C", description="Key signature (e.g., 'C', 'Gm')")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    tags: List[str] = Field(default_factory=list, description="Tags to filter by")


class ClipBundle(BaseModel):
    """A generated clip bundle."""
    clip_id: str
    exercise_id: Optional[str] = None
    tempo_bpm: int
    bars: int
    key: str
    seed: int
    tags: List[str] = []
    files: Dict[str, str] = Field(
        default_factory=dict,
        description="Bundle files: clip.mid, clip.tags.json, clip.coach.json, clip.runlog.json"
    )


class Exercise(BaseModel):
    """An available exercise."""
    id: str
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    difficulty: Optional[str] = None


class ZoneInfo(BaseModel):
    """Tritone zone theory data."""
    zones: List[str]
    tritone_pairs: Dict[str, str]
    description: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    sg_agentd_reachable: bool
    sg_agentd_url: str
    version: Optional[str] = None


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------


async def _proxy_get(path: str) -> Dict[str, Any]:
    """Proxy a GET request to sg-agentd."""
    async with httpx.AsyncClient(timeout=SG_AGENTD_TIMEOUT) as client:
        try:
            response = await client.get(f"{SG_AGENTD_BASE}{path}")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"sg-agentd not reachable at {SG_AGENTD_BASE}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"sg-agentd error: {e.response.text}"
            )


async def _proxy_post(path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Proxy a POST request to sg-agentd."""
    async with httpx.AsyncClient(timeout=SG_AGENTD_TIMEOUT) as client:
        try:
            response = await client.post(f"{SG_AGENTD_BASE}{path}", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"sg-agentd not reachable at {SG_AGENTD_BASE}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"sg-agentd error: {e.response.text}"
            )


async def _check_sg_agentd() -> bool:
    """Check if sg-agentd is reachable."""
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            response = await client.get(f"{SG_AGENTD_BASE}/health")
            return response.status_code == 200
        except Exception:
            return False


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check health of String Master integration and sg-agentd connectivity."""
    reachable = await _check_sg_agentd()
    version = None

    if reachable:
        try:
            data = await _proxy_get("/health")
            version = data.get("version")
        except Exception:
            pass

    return HealthResponse(
        status="ok" if reachable else "degraded",
        sg_agentd_reachable=reachable,
        sg_agentd_url=SG_AGENTD_BASE,
        version=version
    )


@router.get("/exercises", response_model=List[Exercise])
async def list_exercises(
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level")
) -> List[Exercise]:
    """List available exercises from zt_band.

    Returns all exercises loaded from .ztex files in the exercises directory.
    """
    params = {}
    if tags:
        params["tags"] = tags
    if difficulty:
        params["difficulty"] = difficulty

    path = "/exercises"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        path = f"{path}?{query}"

    data = await _proxy_get(path)
    return [Exercise(**ex) for ex in data]


@router.post("/generate", response_model=ClipBundle)
async def generate_clip(request: GenerateRequest) -> ClipBundle:
    """Generate a new clip bundle from the given parameters.

    Creates a 4-file bundle:
    - clip.mid: MIDI file
    - clip.tags.json: Clip metadata tags
    - clip.coach.json: Practice coaching hints
    - clip.runlog.json: Generation parameters and seed
    """
    data = await _proxy_post("/generate", request.model_dump())
    return ClipBundle(**data)


@router.get("/bundles/{clip_id}", response_model=ClipBundle)
async def get_bundle(clip_id: str) -> ClipBundle:
    """Retrieve a previously generated clip bundle by ID."""
    data = await _proxy_get(f"/bundle/{clip_id}")
    return ClipBundle(**data)


@router.get("/tags", response_model=List[str])
async def list_tags() -> List[str]:
    """List all unique tags across all exercises.

    Useful for building filter UIs.
    """
    data = await _proxy_get("/tags")
    return data


@router.get("/zones", response_model=ZoneInfo)
async def get_zones() -> ZoneInfo:
    """Get tritone zone theory data.

    Returns the zone classification system and tritone pairs used
    by zt_band for practice pattern generation.
    """
    # Zone theory is static — can be served without sg-agentd
    return ZoneInfo(
        zones=[
            "ZONE_I",    # Tonic area
            "ZONE_II",   # Subdominant area
            "ZONE_III",  # Dominant area
            "ZONE_IV",   # Tritone area
        ],
        tritone_pairs={
            "C": "F#/Gb",
            "G": "Db",
            "D": "Ab",
            "A": "Eb",
            "E": "Bb",
            "B": "F",
            "F#": "C",
            "Db": "G",
            "Ab": "D",
            "Eb": "A",
            "Bb": "E",
            "F": "B",
        },
        description=(
            "Tritone substitution zones define harmonic relationships. "
            "Each zone groups chords by their function (tonic, subdominant, dominant). "
            "Tritone pairs are keys separated by 6 semitones that share dominant function."
        )
    )
