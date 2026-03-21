"""
Wood Grading Router - Visual Wood Assessment (E-4)

POST /api/ai/wood-grading/analyze
Returns visual description only (grain count, figure type, color uniformity).
Does NOT return acoustic grades - that requires Tap Tone Analyzer.

DATE: March 2026
"""
from __future__ import annotations

import base64
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...ai.transport.vision_client import get_vision_client, VisionClientError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/wood-grading", tags=["AI", "Wood Assessment"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class WoodVisualAnalysisRequest(BaseModel):
    """Request for visual wood analysis."""
    image_base64: str = Field(..., description="Base64 encoded image data")
    wood_species: Optional[str] = Field(None, description="Known wood species (optional)")


class WoodVisualAnalysisResponse(BaseModel):
    """Visual observations only - no acoustic grading."""
    ok: bool = True
    observations: str = Field(..., description="Natural language description of wood surface")
    grain_spacing_estimate: str = Field(..., description="Grain line density (tight/medium/wide)")
    grain_straightness: str = Field(..., description="Grain orientation (straight/slight runout/significant runout)")
    figure_type: str = Field(..., description="Visual figure pattern (plain/quilted/flamed/birdseye/none)")
    color_uniformity: str = Field(..., description="Color consistency (uniform/slight variation/significant variation)")
    surface_anomalies: list[str] = Field(default_factory=list, description="Visible defects or features")
    confidence: str = Field(..., description="Assessment confidence (high/medium/low)")
    note: str = Field(
        default="Visual assessment only. For acoustic properties (density, stiffness, Q factor), use the Tap Tone Analyzer.",
        description="Reminder about acoustic grading"
    )


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

VISUAL_ASSESSMENT_PROMPT = """Analyze this wood surface image and provide visual observations only.
Do NOT assign quality grades or make acoustic predictions - those require physical measurement.

Describe what you observe:
1. Grain spacing: Count approximate grain lines per inch if visible. Categorize as tight (>20 lines/inch), medium (10-20), or wide (<10).
2. Grain straightness: Is the grain straight, or does it show runout? Estimate angle if visible.
3. Figure type: Plain, quilted, flamed/tiger stripe, birdseye, or other figure pattern. Note if none visible.
4. Color uniformity: Is the color consistent across the surface, or are there variations?
5. Surface anomalies: Note any visible features like knots, checking, mineral streaks, discoloration, or other inclusions.

Respond with JSON:
{
  "observations": "natural language summary",
  "grain_spacing_estimate": "tight|medium|wide",
  "grain_straightness": "straight|slight runout|significant runout",
  "figure_type": "plain|quilted|flamed|birdseye|other|none",
  "color_uniformity": "uniform|slight variation|significant variation",
  "surface_anomalies": ["list of observed features"],
  "confidence": "high|medium|low"
}"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=WoodVisualAnalysisResponse)
async def analyze_wood_visual(request: WoodVisualAnalysisRequest) -> WoodVisualAnalysisResponse:
    """
    Analyze wood surface image for visual characteristics.

    Returns observations only - not acoustic grades.
    For acoustic grading (density, stiffness, Q factor), use Tap Tone Analyzer.
    """
    try:
        # Decode image
        try:
            image_bytes = base64.b64decode(request.image_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")

        # Build prompt with species context if provided
        prompt = VISUAL_ASSESSMENT_PROMPT
        if request.wood_species:
            prompt = f"Wood species: {request.wood_species}\n\n" + prompt

        # Call vision API
        client = get_vision_client(provider="openai")

        if not client.is_configured:
            # Return stub response if API not configured
            logger.warning("Vision API not configured, returning stub response")
            return WoodVisualAnalysisResponse(
                ok=True,
                observations="Vision API not configured. This is a placeholder response.",
                grain_spacing_estimate="medium",
                grain_straightness="straight",
                figure_type="plain",
                color_uniformity="uniform",
                surface_anomalies=[],
                confidence="low",
            )

        response = client.analyze(
            image_bytes=image_bytes,
            prompt=prompt,
            response_format="json",
            detail="high",
        )

        # Parse response
        data = response.as_json

        return WoodVisualAnalysisResponse(
            ok=True,
            observations=data.get("observations", "No observations available"),
            grain_spacing_estimate=data.get("grain_spacing_estimate", "unknown"),
            grain_straightness=data.get("grain_straightness", "unknown"),
            figure_type=data.get("figure_type", "unknown"),
            color_uniformity=data.get("color_uniformity", "unknown"),
            surface_anomalies=data.get("surface_anomalies", []),
            confidence=data.get("confidence", "low"),
        )

    except VisionClientError as e:
        logger.error(f"Vision analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in wood visual analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.get("/health")
async def wood_grading_health() -> dict:
    """Health check for wood grading endpoint."""
    client = get_vision_client(provider="openai")
    return {
        "ok": True,
        "service": "wood-visual-assessment",
        "vision_configured": client.is_configured,
        "note": "Visual assessment only. Acoustic grading requires Tap Tone Analyzer.",
    }
