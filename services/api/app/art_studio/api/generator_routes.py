"""
Generator Routes - Bundle 31.0.2

API for parametric generators.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.generator_requests import (
    GeneratorListResponse,
    GeneratorGenerateRequest,
    GeneratorGenerateResponse,
)
from ..services.generators import list_generators, generate_spec, get_generator


router = APIRouter(
    prefix="/api/art/generators",
    tags=["art_studio_generators"],
)


@router.get("", response_model=GeneratorListResponse)
async def list_available_generators() -> GeneratorListResponse:
    """List all available generators with their parameter hints."""
    generators = list_generators()
    return GeneratorListResponse(generators=generators)


@router.post("/{generator_key}/generate", response_model=GeneratorGenerateResponse)
async def generate_rosette_spec(
    generator_key: str,
    req: GeneratorGenerateRequest,
) -> GeneratorGenerateResponse:
    """
    Generate a RosetteParamSpec using the specified generator.

    The generator_key should match a registered generator (e.g., "basic_rings@1").
    """
    fn = get_generator(generator_key)
    if fn is None:
        raise HTTPException(
            status_code=404,
            detail=f"Generator not found: {generator_key}"
        )

    try:
        response = generate_spec(
            generator_key=generator_key,
            outer_diameter_mm=req.outer_diameter_mm,
            inner_diameter_mm=req.inner_diameter_mm,
            params=req.params,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
