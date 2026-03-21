"""Defect Detection Router (Session E-3) — Visual Observation Endpoint

AI-powered wood surface observation. Returns descriptive observations
without assigning quality grades — describe what you see, not judge.

Endpoints:
    POST /api/ai/defects/analyze — Analyze wood surface image

Uses vision_client.py (GPT-4o Vision) to analyze uploaded images.
"""

from __future__ import annotations

import base64
import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...ai.transport.vision_client import (
    get_vision_client,
    VisionClientError,
    VisionAuthError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ai/defects",
    tags=["AI Defects", "Vision", "Wood Analysis"],
)


# =============================================================================
# SCHEMAS
# =============================================================================


class DefectAnalyzeRequest(BaseModel):
    """Request body for defect analysis endpoint."""

    image_base64: str = Field(
        ...,
        description="Base64-encoded image data (PNG, JPG, WebP)",
    )
    wood_species: Optional[str] = Field(
        None,
        description="Optional wood species hint for context (e.g., 'sitka spruce', 'mahogany')",
    )


class DefectAnalyzeResponse(BaseModel):
    """Response from defect analysis endpoint."""

    observations: str = Field(
        ...,
        description="Detailed visual observations about the wood surface",
    )
    grain_spacing_estimate: str = Field(
        ...,
        description="Estimated grain line spacing (e.g., '8-12 lines per inch')",
    )
    runout_visible: bool = Field(
        ...,
        description="Whether grain runout is visible in the image",
    )
    anomalies_detected: bool = Field(
        ...,
        description="Whether surface anomalies were detected",
    )
    confidence: str = Field(
        ...,
        description="Confidence level in observations (low, medium, high)",
    )


# =============================================================================
# PROMPT
# =============================================================================

DEFECT_OBSERVATION_PROMPT = """Describe what you observe about this wood surface. Include:
- Grain line spacing estimate (lines per inch or mm)
- Visible runout angle (if any)
- Any surface anomalies (checking, discoloration, knots, mineral streaks)
- Grain straightness assessment

Do not assign a quality grade — describe what you see.

Respond in JSON format:
{
  "observations": "detailed text description of all observations",
  "grain_spacing_estimate": "e.g., '10-14 lines per inch' or 'tight, ~1mm spacing'",
  "runout_visible": true or false,
  "anomalies_detected": true or false,
  "confidence": "low" | "medium" | "high"
}"""


def _build_prompt(wood_species: Optional[str]) -> str:
    """Build the analysis prompt, optionally including wood species context."""
    if wood_species:
        return f"Wood species hint: {wood_species}\n\n{DEFECT_OBSERVATION_PROMPT}"
    return DEFECT_OBSERVATION_PROMPT


def _parse_response(raw: Any) -> Dict[str, Any]:
    """Parse and validate the vision response."""
    # Handle dict response
    if isinstance(raw, dict):
        return {
            "observations": str(raw.get("observations", "No observations available")),
            "grain_spacing_estimate": str(raw.get("grain_spacing_estimate", "Unable to estimate")),
            "runout_visible": bool(raw.get("runout_visible", False)),
            "anomalies_detected": bool(raw.get("anomalies_detected", False)),
            "confidence": str(raw.get("confidence", "low")),
        }

    # Handle string response - try to extract JSON
    if isinstance(raw, str):
        # Try to find JSON in response
        json_match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
        if json_match:
            import json

            try:
                parsed = json.loads(json_match.group())
                return _parse_response(parsed)
            except json.JSONDecodeError:
                pass

        # Fallback: treat entire response as observations
        return {
            "observations": raw,
            "grain_spacing_estimate": "Unable to parse",
            "runout_visible": False,
            "anomalies_detected": False,
            "confidence": "low",
        }

    # Unknown type
    return {
        "observations": "Unable to parse response",
        "grain_spacing_estimate": "Unknown",
        "runout_visible": False,
        "anomalies_detected": False,
        "confidence": "low",
    }


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/analyze", response_model=DefectAnalyzeResponse)
async def analyze_defects(request: DefectAnalyzeRequest) -> DefectAnalyzeResponse:
    """
    Analyze a wood surface image for visual observations.

    Returns descriptive observations about grain, runout, and anomalies.
    Does NOT assign quality grades — describes what is visible.
    """
    # Decode image
    try:
        # Handle data URL prefix if present
        image_data = request.image_base64
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        image_bytes = base64.b64decode(image_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")

    if len(image_bytes) < 100:
        raise HTTPException(status_code=400, detail="Image data too small")

    if len(image_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 20MB)")

    # Get vision client
    try:
        client = get_vision_client("openai")

        if not client.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Vision service not configured. Set OPENAI_API_KEY.",
            )

        # Build prompt with optional species context
        prompt = _build_prompt(request.wood_species)

        # Analyze image
        response = client.analyze(
            image_bytes=image_bytes,
            prompt=prompt,
            response_format="json",
            detail="high",  # High detail for wood grain analysis
        )

        # Parse response
        parsed = _parse_response(response.content)

        logger.info(
            f"Defect analysis: species={request.wood_species or 'unspecified'}, "
            f"anomalies={parsed['anomalies_detected']}, "
            f"runout={parsed['runout_visible']}, "
            f"confidence={parsed['confidence']}"
        )

        return DefectAnalyzeResponse(**parsed)

    except VisionAuthError:
        raise HTTPException(status_code=503, detail="Vision API authentication failed")
    except VisionClientError as e:
        logger.error(f"Vision client error: {e}")
        raise HTTPException(status_code=502, detail=f"Vision analysis failed: {e}")


@router.get("/status")
async def defect_status() -> Dict[str, Any]:
    """Check defect detection service status."""
    try:
        client = get_vision_client("openai")
        configured = client.is_configured
    except Exception:
        configured = False

    return {
        "ok": configured,
        "provider": "openai",
        "model": "gpt-4o",
        "configured": configured,
    }


__all__ = ["router"]
