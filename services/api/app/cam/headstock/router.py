"""
Headstock Inlay Prompt Router

API endpoints for AI-assisted headstock inlay design generation.
Exposes the 11 headstock inlay templates and custom prompt generation.

Resolves: INLAY-01 (No headstock inlay router)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .inlay_prompts import (
    HeadstockStyle,
    InlayDesign,
    HEADSTOCK_TEMPLATES,
    INLAY_TEMPLATES,
    WOOD_DESCRIPTIONS,
    HEADSTOCK_SHAPES,
    INLAY_DESIGNS,
    generate_headstock_prompt,
    generate_inlay_prompt,
    get_template_prompt,
    list_available_options,
)

router = APIRouter(
    prefix="/api/cam/headstock/inlay",
    tags=["Headstock Inlay"],
)


# --------------------------------------------------------------------- #
# Request/Response Models
# --------------------------------------------------------------------- #

class HeadstockPromptRequest(BaseModel):
    """Request for custom headstock inlay prompt generation."""

    style: str = Field(
        "les_paul",
        description="Headstock style (les_paul, stratocaster, prs, etc.)"
    )
    headstock_wood: str = Field(
        "mahogany",
        description="Wood species for headstock (mahogany, rosewood, ebony, etc.)"
    )
    inlay_design: str = Field(
        "hummingbird",
        description="Inlay design (hummingbird, dove, dragon, tree_of_life, etc.)"
    )
    inlay_material: str = Field(
        "mother_of_pearl",
        description="Inlay material (mother_of_pearl, abalone, maple, etc.)"
    )
    tuner_style: str = Field(
        "chrome vintage",
        description="Tuner style description"
    )
    additional_details: Optional[str] = Field(
        None,
        description="Additional custom details to include in the prompt"
    )
    background: str = Field(
        "dark gradient studio",
        description="Background style for the image"
    )
    include_strings: bool = Field(
        True,
        description="Include guitar strings in the image"
    )


class InlayPromptRequest(BaseModel):
    """Request for isolated inlay piece prompt generation."""

    design: str = Field(
        "hummingbird",
        description="Inlay design name"
    )
    material: str = Field(
        "mother_of_pearl",
        description="Inlay material"
    )
    size_description: str = Field(
        "approximately 2 inches tall",
        description="Size description for the inlay"
    )
    style_notes: Optional[str] = Field(
        None,
        description="Additional style notes"
    )


class PromptResponse(BaseModel):
    """Response containing the generated prompt."""

    prompt: str = Field(..., description="Generated AI image prompt")
    template_used: Optional[str] = Field(
        None,
        description="Template name if a template was used"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters used to generate the prompt"
    )


class TemplateInfo(BaseModel):
    """Information about a headstock template."""

    name: str
    description: str
    style: str
    headstock_wood: str
    inlay_design: str
    inlay_material: str
    tuner_style: str


class OptionsResponse(BaseModel):
    """Response containing available options."""

    headstock_styles: List[str]
    inlay_designs: List[str]
    wood_species: List[str]
    templates: List[str]


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #

@router.get("/options", response_model=OptionsResponse)
def get_options() -> OptionsResponse:
    """
    List all available options for headstock inlay generation.

    Returns lists of:
    - Headstock styles (les_paul, stratocaster, prs, etc.)
    - Inlay designs (hummingbird, dove, dragon, etc.)
    - Wood species (mahogany, rosewood, maple, etc.)
    - Pre-built templates
    """
    options = list_available_options()
    return OptionsResponse(**options)


@router.get("/templates", response_model=List[TemplateInfo])
def list_templates() -> List[TemplateInfo]:
    """
    List all pre-built headstock templates.

    Returns 11 curated template combinations including:
    - Gibson Hummingbird Style
    - Gibson Dove Style
    - PRS Custom Eagle
    - Tree of Life
    - Dragon Master
    - And more...
    """
    result = []
    for name, template in HEADSTOCK_TEMPLATES.items():
        result.append(TemplateInfo(
            name=name,
            description=template.get("description", ""),
            style=template["style"],
            headstock_wood=template["headstock_wood"],
            inlay_design=template["inlay_design"],
            inlay_material=template["inlay_material"],
            tuner_style=template.get("tuner_style", "chrome vintage"),
        ))
    return result


@router.get("/templates/{template_name}", response_model=PromptResponse)
def get_template(template_name: str) -> PromptResponse:
    """
    Get a prompt from a pre-built template.

    Templates are curated combinations of headstock style, wood,
    inlay design, and material that work well together.
    """
    if template_name not in HEADSTOCK_TEMPLATES:
        available = list(HEADSTOCK_TEMPLATES.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available: {available}"
        )

    prompt = get_template_prompt(template_name)
    template = HEADSTOCK_TEMPLATES[template_name]

    return PromptResponse(
        prompt=prompt,
        template_used=template_name,
        parameters={
            "style": template["style"],
            "headstock_wood": template["headstock_wood"],
            "inlay_design": template["inlay_design"],
            "inlay_material": template["inlay_material"],
        }
    )


@router.post("/generate", response_model=PromptResponse)
def generate_custom_prompt(req: HeadstockPromptRequest) -> PromptResponse:
    """
    Generate a custom headstock inlay prompt.

    Allows full customization of headstock style, wood, inlay design,
    material, tuners, and additional details.

    The generated prompt is suitable for AI image generators like
    Stable Diffusion, DALL-E, or Midjourney.
    """
    # Validate style
    valid_styles = [s.value for s in HeadstockStyle]
    if req.style not in valid_styles and req.style not in HEADSTOCK_SHAPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown headstock style '{req.style}'. Valid: {valid_styles}"
        )

    # Validate inlay design
    valid_designs = [d.value for d in InlayDesign]
    if req.inlay_design not in valid_designs and req.inlay_design not in INLAY_DESIGNS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown inlay design '{req.inlay_design}'. Valid: {valid_designs}"
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

    return PromptResponse(
        prompt=prompt,
        template_used=None,
        parameters=req.model_dump()
    )


@router.post("/generate-inlay", response_model=PromptResponse)
def generate_inlay_piece_prompt(req: InlayPromptRequest) -> PromptResponse:
    """
    Generate a prompt for an isolated inlay piece.

    This creates a prompt for photographing/generating an inlay piece
    by itself (not installed in a headstock), useful for:
    - Inlay design previews
    - Material selection
    - CAM cutting templates
    """
    # Validate design
    valid_designs = [d.value for d in InlayDesign]
    if req.design not in valid_designs and req.design not in INLAY_DESIGNS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown inlay design '{req.design}'. Valid: {valid_designs}"
        )

    prompt = generate_inlay_prompt(
        design=req.design,
        material=req.material,
        size_description=req.size_description,
        style_notes=req.style_notes,
    )

    return PromptResponse(
        prompt=prompt,
        template_used=None,
        parameters=req.model_dump()
    )


@router.get("/inlay-templates", response_model=Dict[str, Any])
def list_inlay_templates() -> Dict[str, Any]:
    """
    List available isolated inlay templates.

    These are simpler templates for inlay pieces alone,
    not installed in a headstock.
    """
    return {
        "templates": {
            name: {
                "design": t["design"],
                "material": t["material"],
                "description": t["description"],
            }
            for name, t in INLAY_TEMPLATES.items()
        }
    }


@router.get("/woods", response_model=Dict[str, str])
def list_wood_descriptions() -> Dict[str, str]:
    """
    List all wood species with their visual descriptions.

    Includes both headstock woods (dark) and inlay materials (light),
    as well as figured woods and shell materials.
    """
    return WOOD_DESCRIPTIONS


@router.get("/designs/{design_name}", response_model=Dict[str, str])
def get_design_description(design_name: str) -> Dict[str, str]:
    """
    Get the description for a specific inlay design.

    Returns the detailed prompt description used for AI generation.
    """
    if design_name not in INLAY_DESIGNS:
        available = list(INLAY_DESIGNS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Design '{design_name}' not found. Available: {available}"
        )

    return {
        "design": design_name,
        "description": INLAY_DESIGNS[design_name].strip()
    }


@router.get("/styles/{style_name}", response_model=Dict[str, str])
def get_style_description(style_name: str) -> Dict[str, str]:
    """
    Get the description for a specific headstock style.

    Returns the detailed shape description used for AI generation.
    """
    if style_name not in HEADSTOCK_SHAPES:
        available = list(HEADSTOCK_SHAPES.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Style '{style_name}' not found. Available: {available}"
        )

    return {
        "style": style_name,
        "description": HEADSTOCK_SHAPES[style_name].strip()
    }


@router.get("/info")
def get_info() -> Dict[str, Any]:
    """Get headstock inlay module information."""
    return {
        "module": "headstock_inlay",
        "description": "AI-assisted headstock inlay design prompt generation",
        "template_count": len(HEADSTOCK_TEMPLATES),
        "design_count": len(INLAY_DESIGNS),
        "wood_count": len(WOOD_DESCRIPTIONS),
        "style_count": len(HEADSTOCK_SHAPES),
        "features": [
            "11 curated headstock templates",
            "12+ inlay designs (birds, floral, geometric, mythical)",
            "17 wood species with visual descriptions",
            "11 headstock styles (Gibson, Fender, PRS, etc.)",
            "Custom prompt generation",
            "Isolated inlay piece prompts",
        ],
        "resolves": ["INLAY-01"],
    }
