"""
Saw Lab 2.0 - Pydantic Models

Defines all data models for saw blade operations within RMOS.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SawRiskLevel(str, Enum):
    """Risk classification for saw operations."""
    GREEN = "GREEN"    # Safe to proceed
    YELLOW = "YELLOW"  # Proceed with caution
    RED = "RED"        # Do not proceed


class SawContext(BaseModel):
    """
    Saw blade and machine context for operations.
    
    Attributes:
        blade_diameter_mm: Saw blade diameter in mm (e.g., 254 for 10")
        blade_kerf_mm: Width of cut (kerf) in mm
        tooth_count: Number of teeth on blade
        max_rpm: Maximum safe RPM for blade
        arbor_size_mm: Arbor hole size in mm
        material_id: Material being cut (lookup from materials DB)
        stock_thickness_mm: Thickness of stock being cut
        feed_rate_mm_per_min: Feed rate during cut
        use_dust_collection: Whether dust collection is active
    """
    blade_diameter_mm: float = Field(default=254.0, ge=100.0, le=600.0)
    blade_kerf_mm: float = Field(default=3.0, ge=1.0, le=10.0)
    tooth_count: int = Field(default=24, ge=10, le=120)
    max_rpm: int = Field(default=5000, ge=1000, le=10000)
    arbor_size_mm: float = Field(default=25.4, ge=10.0, le=50.0)
    material_id: Optional[str] = None
    stock_thickness_mm: float = Field(default=25.0, ge=1.0, le=150.0)
    feed_rate_mm_per_min: float = Field(default=3000.0, ge=100.0, le=20000.0)
    use_dust_collection: bool = True


class SawDesign(BaseModel):
    """
    Saw cut design parameters.
    
    Attributes:
        cut_length_mm: Length of cut in mm
        cut_type: Type of cut (rip, crosscut, miter, bevel, dado)
        miter_angle_deg: Miter angle in degrees (0 for straight cut)
        bevel_angle_deg: Bevel angle in degrees (0 for vertical cut)
        dado_width_mm: Width for dado cuts (0 for through cuts)
        dado_depth_mm: Depth for dado cuts
        repeat_count: Number of times to repeat cut
        offset_mm: Offset between repeated cuts
    """
    cut_length_mm: float = Field(default=300.0, ge=10.0, le=3000.0)
    cut_type: str = Field(default="crosscut")
    miter_angle_deg: float = Field(default=0.0, ge=-60.0, le=60.0)
    bevel_angle_deg: float = Field(default=0.0, ge=-45.0, le=45.0)
    dado_width_mm: float = Field(default=0.0, ge=0.0, le=50.0)
    dado_depth_mm: float = Field(default=0.0, ge=0.0, le=75.0)
    repeat_count: int = Field(default=1, ge=1, le=100)
    offset_mm: float = Field(default=0.0, ge=0.0, le=1000.0)


class SawCalculatorResult(BaseModel):
    """Result from a single saw calculator."""
    calculator_name: str
    score: float = Field(ge=0.0, le=100.0)
    warning: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SawFeasibilityResult(BaseModel):
    """
    Aggregated feasibility result for saw operation.
    
    Attributes:
        score: Overall feasibility score (0-100)
        risk_level: Risk classification (GREEN/YELLOW/RED)
        warnings: List of warning messages
        calculator_results: Dict of individual calculator results
        efficiency: Estimated cut efficiency percentage
        estimated_cut_time_seconds: Estimated time for cut
    """
    score: float = Field(ge=0.0, le=100.0)
    risk_level: SawRiskLevel
    warnings: List[str] = Field(default_factory=list)
    calculator_results: Dict[str, SawCalculatorResult] = Field(default_factory=dict)
    efficiency: float = Field(default=100.0, ge=0.0, le=100.0)
    estimated_cut_time_seconds: float = Field(default=0.0, ge=0.0)


class SawToolpathMove(BaseModel):
    """Single toolpath move for saw operation."""
    code: str  # G-code command (G0, G1, etc.)
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    f: Optional[float] = None  # Feed rate
    comment: Optional[str] = None


class SawToolpathPlan(BaseModel):
    """
    Complete toolpath plan for saw operation.
    
    Attributes:
        moves: List of G-code moves
        total_length_mm: Total path length in mm
        estimated_time_seconds: Estimated machining time
        warnings: List of warning messages
        cut_count: Number of individual cuts
        material_removed_mm3: Volume of material removed
    """
    moves: List[SawToolpathMove] = Field(default_factory=list)
    total_length_mm: float = Field(default=0.0, ge=0.0)
    estimated_time_seconds: float = Field(default=0.0, ge=0.0)
    warnings: List[str] = Field(default_factory=list)
    cut_count: int = Field(default=0, ge=0)
    material_removed_mm3: float = Field(default=0.0, ge=0.0)


class MaterialProperties(BaseModel):
    """Material properties for saw calculations."""
    id: str
    name: str
    density_kg_per_m3: float = 700.0
    burn_tendency: float = Field(default=0.5, ge=0.0, le=1.0)
    tearout_tendency: float = Field(default=0.5, ge=0.0, le=1.0)
    hardness_scale: float = Field(default=0.5, ge=0.0, le=1.0)
