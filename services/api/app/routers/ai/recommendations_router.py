"""
Recommendations Router - AI Design & Material Recommendations (E-5)

POST /api/ai/recommendations/generate
    Generate recommendations based on build preferences

GET /api/ai/recommendations/status
    Check service availability

DATE: March 2026
"""
from __future__ import annotations

import json
import logging
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...ai.transport.llm_client import get_llm_client, LLMClientError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/recommendations", tags=["AI", "Recommendations"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TonewoodRecommendation(BaseModel):
    """Single tonewood recommendation."""
    name: str
    reason: str
    score: int = Field(ge=0, le=100)


class DesignRecommendation(BaseModel):
    """Single design feature recommendation."""
    feature: str
    suggestion: str


class HardwareRecommendation(BaseModel):
    """Single hardware recommendation."""
    item: str
    recommendation: str


class RecommendationsRequest(BaseModel):
    """Request for AI recommendations."""
    build_type: str = Field(..., description="Instrument type: acoustic, classical, electric")
    target_tone: str = Field(..., description="Tonal goal: warm, balanced, bright")
    playing_style: str = Field(..., description="Playing technique: fingerstyle, strumming, flatpicking, hybrid")
    budget: str = Field(..., description="Budget tier: budget, mid, premium")


class RecommendationsResponse(BaseModel):
    """AI-generated recommendations."""
    ok: bool = True
    tonewoods: List[TonewoodRecommendation]
    design: List[DesignRecommendation]
    hardware: List[HardwareRecommendation]
    reasoning: str = Field(..., description="Brief explanation of recommendation strategy")


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

RECOMMENDATIONS_PROMPT = """You are an expert luthier AI assistant. Generate wood, design, and hardware recommendations for a guitar build.

Build preferences:
- Instrument type: {build_type}
- Target tone: {target_tone}
- Playing style: {playing_style}
- Budget: {budget}

Provide recommendations in JSON format:
{{
  "tonewoods": [
    {{"name": "Wood for part (e.g., Sitka Spruce Top)", "reason": "Why this choice suits the preferences", "score": 85-95}}
  ],
  "design": [
    {{"feature": "Body Shape", "suggestion": "Specific recommendation with reasoning"}}
  ],
  "hardware": [
    {{"item": "Component name", "recommendation": "Specific product or material"}}
  ],
  "reasoning": "Brief summary of overall recommendation strategy"
}}

Include 3-5 tonewood recommendations (top, back/sides, neck, fingerboard, bridge).
Include 4-6 design recommendations (body shape, scale length, bracing, soundhole, finish).
Include 3-4 hardware recommendations (tuners, nut/saddle, bridge pins, strings).

Scores should reflect confidence and suitability (85-98 range typical)."""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=RecommendationsResponse)
async def generate_recommendations(request: RecommendationsRequest) -> RecommendationsResponse:
    """
    Generate AI recommendations based on build preferences.

    Uses LLM to analyze preferences and generate contextual recommendations.
    """
    try:
        client = get_llm_client("anthropic")

        if not client.is_configured:
            client = get_llm_client("openai")

        if not client.is_configured:
            raise HTTPException(
                status_code=503,
                detail="AI service not configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.",
            )

        # Build prompt
        prompt = RECOMMENDATIONS_PROMPT.format(
            build_type=request.build_type,
            target_tone=request.target_tone,
            playing_style=request.playing_style,
            budget=request.budget,
        )

        response = client.request_text(
            prompt=prompt,
            system_prompt="You are a master luthier providing expert recommendations. Always respond with valid JSON.",
            temperature=0.7,
            max_tokens=2048,
        )

        # Parse JSON response
        content = response.content.strip()

        # Extract JSON from response
        json_match = re.search(r"\{[\s\S]*\}", content)
        if not json_match:
            raise ValueError("No JSON found in response")

        parsed = json.loads(json_match.group())

        logger.info(
            f"Recommendations generated: type={request.build_type}, "
            f"tone={request.target_tone}, style={request.playing_style}, "
            f"budget={request.budget}"
        )

        return RecommendationsResponse(
            ok=True,
            tonewoods=[TonewoodRecommendation(**tw) for tw in parsed.get("tonewoods", [])],
            design=[DesignRecommendation(**d) for d in parsed.get("design", [])],
            hardware=[HardwareRecommendation(**h) for h in parsed.get("hardware", [])],
            reasoning=parsed.get("reasoning", "Recommendations based on provided preferences."),
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 503 from unconfigured client)
        raise
    except LLMClientError as e:
        logger.error(f"LLM client error: {e}")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        raise HTTPException(status_code=502, detail="Failed to parse AI response")
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def recommendations_status() -> dict:
    """Check recommendations service status."""
    anthropic_configured = False
    openai_configured = False

    try:
        anthropic_client = get_llm_client("anthropic")
        anthropic_configured = anthropic_client.is_configured
    except Exception:
        pass

    try:
        openai_client = get_llm_client("openai")
        openai_configured = openai_client.is_configured
    except Exception:
        pass

    return {
        "ok": anthropic_configured or openai_configured,
        "providers": {
            "anthropic": {"configured": anthropic_configured},
            "openai": {"configured": openai_configured},
        },
    }


__all__ = ["router"]
