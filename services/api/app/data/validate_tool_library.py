# services/api/app/data/validate_tool_library.py

"""
Tool & Material Library Validator

Validates tool_library.json and material profiles for consistency.
Run standalone: python -m app.data.validate_tool_library

Phase 1 of Tool Library Migration — additive validation on existing schema.
"""

from __future__ import annotations

from typing import List, Optional

from .tool_library import load_tool_library, ToolProfile, MaterialProfile, _DEFAULT_TOOL_LIBRARY_PATH


# Type alias for library (uses the actual return type)
ToolLibrary = type(load_tool_library()).__class__


class ValidationError(Exception):
    """Raised when tool/material library validation fails."""
    pass


def validate_tool_profile(tool: ToolProfile) -> List[str]:
    """
    Validate a single tool profile.
    
    Returns list of error messages (empty if valid).
    """
    errors: List[str] = []
    
    # Required: positive diameter
    if tool.diameter_mm <= 0:
        errors.append(f"{tool.tool_id}: diameter_mm must be > 0 (got {tool.diameter_mm})")
    
    # Required: at least 1 flute (except saw blades which use teeth)
    if tool.flutes < 1 and tool.tool_type not in ("saw_blade", "saw"):
        errors.append(f"{tool.tool_id}: flutes must be >= 1 for non-saw tools (got {tool.flutes})")
    
    # Chipload range: min <= max
    if tool.chipload_min_mm > tool.chipload_max_mm:
        errors.append(
            f"{tool.tool_id}: chipload_min_mm ({tool.chipload_min_mm}) > "
            f"chipload_max_mm ({tool.chipload_max_mm})"
        )
    
    # Chipload values should be positive
    if tool.chipload_min_mm < 0:
        errors.append(f"{tool.tool_id}: chipload_min_mm must be >= 0")
    if tool.chipload_max_mm < 0:
        errors.append(f"{tool.tool_id}: chipload_max_mm must be >= 0")
    
    return errors


def validate_material_profile(mat: MaterialProfile) -> List[str]:
    """
    Validate a single material profile.
    
    Returns list of error messages (empty if valid).
    """
    errors: List[str] = []
    
    # Heat sensitivity must be valid enum
    valid_heat = {"low", "medium", "high", "very_high"}
    if mat.heat_sensitivity.lower() not in valid_heat:
        errors.append(
            f"{mat.material_id}: heat_sensitivity must be one of {valid_heat} "
            f"(got '{mat.heat_sensitivity}')"
        )
    
    # Density should be positive if specified
    if mat.density_kg_m3 < 0:
        errors.append(f"{mat.material_id}: density_kg_m3 must be >= 0")
    
    return errors


def validate_library(library = None) -> List[str]:
    """
    Validate entire tool library.
    
    Args:
        library: ToolLibrary instance (loads default if None)
        
    Returns:
        List of all error messages (empty if all valid)
    """
    if library is None:
        library = load_tool_library()
    
    all_errors: List[str] = []
    
    # Validate all tools
    for tool_id in library.list_tool_ids():
        tool = library.get_tool(tool_id)
        if tool:
            all_errors.extend(validate_tool_profile(tool))
    
    # Validate all materials
    for mat_id in library.list_material_ids():
        mat = library.get_material(mat_id)
        if mat:
            all_errors.extend(validate_material_profile(mat))
    
    return all_errors


def main() -> None:
    """
    CLI entry point for validation.
    
    Usage: python -m app.data.validate_tool_library
    """
    print(f"Loading tool library from: {_DEFAULT_TOOL_LIBRARY_PATH}")
    
    try:
        library = ToolLibrary()
        print(f"  Tools loaded: {len(library.list_tool_ids())}")
        print(f"  Materials loaded: {len(library.list_material_ids())}")
    except Exception as e:  # WP-1: keep broad — CLI validator must catch any load error to report
        print(f"❌ Failed to load library: {e}")
        raise ValidationError(f"Library load failed: {e}")
    
    errors = validate_library(library)
    
    if errors:
        print(f"\n❌ Validation errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        raise ValidationError(f"Tool/Material library validation failed with {len(errors)} errors")
    else:
        print("\n✅ Tool and Material libraries validated OK.")


if __name__ == "__main__":
    main()
