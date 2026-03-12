# services/api/app/art_studio/headstock_inlay_router.py

"""
Art Studio Headstock Inlay Router

INLAY-01: Provides API endpoints for headstock inlay design and AI prompt generation.
Exposes headstock styles, inlay designs, materials, and pre-built templates from
the orphaned inlay_prompts.py module.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..cam.headstock.inlay_prompts import (
    HeadstockStyle,
    InlayDesign,
    HEADSTOCK_SHAPES,
    INLAY_DESIGNS,
    WOOD_DESCRIPTIONS,
    HEADSTOCK_TEMPLATES,
    INLAY_TEMPLATES,
    generate_headstock_prompt,
    generate_inlay_prompt,
    get_template_prompt,
    list_available_options,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/art-studio/headstock-inlay",
    tags=["Art Studio - Headstock Inlay"],
)


# --------------------------------------------------------------------- #
# Request/Response Models
# --------------------------------------------------------------------- #

class HeadstockStyleInfo(BaseModel):
    """Information about a headstock style."""
    id: str
    name: str
    description: str


class InlayDesignInfo(BaseModel):
    """Information about an inlay design."""
    id: str
    name: str
    description: str


class MaterialInfo(BaseModel):
    """Information about a wood/material option."""
    id: str
    description: str
    category: str = Field(description="dark_wood, light_wood, figured, or accent")


class TemplateInfo(BaseModel):
    """Information about a headstock inlay template."""
    id: str
    name: str
    description: str
    headstock_style: str
    inlay_design: str
    headstock_wood: str
    inlay_material: str
    tuner_style: str


class HeadstockPromptRequest(BaseModel):
    """Request for headstock inlay prompt generation."""

    style: str = Field(
        default="les_paul",
        description="Headstock style (les_paul, stratocaster, prs, etc.)"
    )
    headstock_wood: str = Field(
        default="mahogany",
        description="Wood species for headstock face"
    )
    inlay_design: str = Field(
        default="dove",
        description="Inlay design (hummingbird, dove, eagle, tree_of_life, etc.)"
    )
    inlay_material: str = Field(
        default="mother_of_pearl",
        description="Inlay material (mother_of_pearl, abalone, maple, etc.)"
    )
    tuner_style: str = Field(
        default="chrome vintage",
        description="Tuner hardware style"
    )
    background: str = Field(
        default="dark gradient studio",
        description="Background for generated image"
    )
    include_strings: bool = Field(
        default=True,
        description="Include guitar strings in the image"
    )
    additional_details: Optional[str] = Field(
        default=None,
        description="Additional prompt details"
    )


class HeadstockPromptResponse(BaseModel):
    """Response with generated prompt."""
    prompt: str
    style: str
    inlay_design: str
    headstock_wood: str
    inlay_material: str
    prompt_length: int


class InlayOnlyPromptRequest(BaseModel):
    """Request for isolated inlay piece prompt."""

    design: str = Field(
        default="hummingbird",
        description="Inlay design type"
    )
    material: str = Field(
        default="mother_of_pearl",
        description="Inlay material"
    )
    size_description: str = Field(
        default="approximately 2 inches tall",
        description="Size of the inlay piece"
    )
    style_notes: Optional[str] = Field(
        default=None,
        description="Additional style notes"
    )


class AvailableOptionsResponse(BaseModel):
    """All available options for headstock generation."""
    headstock_styles: List[str]
    inlay_designs: List[str]
    wood_species: List[str]
    templates: List[str]


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #

@router.get("/styles", response_model=List[HeadstockStyleInfo])
def list_headstock_styles() -> List[HeadstockStyleInfo]:
    """
    List available headstock styles.

    Returns all supported headstock shapes with descriptions:
    - les_paul (Gibson open-book)
    - stratocaster (Fender 6-in-line)
    - telecaster (Fender variant)
    - classical (slotted)
    - acoustic (Martin-style)
    - prs (Paul Reed Smith)
    - explorer, flying_v, sg, jazz
    """
    results = []
    for style in HeadstockStyle:
        desc = HEADSTOCK_SHAPES.get(style.value, "").strip()
        # Truncate to first sentence for summary
        summary = desc.split('.')[0] + '.' if desc else f"{style.value} headstock"
        results.append(HeadstockStyleInfo(
            id=style.value,
            name=style.value.replace('_', ' ').title(),
            description=summary,
        ))
    return results


@router.get("/styles/{style_id}")
def get_headstock_style(style_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific headstock style.

    Returns the full shape description and configuration.
    """
    # Validate style exists
    valid_styles = [s.value for s in HeadstockStyle]
    if style_id not in valid_styles:
        raise HTTPException(
            status_code=404,
            detail=f"Style '{style_id}' not found. Available: {valid_styles}"
        )

    return {
        "id": style_id,
        "name": style_id.replace('_', ' ').title(),
        "description": HEADSTOCK_SHAPES.get(style_id, "").strip(),
    }


@router.get("/designs", response_model=List[InlayDesignInfo])
def list_inlay_designs() -> List[InlayDesignInfo]:
    """
    List available inlay designs.

    Returns all supported inlay designs with descriptions:
    - Birds: hummingbird, dove, eagle, phoenix, owl, swallow
    - Floral: rose, vine, tree_of_life, lotus, cherry_blossom, acanthus
    - Geometric: diamond, split_block, crown, torch, star, celtic_knot
    - Other: dragon, koi, skull, custom
    """
    results = []
    for design in InlayDesign:
        desc = INLAY_DESIGNS.get(design.value, "").strip()
        # Truncate to first sentence for summary
        summary = desc.split('.')[0] + '.' if desc else f"{design.value} design"
        results.append(InlayDesignInfo(
            id=design.value,
            name=design.value.replace('_', ' ').title(),
            description=summary,
        ))
    return results


@router.get("/designs/{design_id}")
def get_inlay_design(design_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific inlay design.
    """
    valid_designs = [d.value for d in InlayDesign]
    if design_id not in valid_designs:
        raise HTTPException(
            status_code=404,
            detail=f"Design '{design_id}' not found. Available: {valid_designs}"
        )

    return {
        "id": design_id,
        "name": design_id.replace('_', ' ').title(),
        "description": INLAY_DESIGNS.get(design_id, "").strip(),
    }


@router.get("/materials", response_model=List[MaterialInfo])
def list_materials() -> List[MaterialInfo]:
    """
    List available wood species and materials for inlay.

    Categories:
    - dark_wood: mahogany, rosewood, ebony, walnut, wenge, koa, ziricote
    - light_wood: maple, holly, boxwood, spruce, ash
    - figured: flame_maple, quilted_maple, birdseye_maple, spalted_maple
    - accent: abalone, mother_of_pearl, paua, goldleaf
    """
    dark_woods = {"mahogany", "rosewood", "ebony", "walnut", "wenge", "koa", "ziricote"}
    light_woods = {"maple", "holly", "boxwood", "spruce", "ash"}
    figured = {"flame_maple", "quilted_maple", "birdseye_maple", "spalted_maple"}
    accents = {"abalone", "mother_of_pearl", "paua", "goldleaf"}

    results = []
    for material_id, description in WOOD_DESCRIPTIONS.items():
        if material_id in dark_woods:
            category = "dark_wood"
        elif material_id in light_woods:
            category = "light_wood"
        elif material_id in figured:
            category = "figured"
        elif material_id in accents:
            category = "accent"
        else:
            category = "other"

        results.append(MaterialInfo(
            id=material_id,
            description=description,
            category=category,
        ))

    return sorted(results, key=lambda x: (x.category, x.id))


@router.get("/templates", response_model=List[TemplateInfo])
def list_templates() -> List[TemplateInfo]:
    """
    List pre-built headstock inlay templates.

    Templates are curated combinations of headstock style, wood,
    inlay design, and material that work well together.
    """
    results = []
    for template_id, template in HEADSTOCK_TEMPLATES.items():
        results.append(TemplateInfo(
            id=template_id,
            name=template.get("name", template_id),
            description=template.get("description", ""),
            headstock_style=template.get("style", "les_paul"),
            inlay_design=template.get("inlay_design", ""),
            headstock_wood=template.get("headstock_wood", ""),
            inlay_material=template.get("inlay_material", ""),
            tuner_style=template.get("tuner_style", "chrome vintage"),
        ))
    return results


@router.get("/templates/{template_id}")
def get_template(template_id: str) -> Dict[str, Any]:
    """
    Get a specific template by ID.

    Returns the full template configuration and generated prompt.
    """
    if template_id not in HEADSTOCK_TEMPLATES:
        available = list(HEADSTOCK_TEMPLATES.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_id}' not found. Available: {available}"
        )

    template = HEADSTOCK_TEMPLATES[template_id]
    prompt = get_template_prompt(template_id)

    return {
        "id": template_id,
        "template": template,
        "prompt": prompt,
        "prompt_length": len(prompt),
    }


@router.post("/generate-prompt", response_model=HeadstockPromptResponse)
def generate_prompt(req: HeadstockPromptRequest) -> HeadstockPromptResponse:
    """
    Generate an AI image prompt for a headstock inlay design.

    Accepts headstock style, woods, inlay design, and materials.
    Returns a detailed prompt suitable for image generation AI.
    """
    try:
        # Validate style
        valid_styles = [s.value for s in HeadstockStyle]
        if req.style not in valid_styles and req.style != "custom":
            raise HTTPException(
                status_code=422,
                detail=f"Invalid style '{req.style}'. Valid: {valid_styles}"
            )

        # Validate inlay design
        valid_designs = [d.value for d in InlayDesign]
        if req.inlay_design not in valid_designs and req.inlay_design != "custom":
            raise HTTPException(
                status_code=422,
                detail=f"Invalid inlay design '{req.inlay_design}'. Valid: {valid_designs}"
            )

        prompt = generate_headstock_prompt(
            style=req.style,
            headstock_wood=req.headstock_wood,
            inlay_design=req.inlay_design,
            inlay_material=req.inlay_material,
            tuner_style=req.tuner_style,
            additional_details=req.additional_details,
            background=req.background,
            include_strings=req.include_strings,
        )

        return HeadstockPromptResponse(
            prompt=prompt,
            style=req.style,
            inlay_design=req.inlay_design,
            headstock_wood=req.headstock_wood,
            inlay_material=req.inlay_material,
            prompt_length=len(prompt),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Headstock prompt generation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-inlay-prompt")
def generate_isolated_inlay_prompt(req: InlayOnlyPromptRequest) -> Dict[str, Any]:
    """
    Generate an AI prompt for an isolated inlay piece (not installed).

    Useful for generating reference images of the inlay piece itself
    before installation into a headstock.
    """
    try:
        prompt = generate_inlay_prompt(
            design=req.design,
            material=req.material,
            size_description=req.size_description,
            style_notes=req.style_notes,
        )

        return {
            "prompt": prompt,
            "design": req.design,
            "material": req.material,
            "prompt_length": len(prompt),
        }

    except Exception as e:
        logger.exception("Inlay prompt generation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options", response_model=AvailableOptionsResponse)
def get_all_options() -> AvailableOptionsResponse:
    """
    Get all available options in a single call.

    Convenience endpoint for populating UI dropdowns.
    """
    options = list_available_options()
    return AvailableOptionsResponse(**options)


@router.get("/inlay-templates")
def list_inlay_only_templates() -> List[Dict[str, Any]]:
    """
    List templates for isolated inlay pieces.

    These are simpler templates for generating inlay piece images
    without the full headstock context.
    """
    results = []
    for template_id, template in INLAY_TEMPLATES.items():
        results.append({
            "id": template_id,
            "design": template.get("design", ""),
            "material": template.get("material", ""),
            "description": template.get("description", ""),
        })
    return results
