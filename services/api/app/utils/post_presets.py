"""
Post-Processor Presets for CNC Controllers

Defines controller-specific G-code quirks and settings for:
- GRBL (I/J mode, G4 P milliseconds)
- Mach3 (I/J mode, G4 P milliseconds)
- Haas (R-mode arcs, G4 S seconds)
- Marlin (I/J mode, G4 P milliseconds, 3D printer style)

Usage:
    preset = get_post_preset("Haas")
    if preset.use_r_mode:
        # Generate R-mode arcs instead of I/J
    if preset.dwell_in_seconds:
        # Convert milliseconds to seconds for G4 S
"""

from typing import Dict, Optional
from pydantic import BaseModel


class PostPreset(BaseModel):
    """Configuration for a specific CNC controller post-processor"""
    
    name: str
    description: str
    use_r_mode: bool = False  # True for R arcs, False for I/J arcs
    dwell_in_seconds: bool = False  # True for G4 S (seconds), False for G4 P (milliseconds)
    supports_g64: bool = False  # Path blending mode (LinuxCNC)
    max_arc_tolerance: Optional[float] = None  # Maximum arc tolerance in mm
    notes: str = ""


# Controller preset definitions
PRESETS: Dict[str, PostPreset] = {
    "GRBL": PostPreset(
        name="GRBL",
        description="GRBL 1.1+ (Arduino CNC)",
        use_r_mode=False,  # I/J mode
        dwell_in_seconds=False,  # G4 P milliseconds
        supports_g64=False,
        max_arc_tolerance=0.002,  # 0.002mm default
        notes="Standard hobbyist CNC controller. Uses I/J relative centers and millisecond dwells."
    ),
    
    "Mach3": PostPreset(
        name="Mach3",
        description="Mach3/Mach4 (Windows CNC)",
        use_r_mode=False,  # I/J mode (Mach3 supports both)
        dwell_in_seconds=False,  # G4 P milliseconds
        supports_g64=False,
        max_arc_tolerance=None,
        notes="Windows-based CNC controller. Supports both I/J and R modes, defaults to I/J."
    ),
    
    "Haas": PostPreset(
        name="Haas",
        description="Haas VMC (Industrial CNC)",
        use_r_mode=True,  # R-mode arcs preferred
        dwell_in_seconds=True,  # G4 S seconds (NOT milliseconds!)
        supports_g64=False,
        max_arc_tolerance=None,
        notes="Industrial VMC controller. Prefers R-mode arcs. IMPORTANT: G4 uses SECONDS (G4 S), not milliseconds."
    ),
    
    "Marlin": PostPreset(
        name="Marlin",
        description="Marlin (3D Printer Firmware)",
        use_r_mode=False,  # I/J mode
        dwell_in_seconds=False,  # G4 P milliseconds
        supports_g64=False,
        max_arc_tolerance=None,
        notes="3D printer firmware adapted for CNC. Uses I/J mode and millisecond dwells like GRBL."
    ),
}


def get_post_preset(preset_name: Optional[str]) -> PostPreset:
    """
    Get post-processor preset by name.
    
    Args:
        preset_name: Preset identifier (GRBL, Mach3, Haas, Marlin) or None
        
    Returns:
        PostPreset configuration
        
    Raises:
        ValueError: If preset_name is not recognized
        
    Example:
        >>> preset = get_post_preset("Haas")
        >>> preset.use_r_mode
        True
        >>> preset.dwell_in_seconds
        True
    """
    if not preset_name:
        # Default to GRBL if no preset specified
        return PRESETS["GRBL"]
    
    if preset_name not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(f"Unknown post preset '{preset_name}'. Available: {available}")
    
    return PRESETS[preset_name]


def list_presets() -> Dict[str, str]:
    """
    List all available post-processor presets.
    
    Returns:
        Dict mapping preset names to descriptions
        
    Example:
        >>> presets = list_presets()
        >>> presets["Haas"]
        'Haas VMC (Industrial CNC)'
    """
    return {name: preset.description for name, preset in PRESETS.items()}


def get_dwell_command(dwell_ms: int, preset: PostPreset) -> str:
    """
    Generate G4 dwell command for given preset.
    
    Args:
        dwell_ms: Dwell time in milliseconds
        preset: Post-processor preset
        
    Returns:
        G-code dwell command (e.g., "G4 P500" or "G4 S0.5")
        
    Example:
        >>> preset_grbl = get_post_preset("GRBL")
        >>> get_dwell_command(500, preset_grbl)
        'G4 P500'
        
        >>> preset_haas = get_post_preset("Haas")
        >>> get_dwell_command(500, preset_haas)
        'G4 S0.5'
    """
    if dwell_ms <= 0:
        return ""
    
    if preset.dwell_in_seconds:
        # Convert milliseconds to seconds
        seconds = dwell_ms / 1000.0
        return f"G4 S{seconds:.3f}".rstrip('0').rstrip('.')
    else:
        # Milliseconds (standard for GRBL, Mach3, Marlin)
        return f"G4 P{int(dwell_ms)}"


def validate_preset_compatibility(preset_name: str, ij_mode: bool) -> None:
    """
    Validate that requested arc mode is compatible with preset.
    
    Args:
        preset_name: Preset identifier
        ij_mode: True for I/J mode, False for R mode
        
    Raises:
        ValueError: If incompatible combination detected
        
    Example:
        >>> validate_preset_compatibility("Haas", False)  # OK - Haas prefers R mode
        >>> validate_preset_compatibility("Haas", True)   # Warning but allowed
    """
    preset = get_post_preset(preset_name)
    
    # Haas prefers R-mode but can handle I/J
    if preset.name == "Haas" and ij_mode:
        # This is just a warning case - Haas can handle I/J mode
        # In production, you might log a warning here
        pass
    
    # GRBL/Marlin prefer I/J but can handle R for simple arcs
    # No strict validation needed, just informational
