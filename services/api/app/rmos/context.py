# services/api/app/rmos/context.py
"""
RMOS Context: Unified Manufacturing Context System

Phase B - Wave 17→18 Integration

Provides the authoritative RmosContext dataclass that integrates:
- Instrument geometry (model specifications)
- Toolpath data (DXF/G-code imports)
- Material specifications (wood species, thickness)
- Cut operations (saw, route, drill sequences)
- Safety constraints (feeds, speeds, tool limits)
- Physics calculations (chipload, deflection, heat)

This is the CRITICAL infrastructure that enables:
- Cross-module reasoning (Saw Lab + CNC Router + Instrument Geometry)
- Type-safe context passing between RMOS components
- Validation at system boundaries
- Future versioning (RmosContextV2, etc.)

Usage:
    from rmos.context import RmosContext, MaterialProfile, SafetyConstraints
    
    # Create from instrument model
    context = RmosContext.from_model_id("benedetto_17")
    
    # Add toolpath data
    context.toolpaths = load_dxf_toolpath("neck_outline.dxf")
    
    # Add material constraints
    context.materials = MaterialProfile(
        species="maple",
        thickness_mm=25.4,
        density_kg_m3=705
    )
    
    # Pass to RMOS calculators
    feasibility = compute_feasibility(context)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CutType(str, Enum):
    """Types of cutting operations."""
    SAW = "saw"
    ROUTE = "route"
    DRILL = "drill"
    MILL = "mill"
    SAND = "sand"


class WoodSpecies(str, Enum):
    """Common wood species for lutherie."""
    MAPLE = "maple"
    MAHOGANY = "mahogany"
    ROSEWOOD = "rosewood"
    EBONY = "ebony"
    SPRUCE = "spruce"
    CEDAR = "cedar"
    WALNUT = "walnut"
    ASH = "ash"
    ALDER = "alder"
    KOA = "koa"
    BASSWOOD = "basswood"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Material Profile
# ---------------------------------------------------------------------------

@dataclass
class MaterialProfile:
    """
    Material specifications for RMOS calculations.
    
    Attributes:
        species: Wood species (maple, mahogany, etc.)
        thickness_mm: Stock thickness in millimeters
        density_kg_m3: Material density (kg/m³) for weight/BOM calculations
        hardness_janka_n: Janka hardness rating (optional, for chipload)
        moisture_content_pct: Moisture content percentage (affects cutting)
        notes: Additional material notes
    """
    species: WoodSpecies = WoodSpecies.MAPLE
    thickness_mm: float = 25.4  # 1 inch default
    density_kg_m3: float = 705.0  # Hard maple default
    hardness_janka_n: Optional[float] = None  # ~6450N for hard maple
    moisture_content_pct: float = 8.0  # Standard kiln-dried
    notes: str = ""


# ---------------------------------------------------------------------------
# Safety Constraints
# ---------------------------------------------------------------------------

@dataclass
class SafetyConstraints:
    """
    Safety limits for CNC operations.
    
    Attributes:
        max_feed_rate_mm_min: Maximum feed rate (mm/min)
        max_spindle_rpm: Maximum spindle speed (RPM)
        max_plunge_rate_mm_min: Maximum Z-axis plunge rate
        min_tool_diameter_mm: Minimum allowed tool diameter
        max_tool_diameter_mm: Maximum allowed tool diameter
        max_depth_of_cut_mm: Maximum depth per pass
        require_dust_collection: Whether dust collection is mandatory
        require_safety_stops: Whether emergency stops are required
        notes: Additional safety notes
    """
    max_feed_rate_mm_min: float = 2000.0
    max_spindle_rpm: float = 24000.0
    max_plunge_rate_mm_min: float = 500.0
    min_tool_diameter_mm: float = 1.5
    max_tool_diameter_mm: float = 25.4
    max_depth_of_cut_mm: float = 3.0
    require_dust_collection: bool = True
    require_safety_stops: bool = True
    notes: str = ""


# ---------------------------------------------------------------------------
# Cut Operation
# ---------------------------------------------------------------------------

@dataclass
class CutOperation:
    """
    Individual cutting operation in a manufacturing sequence.
    
    Attributes:
        operation_id: Unique identifier for this operation
        cut_type: Type of operation (saw, route, drill, etc.)
        tool_id: Tool identifier (from tool library)
        feed_rate_mm_min: Feed rate for this operation
        spindle_rpm: Spindle speed for this operation
        depth_mm: Depth of cut
        description: Human-readable description
        gcode_file: Optional G-code filename
        estimated_time_seconds: Estimated operation time
        metadata: Additional operation-specific data
    """
    operation_id: str
    cut_type: CutType
    tool_id: str
    feed_rate_mm_min: float
    spindle_rpm: float
    depth_mm: float
    description: str = ""
    gcode_file: Optional[str] = None
    estimated_time_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Toolpath Data
# ---------------------------------------------------------------------------

@dataclass
class ToolpathData:
    """
    Toolpath data from DXF/G-code imports.
    
    Attributes:
        source_file: Original DXF/G-code filename
        format: File format (dxf_r12, gcode, svg, etc.)
        path_count: Number of paths/contours
        total_length_mm: Total toolpath length in millimeters
        bounds_mm: Bounding box [x_min, y_min, x_max, y_max]
        geometry: Optional geometry data (Shapely objects, etc.)
        metadata: Additional toolpath metadata
    """
    source_file: str
    format: str
    path_count: int = 0
    total_length_mm: float = 0.0
    bounds_mm: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    geometry: Optional[Any] = None  # Shapely geometry or similar
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# RMOS Context (AUTHORITATIVE)
# ---------------------------------------------------------------------------

@dataclass
class RmosContext:
    """
    Unified RMOS manufacturing context.
    
    This is the AUTHORITATIVE context structure that integrates:
    - Instrument geometry specifications
    - Toolpath data (from DXF/G-code)
    - Material profiles
    - Cut operation sequences
    - Safety constraints
    - Physics calculation inputs/outputs
    
    All RMOS components (feasibility scoring, constraint optimization,
    AI search, telemetry) use this structure for cross-module communication.
    
    Attributes:
        model_id: Instrument model identifier (e.g., "benedetto_17")
        model_spec: Full instrument specification (geometry, scale, strings)
        toolpaths: Optional toolpath data from DXF/G-code imports
        materials: Material profile (wood species, thickness, density)
        cuts: Ordered list of cut operations
        safety_constraints: Safety limits (feeds, speeds, tool limits)
        physics_inputs: Physics calculation inputs (chipload, deflection, etc.)
        metadata: Additional context metadata
    """
    # Core instrument geometry
    model_id: str
    model_spec: Dict[str, Any]  # InstrumentSpec or GuitarModelSpec as dict
    
    # Manufacturing data
    toolpaths: Optional[ToolpathData] = None
    materials: Optional[MaterialProfile] = None
    cuts: Optional[List[CutOperation]] = None
    safety_constraints: Optional[SafetyConstraints] = None
    
    # Physics/calculator data
    physics_inputs: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ---------------------------------------------------------------------------
    # Factory Methods
    # ---------------------------------------------------------------------------
    
    @classmethod
    def from_model_id(cls, model_id: str) -> "RmosContext":
        """
        Create RmosContext from instrument model ID.
        
        Loads model specification from the instrument geometry registry
        and creates a minimal context with default material/safety profiles.
        
        Args:
            model_id: Instrument model identifier (e.g., "strat_25_5")
        
        Returns:
            RmosContext with loaded model spec and defaults
        
        Example:
            >>> context = RmosContext.from_model_id("benedetto_17")
            >>> print(context.model_spec["scale_length_mm"])
            647.7
        """
        # Import here to avoid circular dependencies
        from ..instrument_geometry.model_spec import PRESET_MODELS, guitar_model_to_instrument_spec
        
        # Load model spec
        if model_id not in PRESET_MODELS:
            raise ValueError(f"Unknown model_id: {model_id}. Available: {list(PRESET_MODELS.keys())}")
        
        guitar_model = PRESET_MODELS[model_id]
        instrument_spec = guitar_model_to_instrument_spec(guitar_model)
        
        # Convert to dict for storage (using GuitarModelSpec and InstrumentSpec fields)
        model_spec_dict = {
            "id": guitar_model.id,
            "display_name": guitar_model.display_name,
            "scale_length_mm": instrument_spec.scale_length_mm,
            "num_strings": instrument_spec.string_count,
            "num_frets": instrument_spec.fret_count,
            "nut_width_mm": guitar_model.neck_taper.nut_width_mm,
            "heel_width_mm": guitar_model.neck_taper.heel_width_mm,
            "neck_length_mm": instrument_spec.scale_length_mm * 0.75,  # Approx: ~75% of scale
            "string_spacings_at_nut_mm": [],  # TODO: compute from nut_spacing
            "string_spacings_at_bridge_mm": [],  # TODO: compute from bridge_spacing
        }
        
        return cls(
            model_id=model_id,
            model_spec=model_spec_dict,
            materials=MaterialProfile(),  # Default maple 1"
            safety_constraints=SafetyConstraints(),  # Default CNC limits
        )
    
    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RmosContext":
        """
        Create RmosContext from dictionary payload (e.g., from context_adapter).
        
        Args:
            payload: Dictionary with context data
        
        Returns:
            RmosContext instance
        
        Example:
            >>> payload = {
            ...     "model_id": "strat_25_5",
            ...     "model_spec": {...},
            ...     "materials": {"species": "maple", "thickness_mm": 25.4},
            ... }
            >>> context = RmosContext.from_dict(payload)
        """
        # Extract required fields
        model_id = payload.get("model_id", "unknown")
        model_spec = payload.get("model_spec", {})
        
        # Extract optional structured fields
        materials_data = payload.get("materials")
        materials = MaterialProfile(**materials_data) if materials_data else None
        
        safety_data = payload.get("safety_constraints")
        safety = SafetyConstraints(**safety_data) if safety_data else None
        
        toolpaths_data = payload.get("toolpaths")
        toolpaths = ToolpathData(**toolpaths_data) if toolpaths_data else None
        
        cuts_data = payload.get("cuts")
        cuts = [CutOperation(**cut) for cut in cuts_data] if cuts_data else None
        
        return cls(
            model_id=model_id,
            model_spec=model_spec,
            toolpaths=toolpaths,
            materials=materials,
            cuts=cuts,
            safety_constraints=safety,
            physics_inputs=payload.get("physics_inputs", {}),
            metadata=payload.get("metadata", {}),
        )
    
    # ---------------------------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize RmosContext to JSON-compatible dictionary.
        
        Returns:
            Dictionary representation of context
        
        Example:
            >>> context = RmosContext.from_model_id("strat_25_5")
            >>> payload = context.to_dict()
            >>> print(payload.keys())
            dict_keys(['model_id', 'model_spec', 'toolpaths', ...])
        """
        result = {
            "model_id": self.model_id,
            "model_spec": self.model_spec,
            "physics_inputs": self.physics_inputs,
            "metadata": self.metadata,
        }
        
        # Conditionally add structured fields
        if self.toolpaths:
            result["toolpaths"] = {
                "source_file": self.toolpaths.source_file,
                "format": self.toolpaths.format,
                "path_count": self.toolpaths.path_count,
                "total_length_mm": self.toolpaths.total_length_mm,
                "bounds_mm": self.toolpaths.bounds_mm,
                "metadata": self.toolpaths.metadata,
            }
        
        if self.materials:
            result["materials"] = {
                "species": self.materials.species.value,
                "thickness_mm": self.materials.thickness_mm,
                "density_kg_m3": self.materials.density_kg_m3,
                "hardness_janka_n": self.materials.hardness_janka_n,
                "moisture_content_pct": self.materials.moisture_content_pct,
                "notes": self.materials.notes,
            }
        
        if self.cuts:
            result["cuts"] = [
                {
                    "operation_id": cut.operation_id,
                    "cut_type": cut.cut_type.value,
                    "tool_id": cut.tool_id,
                    "feed_rate_mm_min": cut.feed_rate_mm_min,
                    "spindle_rpm": cut.spindle_rpm,
                    "depth_mm": cut.depth_mm,
                    "description": cut.description,
                    "gcode_file": cut.gcode_file,
                    "estimated_time_seconds": cut.estimated_time_seconds,
                    "metadata": cut.metadata,
                }
                for cut in self.cuts
            ]
        
        if self.safety_constraints:
            result["safety_constraints"] = {
                "max_feed_rate_mm_min": self.safety_constraints.max_feed_rate_mm_min,
                "max_spindle_rpm": self.safety_constraints.max_spindle_rpm,
                "max_plunge_rate_mm_min": self.safety_constraints.max_plunge_rate_mm_min,
                "min_tool_diameter_mm": self.safety_constraints.min_tool_diameter_mm,
                "max_tool_diameter_mm": self.safety_constraints.max_tool_diameter_mm,
                "max_depth_of_cut_mm": self.safety_constraints.max_depth_of_cut_mm,
                "require_dust_collection": self.safety_constraints.require_dust_collection,
                "require_safety_stops": self.safety_constraints.require_safety_stops,
                "notes": self.safety_constraints.notes,
            }
        
        return result
    
    # ---------------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------------
    
    def validate(self) -> List[str]:
        """
        Validate context integrity and return list of warnings/errors.
        
        Returns:
            List of validation messages (empty if valid)
        
        Example:
            >>> context = RmosContext.from_model_id("strat_25_5")
            >>> errors = context.validate()
            >>> if errors:
            ...     print("Validation failed:", errors)
        """
        errors = []
        
        # Required fields
        if not self.model_id:
            errors.append("model_id is required")
        if not self.model_spec:
            errors.append("model_spec is required")
        
        # Material validation
        if self.materials:
            if self.materials.thickness_mm <= 0:
                errors.append(f"Invalid material thickness: {self.materials.thickness_mm}mm")
            if self.materials.density_kg_m3 <= 0:
                errors.append(f"Invalid material density: {self.materials.density_kg_m3} kg/m³")
        
        # Safety validation
        if self.safety_constraints:
            if self.safety_constraints.max_feed_rate_mm_min <= 0:
                errors.append(f"Invalid max feed rate: {self.safety_constraints.max_feed_rate_mm_min}")
            if self.safety_constraints.max_spindle_rpm <= 0:
                errors.append(f"Invalid max spindle RPM: {self.safety_constraints.max_spindle_rpm}")
        
        # Cut operation validation
        if self.cuts:
            for i, cut in enumerate(self.cuts):
                if cut.feed_rate_mm_min <= 0:
                    errors.append(f"Cut #{i} has invalid feed rate: {cut.feed_rate_mm_min}")
                if cut.spindle_rpm < 0:
                    errors.append(f"Cut #{i} has invalid spindle RPM: {cut.spindle_rpm}")
                if cut.depth_mm < 0:
                    errors.append(f"Cut #{i} has invalid depth: {cut.depth_mm}")
        
        return errors


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def create_default_context(model_id: str) -> RmosContext:
    """
    Create RmosContext with default material/safety profiles.
    
    Convenience wrapper around RmosContext.from_model_id().
    
    Args:
        model_id: Instrument model identifier
    
    Returns:
        RmosContext with defaults
    
    Example:
        >>> context = create_default_context("benedetto_17")
        >>> print(context.materials.species)
        WoodSpecies.MAPLE
    """
    return RmosContext.from_model_id(model_id)
