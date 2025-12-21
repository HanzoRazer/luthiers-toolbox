"""
Rosette Pattern Routes - Phase 5 Consolidation

Traditional Matrix + Modern Parametric pattern generation methods.

Migrated from:
    - routers/rosette_pattern_router.py

Endpoints:
    GET  /status               - Check pattern generator availability
    GET  /patterns             - List available preset patterns
    GET  /patterns/{id}        - Get pattern details
    POST /generate_traditional - Traditional matrix method
    POST /generate_modern      - Modern parametric method
    POST /export               - Export pattern in various formats

Target: TXRX Labs January 2026 presentation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
import json
from pathlib import Path

router = APIRouter(
    prefix="/api/art/rosette/pattern",
    tags=["art_studio_rosette_pattern"],
)

# Try to import pattern generator, gracefully degrade if unavailable
GENERATOR_AVAILABLE = False
try:
    from ...cam.rosette.pattern_generator import (
        RosettePatternEngine,
        MatrixFormula,
        RosetteSpec,
        RingSpec,
        PatternType,
        MaterialType,
        OutputFormat,
    )
    GENERATOR_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not load pattern_generator: {e}")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MatrixRow(BaseModel):
    """Single row in a matrix formula."""
    materials: List[str] = Field(..., description="Material codes for each column (e.g., ['B', 'W', 'B'])")


class TraditionalPatternRequest(BaseModel):
    """Request for traditional matrix-based pattern generation."""
    preset_id: Optional[str] = Field(None, description="Use preset pattern (e.g., 'classic_rope_5x9')")
    custom_matrix: Optional[List[List[str]]] = Field(None, description="Custom matrix rows")
    name: str = Field("Custom Pattern", description="Pattern name")
    chip_length_mm: float = Field(2.0, description="Length of each chip/tile in mm")
    waste_factor: float = Field(0.15, description="Material waste percentage (0.15 = 15%)")


class RingDefinition(BaseModel):
    """Single ring definition for modern parametric method."""
    inner_diameter_mm: float = Field(..., ge=0)
    outer_diameter_mm: float = Field(..., ge=0)
    pattern_type: Literal["solid", "rope", "herringbone", "checkerboard"] = "solid"
    primary_color: str = "black"
    secondary_color: str = "white"
    segment_count: Optional[int] = Field(None, description="Number of segments for patterns")


class ModernPatternRequest(BaseModel):
    """Request for modern parametric pattern generation."""
    name: str = Field(..., description="Pattern name")
    rings: List[RingDefinition] = Field(..., description="Ring definitions from inner to outer")
    soundhole_diameter_mm: float = Field(90.0, description="Central soundhole diameter")
    chip_length_mm: float = Field(2.0, description="Chip length for patterned rings")


class PatternExportRequest(BaseModel):
    """Request to export generated pattern."""
    pattern_data: Dict[str, Any] = Field(..., description="Pattern result data")
    formats: List[Literal["dxf", "svg", "json", "gcode"]] = Field(["dxf", "svg"], description="Export formats")
    target_units: Literal["mm", "inch"] = Field("mm", description="Output units")


class TraditionalPatternResponse(BaseModel):
    """Response with traditional pattern results."""
    formula: Dict[str, Any]
    pattern_dimensions: Dict[str, float]
    material_totals: Dict[str, int]
    cut_list: List[Dict[str, Any]]
    assembly_instructions: List[Dict[str, Any]]
    bom: Dict[str, Any]


class ModernPatternResponse(BaseModel):
    """Response with modern parametric pattern results."""
    spec: Dict[str, Any]
    paths: List[Dict[str, Any]]
    bom: Dict[str, float]
    estimated_cut_time_min: float
    dxf_content: Optional[str] = None
    svg_content: Optional[str] = None


class PatternListItem(BaseModel):
    """Single pattern in catalog."""
    id: str
    name: str
    rows: int
    columns: int
    materials: List[str]
    category: str
    notes: Optional[str] = None


class PatternCatalogResponse(BaseModel):
    """Response with available patterns."""
    total_patterns: int
    categories: List[str]
    patterns: List[PatternListItem]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/status")
async def get_status():
    """Check if pattern generator is available."""
    if not GENERATOR_AVAILABLE:
        return {
            "available": False,
            "error": "Pattern generator module not loaded",
            "details": "Check that rosette pattern_generator.py is installed"
        }

    return {
        "available": True,
        "error": None,
        "features": {
            "traditional_method": True,
            "modern_parametric": True,
            "preset_patterns": True,
            "export_formats": ["dxf", "svg", "json"]
        }
    }


@router.get("/patterns", response_model=PatternCatalogResponse)
async def list_patterns(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """List available preset patterns from catalog."""
    if not GENERATOR_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Pattern generator not available"
        )

    try:
        engine = RosettePatternEngine()
        presets = engine.list_preset_matrices()

        # Load catalog to get categories
        catalog_path = Path(__file__).parent.parent.parent / "data" / "rosette_pattern_catalog.json"
        if catalog_path.exists():
            with open(catalog_path) as f:
                catalog = json.load(f)
                categories = list(catalog.get("categories", {}).keys())
        else:
            categories = ["basic", "torres", "hauser", "romanillos", "fleta"]

        # Build pattern list
        patterns = []
        for preset in presets:
            # Determine category from preset_id
            preset_category = "basic"
            for cat in categories:
                if cat in preset['id']:
                    preset_category = cat
                    break

            if category is None or preset_category == category:
                patterns.append(PatternListItem(
                    id=preset['id'],
                    name=preset['name'],
                    rows=preset['rows'],
                    columns=preset['columns'],
                    materials=preset.get('materials', ['black', 'white']),
                    category=preset_category,
                    notes=preset.get('notes')
                ))

        return PatternCatalogResponse(
            total_patterns=len(patterns),
            categories=categories,
            patterns=patterns
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list patterns: {str(e)}"
        )


@router.post("/generate_traditional", response_model=TraditionalPatternResponse)
async def generate_traditional_pattern(body: TraditionalPatternRequest):
    """Generate rosette using traditional matrix method."""
    if not GENERATOR_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Pattern generator not available"
        )

    try:
        engine = RosettePatternEngine()

        # Use preset or custom matrix
        if body.preset_id:
            result = engine.generate_traditional(
                preset_id=body.preset_id,
                chip_length_mm=body.chip_length_mm,
                waste_factor=body.waste_factor
            )
        elif body.custom_matrix:
            result = engine.generate_traditional(
                custom_matrix=body.custom_matrix,
                name=body.name,
                chip_length_mm=body.chip_length_mm,
                waste_factor=body.waste_factor
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either preset_id or custom_matrix"
            )

        return TraditionalPatternResponse(
            formula=result.formula.to_dict(),
            pattern_dimensions=result.pattern_dimensions,
            material_totals=result.material_totals,
            cut_list=[item.to_dict() for item in result.cut_list],
            assembly_instructions=[instr.to_dict() for instr in result.assembly_instructions],
            bom=result.bom
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pattern generation failed: {str(e)}"
        )


@router.post("/generate_modern", response_model=ModernPatternResponse)
async def generate_modern_pattern(body: ModernPatternRequest):
    """Generate rosette using modern parametric method."""
    if not GENERATOR_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Pattern generator not available"
        )

    try:
        engine = RosettePatternEngine()

        # Convert ring definitions
        rings = []
        for ring_def in body.rings:
            rings.append({
                "inner_diameter_mm": ring_def.inner_diameter_mm,
                "outer_diameter_mm": ring_def.outer_diameter_mm,
                "pattern_type": ring_def.pattern_type,
                "primary_color": ring_def.primary_color,
                "secondary_color": ring_def.secondary_color,
                "segment_count": ring_def.segment_count
            })

        result = engine.generate_modern(
            name=body.name,
            rings=rings,
            soundhole_diameter_mm=body.soundhole_diameter_mm,
            chip_length_mm=body.chip_length_mm
        )

        return ModernPatternResponse(
            spec=result.spec.to_dict(),
            paths=result.paths,
            bom=result.bom,
            estimated_cut_time_min=result.estimated_cut_time_min,
            dxf_content=result.dxf_content,
            svg_content=result.svg_content
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pattern generation failed: {str(e)}"
        )


@router.get("/patterns/{pattern_id}")
async def get_pattern_details(pattern_id: str):
    """Get detailed information about a specific pattern."""
    if not GENERATOR_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Pattern generator not available"
        )

    try:
        # Load catalog
        catalog_path = Path(__file__).parent.parent.parent / "data" / "rosette_pattern_catalog.json"
        if not catalog_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Pattern catalog not found"
            )

        with open(catalog_path) as f:
            catalog = json.load(f)

        # Search all categories
        for category_name, patterns in catalog.get("categories", {}).items():
            for pattern in patterns:
                if pattern.get("id") == pattern_id:
                    return {
                        **pattern,
                        "category": category_name
                    }

        raise HTTPException(
            status_code=404,
            detail=f"Pattern '{pattern_id}' not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load pattern: {str(e)}"
        )


@router.post("/export")
async def export_pattern(body: PatternExportRequest):
    """Export pattern in requested formats."""
    if not GENERATOR_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Pattern generator not available"
        )

    # For now, return the pattern data as-is
    # Future: Implement format conversion and unit scaling
    return {
        "formats": body.formats,
        "target_units": body.target_units,
        "data": body.pattern_data,
        "message": "Export functionality - full implementation pending"
    }
