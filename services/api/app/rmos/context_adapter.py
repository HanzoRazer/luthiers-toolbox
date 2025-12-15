# services/api/app/rmos/context_adapter.py
"""
RMOS Context Adapter: Model ID → RmosContext Transformation

Phase B - Wave 17→18 Integration

Transforms instrument model IDs and specifications into full RmosContext
payloads for RMOS feasibility scoring, constraint optimization, and AI workflows.

This adapter is the bridge between:
- Instrument Geometry (static model definitions)
- RMOS (dynamic manufacturing context)

Usage:
    from rmos.context_adapter import build_rmos_context_for_model
    
    # Create context from model ID
    context = build_rmos_context_for_model("benedetto_17")
    
    # Pass to feasibility scorer
    from rmos.feasibility_fusion import compute_feasibility_for_model_design
    result = compute_feasibility_for_model_design(context)
    
    # Or pass to constraint optimization
    from rmos.constraint_profiles import optimize_with_context
    optimized = optimize_with_context(context, target_rpm=18000)
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List

from .context import (
    RmosContext,
    MaterialProfile,
    SafetyConstraints,
    WoodSpecies,
    CutOperation,
    CutType,
)


# ---------------------------------------------------------------------------
# Main Adapter Function
# ---------------------------------------------------------------------------

def build_rmos_context_for_model(
    model_id: str,
    material_species: str = "maple",
    material_thickness_mm: float = 25.4,
    include_default_cuts: bool = False,
) -> RmosContext:
    """
    Build full RmosContext from instrument model ID.
    
    This is the primary entry point for creating RMOS contexts from
    instrument geometry specifications. It:
    
    1. Loads the instrument model spec (scale, strings, taper, etc.)
    2. Creates default material profile (maple 1" by default)
    3. Creates default safety constraints (CNC router defaults)
    4. Optionally adds typical cut operations
    
    Args:
        model_id: Instrument model identifier (e.g., "benedetto_17", "strat_25_5")
        material_species: Wood species (default: "maple")
        material_thickness_mm: Stock thickness in mm (default: 25.4 = 1 inch)
        include_default_cuts: Whether to add typical neck/body cut operations
    
    Returns:
        RmosContext with loaded model spec and manufacturing profiles
    
    Raises:
        ValueError: If model_id is not found in registry
    
    Example:
        >>> context = build_rmos_context_for_model("benedetto_17")
        >>> print(context.model_spec["scale_length_mm"])
        647.7
        >>> print(context.materials.species)
        WoodSpecies.MAPLE
    """
    # Create base context from model ID
    context = RmosContext.from_model_id(model_id)
    
    # Override material if specified
    try:
        species_enum = WoodSpecies(material_species.lower())
    except ValueError:
        species_enum = WoodSpecies.MAPLE  # Fallback to maple
    
    context.materials = MaterialProfile(
        species=species_enum,
        thickness_mm=material_thickness_mm,
        density_kg_m3=_get_default_density(species_enum),
        hardness_janka_n=_get_default_hardness(species_enum),
        moisture_content_pct=8.0,  # Standard kiln-dried
    )
    
    # Add default cuts if requested
    if include_default_cuts:
        context.cuts = _generate_default_cuts_for_model(model_id)
    
    return context


# ---------------------------------------------------------------------------
# Material Database Helpers
# ---------------------------------------------------------------------------

def _get_default_density(species: WoodSpecies) -> float:
    """
    Get default density (kg/m³) for wood species.
    
    Reference: Wood Database (wood-database.com)
    """
    densities = {
        WoodSpecies.MAPLE: 705.0,       # Hard maple (sugar maple)
        WoodSpecies.MAHOGANY: 545.0,    # Honduran mahogany
        WoodSpecies.ROSEWOOD: 865.0,    # Indian rosewood
        WoodSpecies.EBONY: 1120.0,      # Gaboon ebony
        WoodSpecies.SPRUCE: 450.0,      # Sitka spruce
        WoodSpecies.CEDAR: 380.0,       # Western red cedar
        WoodSpecies.WALNUT: 610.0,      # Black walnut
        WoodSpecies.ASH: 675.0,         # White ash
        WoodSpecies.ALDER: 450.0,       # Red alder
        WoodSpecies.KOA: 625.0,         # Hawaiian koa
        WoodSpecies.BASSWOOD: 415.0,    # American basswood
        WoodSpecies.UNKNOWN: 600.0,     # Generic hardwood average
    }
    return densities.get(species, 600.0)


def _get_default_hardness(species: WoodSpecies) -> float:
    """
    Get default Janka hardness (N) for wood species.
    
    Reference: Wood Database (wood-database.com)
    Converted from lbf: 1 lbf = 4.448 N
    """
    hardnesses = {
        WoodSpecies.MAPLE: 6450.0,      # 1450 lbf
        WoodSpecies.MAHOGANY: 3780.0,   # 850 lbf
        WoodSpecies.ROSEWOOD: 6230.0,   # 1400 lbf
        WoodSpecies.EBONY: 14900.0,     # 3350 lbf (extremely hard)
        WoodSpecies.SPRUCE: 2220.0,     # 500 lbf
        WoodSpecies.CEDAR: 1560.0,      # 350 lbf
        WoodSpecies.WALNUT: 4490.0,     # 1010 lbf
        WoodSpecies.ASH: 5870.0,        # 1320 lbf
        WoodSpecies.ALDER: 2590.0,      # 590 lbf
        WoodSpecies.KOA: 6160.0,        # 1385 lbf
        WoodSpecies.BASSWOOD: 1820.0,   # 410 lbf
        WoodSpecies.UNKNOWN: 4000.0,    # Generic hardwood average
    }
    return hardnesses.get(species, 4000.0)


# ---------------------------------------------------------------------------
# Default Cut Generation
# ---------------------------------------------------------------------------

def _generate_default_cuts_for_model(model_id: str) -> List[CutOperation]:
    """
    Generate typical cut operations for an instrument model.
    
    This creates a representative cutting sequence for:
    - Neck roughing (saw)
    - Neck profiling (route)
    - Fretboard slotting (route)
    - Body outline (saw + route)
    
    Args:
        model_id: Instrument model identifier
    
    Returns:
        List of CutOperation instances
    """
    cuts = [
        CutOperation(
            operation_id="neck_roughing",
            cut_type=CutType.SAW,
            tool_id="bandsaw_3_4",
            feed_rate_mm_min=1500.0,
            spindle_rpm=0.0,  # Bandsaw (no spindle)
            depth_mm=25.4,
            description="Rough cut neck blank from stock",
        ),
        CutOperation(
            operation_id="neck_profile",
            cut_type=CutType.ROUTE,
            tool_id="ballnose_12mm",
            feed_rate_mm_min=1200.0,
            spindle_rpm=18000.0,
            depth_mm=2.5,
            description="Profile neck contour (multi-pass)",
        ),
        CutOperation(
            operation_id="fret_slots",
            cut_type=CutType.ROUTE,
            tool_id="endmill_6mm",
            feed_rate_mm_min=800.0,
            spindle_rpm=12000.0,
            depth_mm=3.0,
            description="Cut fret slots (22 slots)",
        ),
        CutOperation(
            operation_id="body_outline",
            cut_type=CutType.SAW,
            tool_id="bandsaw_1_2",
            feed_rate_mm_min=1000.0,
            spindle_rpm=0.0,
            depth_mm=44.45,  # 1.75" body thickness
            description="Cut body outline from stock",
        ),
        CutOperation(
            operation_id="body_routing",
            cut_type=CutType.ROUTE,
            tool_id="endmill_12mm",
            feed_rate_mm_min=1500.0,
            spindle_rpm=18000.0,
            depth_mm=2.0,
            description="Clean up body edges and pockets",
        ),
    ]
    
    return cuts


# ---------------------------------------------------------------------------
# Advanced Context Building
# ---------------------------------------------------------------------------

def build_rmos_context_with_toolpath(
    model_id: str,
    dxf_file: str,
    material_species: str = "maple",
    material_thickness_mm: float = 25.4,
) -> RmosContext:
    """
    Build RmosContext with imported toolpath data from DXF file.
    
    This variant loads a DXF file and extracts toolpath information
    (path count, total length, bounds) for inclusion in the context.
    
    Args:
        model_id: Instrument model identifier
        dxf_file: Path to DXF file to import
        material_species: Wood species
        material_thickness_mm: Stock thickness
    
    Returns:
        RmosContext with toolpath data
    
    Example:
        >>> context = build_rmos_context_with_toolpath(
        ...     "benedetto_17",
        ...     "neck_outline.dxf",
        ...     material_species="mahogany"
        ... )
        >>> print(context.toolpaths.path_count)
        1
    """
    # Create base context
    context = build_rmos_context_for_model(
        model_id,
        material_species=material_species,
        material_thickness_mm=material_thickness_mm,
    )
    
    # Import toolpath (stub - full implementation requires DXF parser)
    from .context import ToolpathData
    
    # TODO: Replace with actual DXF parsing
    # from ..instrument_geometry.dxf_loader import load_dxf_geometry_stub
    # geometry = load_dxf_geometry_stub(dxf_file)
    
    context.toolpaths = ToolpathData(
        source_file=dxf_file,
        format="dxf_r12",
        path_count=1,  # Stub
        total_length_mm=1000.0,  # Stub
        bounds_mm=[0.0, 0.0, 648.0, 42.0],  # Stub: neck dimensions
        metadata={"imported": True},
    )
    
    return context


def build_rmos_context_from_dict(payload: Dict[str, Any]) -> RmosContext:
    """
    Build RmosContext from dictionary payload (API request body).
    
    This is used by FastAPI endpoints that receive context data as JSON.
    
    Args:
        payload: Dictionary with context fields
    
    Returns:
        RmosContext instance
    
    Example:
        >>> payload = {
        ...     "model_id": "strat_25_5",
        ...     "materials": {"species": "ash", "thickness_mm": 44.45},
        ...     "safety_constraints": {"max_feed_rate_mm_min": 2500.0},
        ... }
        >>> context = build_rmos_context_from_dict(payload)
    """
    return RmosContext.from_dict(payload)


# ---------------------------------------------------------------------------
# Context Export Helpers
# ---------------------------------------------------------------------------

def export_context_to_dict(context: RmosContext) -> Dict[str, Any]:
    """
    Export RmosContext to JSON-compatible dictionary.
    
    Wrapper around context.to_dict() for consistency with adapter pattern.
    
    Args:
        context: RmosContext to export
    
    Returns:
        Dictionary representation
    
    Example:
        >>> context = build_rmos_context_for_model("benedetto_17")
        >>> payload = export_context_to_dict(context)
        >>> print(payload.keys())
        dict_keys(['model_id', 'model_spec', 'materials', ...])
    """
    return context.to_dict()


def get_context_summary(context: RmosContext) -> Dict[str, Any]:
    """
    Get human-readable summary of RmosContext.
    
    Args:
        context: RmosContext to summarize
    
    Returns:
        Summary dictionary with key metrics
    
    Example:
        >>> context = build_rmos_context_for_model("benedetto_17")
        >>> summary = get_context_summary(context)
        >>> print(summary["scale_length_in"])
        25.5
    """
    summary = {
        "model_id": context.model_id,
        "display_name": context.model_spec.get("display_name", "Unknown"),
        "scale_length_mm": context.model_spec.get("scale_length_mm", 0.0),
        "scale_length_in": round(context.model_spec.get("scale_length_mm", 0.0) / 25.4, 2),
        "num_strings": context.model_spec.get("num_strings", 6),
        "num_frets": context.model_spec.get("num_frets", 22),
        "material_species": context.materials.species.value if context.materials else "unknown",
        "material_thickness_in": round(context.materials.thickness_mm / 25.4, 2) if context.materials else 0.0,
        "has_toolpaths": context.toolpaths is not None,
        "cut_count": len(context.cuts) if context.cuts else 0,
        "validation_errors": context.validate(),
    }
    
    return summary
