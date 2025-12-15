"""
AI Graphics API Routes - Main Suggestion Endpoints

Provides:
- POST /api/ai/graphics/suggest: Generate AI rosette suggestions
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.ai_schemas import (
    AiRosettePromptInput,
    AiRosetteSuggestionBatch,
)
from ..services.ai_parameter_suggester import suggest_rosette_parameters


router = APIRouter(
    prefix="/api/ai/graphics",
    tags=["ai_graphics"],
)


@router.post("/suggest", response_model=AiRosetteSuggestionBatch)
async def suggest_rosette_designs(
    req: AiRosettePromptInput,
) -> AiRosetteSuggestionBatch:
    """
    Generate AI rosette suggestions with RMOS feasibility scoring.
    
    Features:
    - LLM-based parameter generation from natural language prompt
    - RMOS feasibility scoring with ring-level diagnostics
    - Optional refinement rounds (0-3) for iterative improvement
    - Session-based deduplication to avoid repeating designs
    
    Args:
        req: AiRosettePromptInput with prompt, count, presets, and refinement controls
    
    Returns:
        AiRosetteSuggestionBatch with scored and sorted suggestions
    """
    try:
        batch = suggest_rosette_parameters(req)
        return batch
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI suggestion generation failed: {str(e)}"
        )


@router.get("/health")
async def health_check() -> dict:
    """Health check for AI Graphics service."""
    return {"status": "ok", "service": "ai_graphics"}
