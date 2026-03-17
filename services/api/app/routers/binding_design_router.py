"""
Binding Design Orchestration Router (BIND-GAP-03)

POST /api/binding/design

Orchestrates the complete binding design workflow:
1. Resolves body_style → body outline polyline
2. Computes binding path around perimeter
3. Validates bend radius for material
4. Returns binding geometry + purfling spec + warnings
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.calculators.binding_geometry import (
    BindingMaterial,
    MINIMUM_BEND_RADII_MM,
    PURFLING_STRIP_PATTERNS,
    PurflingStripSpec,
    calculate_body_binding_path,
    polyline_length,
)

# OM-PURF-05: Corner miter analysis
from app.cam.binding import calculate_corner_miters

router = APIRouter()

Pt2D = Tuple[float, float]


# =============================================================================
# BODY OUTLINE RESOLVER
# =============================================================================

# Path to body outlines JSON
BODY_OUTLINES_PATH = Path(__file__).parent.parent / "instrument_geometry" / "body" / "body_outlines.json"

# Mapping of common body style aliases to canonical keys
BODY_STYLE_ALIASES: Dict[str, str] = {
    "om": "om_000",
    "om-000": "om_000",
    "om000": "om_000",
    "000": "om_000",
    "triple-o": "om_000",
    "strat": "stratocaster",
    "stratocaster": "stratocaster",
    "lp": "les_paul",
    "lespaul": "les_paul",
    "les-paul": "les_paul",
    "les_paul": "les_paul",
    "j45": "j45",
    "j-45": "j45",
    "dreadnought": "dreadnought",
    "dread": "dreadnought",
    "classical": "classical",
    "jumbo": "jumbo",
    "sg": "gibson_sg",
    "gibson-sg": "gibson_sg",
}


def _load_body_outlines() -> Dict[str, List[List[float]]]:
    """Load body outlines from JSON file."""
    if not BODY_OUTLINES_PATH.exists():
        raise RuntimeError(f"Body outlines file not found: {BODY_OUTLINES_PATH}")

    with open(BODY_OUTLINES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_body_outline(body_style: str) -> Tuple[str, List[Pt2D]]:
    """
    Resolve body_style to canonical outline polyline.

    Args:
        body_style: Body style name or alias (e.g., "om", "stratocaster")

    Returns:
        Tuple of (canonical_style_id, outline_points)

    Raises:
        HTTPException 404 if style not found
    """
    # Normalize input
    style_key = body_style.lower().strip().replace(" ", "_")

    # Try alias first
    canonical_key = BODY_STYLE_ALIASES.get(style_key, style_key)

    # Load outlines
    outlines = _load_body_outlines()

    if canonical_key not in outlines:
        available = list(outlines.keys())
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Body style '{body_style}' not found",
                "resolved_key": canonical_key,
                "available_styles": available[:10],  # First 10
                "total_available": len(available),
            }
        )

    raw_points = outlines[canonical_key]

    # Convert to tuple format
    points: List[Pt2D] = [(float(p[0]), float(p[1])) for p in raw_points]

    return canonical_key, points


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class BindingDesignRequest(BaseModel):
    """Request for binding design orchestration."""

    body_style: str = Field(
        ...,
        description="Body style name or alias (e.g., 'om', 'stratocaster', 'les_paul')"
    )
    binding_material: str = Field(
        "abs_plastic",
        description="Binding material (celluloid, abs_plastic, wood_maple, abalone_shell, etc.)"
    )
    purfling_pattern: Optional[str] = Field(
        None,
        description="Purfling pattern ID (solid_standard, herringbone_standard, spanish_wave)"
    )
    binding_width_mm: float = Field(
        2.5,
        ge=0.5,
        le=10.0,
        description="Binding width in mm"
    )
    neck_binding: bool = Field(
        False,
        description="Include neck binding in design"
    )
    headstock_binding: bool = Field(
        False,
        description="Include headstock binding in design"
    )


class BindingDesignResponse(BaseModel):
    """Response from binding design orchestration."""

    ok: bool
    body_style: str
    body_style_resolved: str
    binding_material: str
    purfling_pattern: Optional[str]

    # Body binding geometry
    body_outline_point_count: int
    body_perimeter_mm: float
    binding_path_analysis: Dict[str, Any]

    # Purfling spec (if requested)
    purfling_spec: Optional[Dict[str, Any]]

    # Neck/headstock (placeholder for now)
    neck_binding_included: bool
    headstock_binding_included: bool

    # OM-PURF-05: Corner miters
    corner_miters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of corner miter positions and angles"
    )

    # Validation
    is_manufacturable: bool
    warnings: List[str]

    # Summary
    summary: str


# =============================================================================
# ENDPOINT
# =============================================================================

@router.post("/design", response_model=BindingDesignResponse)
def design_binding(req: BindingDesignRequest) -> BindingDesignResponse:
    """
    Design binding for a guitar body.

    Orchestrates:
    1. Body style → outline resolution
    2. Binding path computation
    3. Material bend radius validation
    4. Purfling pattern lookup

    Returns complete binding design with warnings.
    """
    warnings: List[str] = []

    # 1. Resolve body style to outline
    try:
        canonical_style, outline_points = resolve_body_outline(req.body_style)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve body style: {e}"
        )

    # 2. Resolve binding material
    try:
        material = BindingMaterial(req.binding_material.lower())
    except ValueError:
        available_materials = [m.value for m in BindingMaterial]
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Unknown binding material: {req.binding_material}",
                "available_materials": available_materials,
            }
        )

    # 3. Calculate body binding path
    try:
        binding_analysis = calculate_body_binding_path(
            body_outline=outline_points,
            binding_width_mm=req.binding_width_mm,
            material=material,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Resolve purfling pattern (if requested)
    purfling_spec: Optional[Dict[str, Any]] = None
    if req.purfling_pattern:
        pattern_key = req.purfling_pattern.lower().strip()
        if pattern_key in PURFLING_STRIP_PATTERNS:
            spec: PurflingStripSpec = PURFLING_STRIP_PATTERNS[pattern_key]
            purfling_spec = spec.to_dict()
        else:
            available_patterns = list(PURFLING_STRIP_PATTERNS.keys())
            warnings.append(
                f"Purfling pattern '{req.purfling_pattern}' not found. "
                f"Available: {available_patterns}"
            )

    # 5. Collect warnings
    warnings.extend(binding_analysis.get("warnings", []))

    # 6. Neck/headstock binding (placeholder - not implemented yet)
    if req.neck_binding:
        warnings.append("Neck binding geometry not yet implemented in orchestrator")
    if req.headstock_binding:
        warnings.append("Headstock binding geometry not yet implemented in orchestrator")

    # 7. Calculate corner miters (OM-PURF-05)
    corner_miters = calculate_corner_miters(
        path=outline_points,
        binding_width_mm=req.binding_width_mm,
        corner_threshold_deg=20.0,
    )

    # 8. Build summary
    is_manufacturable = binding_analysis.get("is_manufacturable", True)
    min_radius = MINIMUM_BEND_RADII_MM.get(material, 10.0)

    summary_parts = [
        f"{canonical_style} body",
        f"{binding_analysis['total_length_mm']:.1f}mm perimeter",
        f"{material.value} binding ({min_radius}mm min bend radius)",
    ]
    if purfling_spec:
        summary_parts.append(f"{req.purfling_pattern} purfling")
    if not is_manufacturable:
        summary_parts.append("⚠️ TIGHT CURVES DETECTED")

    summary = " | ".join(summary_parts)

    return BindingDesignResponse(
        ok=True,
        body_style=req.body_style,
        body_style_resolved=canonical_style,
        binding_material=material.value,
        purfling_pattern=req.purfling_pattern,
        body_outline_point_count=len(outline_points),
        body_perimeter_mm=binding_analysis["total_length_mm"],
        binding_path_analysis=binding_analysis,
        purfling_spec=purfling_spec,
        corner_miters=corner_miters,
        neck_binding_included=req.neck_binding,
        headstock_binding_included=req.headstock_binding,
        is_manufacturable=is_manufacturable,
        warnings=warnings,
        summary=summary,
    )


@router.get("/styles")
def list_body_styles() -> Dict[str, Any]:
    """List available body styles for binding design."""
    outlines = _load_body_outlines()

    styles = []
    for key in sorted(outlines.keys()):
        points = outlines[key]
        styles.append({
            "id": key,
            "point_count": len(points),
            "aliases": [alias for alias, canonical in BODY_STYLE_ALIASES.items() if canonical == key],
        })

    return {
        "count": len(styles),
        "styles": styles,
    }


@router.get("/materials")
def list_binding_materials() -> Dict[str, Any]:
    """List available binding materials with bend radius info."""
    materials = []
    for material in BindingMaterial:
        min_radius = MINIMUM_BEND_RADII_MM.get(material, 10.0)
        materials.append({
            "id": material.value,
            "minimum_bend_radius_mm": min_radius,
        })

    return {
        "count": len(materials),
        "materials": materials,
    }


@router.get("/purfling-patterns")
def list_purfling_patterns() -> Dict[str, Any]:
    """List available purfling strip patterns."""
    patterns = []
    for key, spec in PURFLING_STRIP_PATTERNS.items():
        patterns.append(spec.to_dict())

    return {
        "count": len(patterns),
        "patterns": patterns,
    }
