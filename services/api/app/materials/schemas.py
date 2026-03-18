# services/api/app/materials/schemas.py
"""
Materials domain schemas (MAT-001)

Typed Pydantic models for all materials data flowing through the platform.
These are the Layer 1 data contracts — used by routers, the Instrument Project
Graph (MaterialSelection species IDs), and Utilities.
"""

from __future__ import annotations

import math
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, computed_field


# ---------------------------------------------------------------------------
# Tonewood role taxonomy
# Matches the typical_uses values in luthier_tonewood_reference.json
# ---------------------------------------------------------------------------

TonewoodRole = Literal[
    "soundboard", "top", "body_top",
    "back_sides",
    "neck", "neck_laminate",
    "fretboard",
    "bridge",
    "bracing",
    "body",
    "decorative", "accent",
    "nuts",
]

# Human-readable labels for UI
ROLE_LABELS: Dict[str, str] = {
    "soundboard":    "Soundboard / Top",
    "top":           "Top",
    "body_top":      "Body Top",
    "back_sides":    "Back & Sides",
    "neck":          "Neck",
    "neck_laminate": "Neck Laminate",
    "fretboard":     "Fretboard",
    "bridge":        "Bridge",
    "bracing":       "Bracing",
    "body":          "Body",
    "decorative":    "Decorative / Accent",
    "accent":        "Accent",
    "nuts":          "Nut / Saddle",
}

# Canonical MaterialSelection field → role mapping
MATERIAL_SELECTION_ROLES: Dict[str, str] = {
    "top":        "soundboard",
    "back_sides": "back_sides",
    "neck":       "neck",
    "fretboard":  "fretboard",
    "bridge":     "bridge",
    "brace_stock":"bracing",
}


# ---------------------------------------------------------------------------
# Machining risk schema
# ---------------------------------------------------------------------------

class MachiningNotes(BaseModel):
    burn_risk:    Literal["low", "medium", "high"] = "low"
    tearout_risk: Literal["low", "medium", "high"] = "low"
    dust_hazard:  Literal["low", "medium", "high"] = "low"
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Tonewood entry — the curated reference record
# ---------------------------------------------------------------------------

class TonewoodEntry(BaseModel):
    """
    A single curated tonewood record from luthier_tonewood_reference.json.

    Acoustic indices (radiation_ratio, specific_moe, ashby_index,
    acoustic_impedance_mrayl) are computed on load via @computed_field.
    They are derived — never stored in the JSON source.
    """
    id: str
    name: str
    scientific_name: Optional[str] = None
    guitar_relevance: Literal["primary", "established", "emerging", "exotic"] = "established"

    # Physical properties
    density_kg_m3: Optional[float] = Field(default=None, description="Density in kg/m³")
    specific_gravity: Optional[float] = None
    janka_hardness_lbf: Optional[float] = None

    # Acoustic / structural properties
    modulus_of_elasticity_gpa: Optional[float] = Field(
        default=None, description="MOE (GPa) — Young's modulus. Primary stiffness indicator."
    )
    E_C_gpa: Optional[float] = Field(
        default=None,
        description="Cross-grain modulus GPa. "
        "Required for plate thickness calculation."
    )
    modulus_of_rupture_mpa: Optional[float] = Field(
        default=None, description="MOR (MPa) — bending strength."
    )
    speed_of_sound_m_s: Optional[float] = Field(
        default=None,
        description="Speed of sound in wood (m/s). Derived from MOE/density if not measured."
    )
    acoustic_impedance: Optional[float] = Field(
        default=None,
        description="Raw acoustic impedance from dataset (unitless ratio)."
    )

    # Tonal and usage
    grain: Optional[str] = None
    tone_character: Optional[str] = None
    typical_uses: List[str] = Field(default_factory=list)
    sustainability: Optional[str] = None

    # Machining
    machining_notes: Optional[MachiningNotes] = None

    # Tier (from which section of tonewood reference it came)
    tier: Literal["tier_1", "tier_2"] = "tier_1"

    # --- Computed acoustic indices ---

    @computed_field  # type: ignore[misc]
    @property
    def speed_of_sound_computed_m_s(self) -> Optional[float]:
        """
        Speed of sound from MOE + density (m/s).
        Formula: c = sqrt(E / ρ) where E in Pa, ρ in kg/m³.
        Falls back to speed_of_sound_m_s field if available.
        """
        if self.speed_of_sound_m_s:
            return round(self.speed_of_sound_m_s, 1)
        if self.modulus_of_elasticity_gpa and self.density_kg_m3:
            e_pa = self.modulus_of_elasticity_gpa * 1e9
            c = math.sqrt(e_pa / self.density_kg_m3)
            return round(c, 1)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def radiation_ratio(self) -> Optional[float]:
        """
        Schelleng radiation ratio: c / ρ (m/s / kg/m³ × 10⁶).
        Primary soundboard quality index. Higher = more projecting.
        Reference: Schelleng (1963) — Adirondack spruce ~11.7, Sitka ~11.4.
        """
        c = self.speed_of_sound_computed_m_s
        if c and self.density_kg_m3:
            return round((c / self.density_kg_m3) * 1e6, 2)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def specific_moe(self) -> Optional[float]:
        """
        Specific MOE: E / ρ × 10⁶ (GPa / kg/m³).
        Stiffness per unit mass. Same as c²/10⁶.
        Used for fretboard and brace comparison where pure stiffness matters.
        """
        if self.modulus_of_elasticity_gpa and self.density_kg_m3:
            return round((self.modulus_of_elasticity_gpa / self.density_kg_m3) * 1e6, 4)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def ashby_index(self) -> Optional[float]:
        """
        Ashby plate bending index: E^(1/3) / ρ.
        Governs deflection at minimum weight for plate bending (soundboard, back).
        Higher = stiffer plate per gram.
        Reference: Ashby (2011) — Materials Selection in Mechanical Design.
        """
        if self.modulus_of_elasticity_gpa and self.density_kg_m3:
            e_mpa = self.modulus_of_elasticity_gpa * 1000
            return round((e_mpa ** (1 / 3)) / self.density_kg_m3, 5)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def acoustic_impedance_mrayl(self) -> Optional[float]:
        """
        Acoustic impedance Z = ρ × c (kg/m²·s), expressed in MRayl (×10⁻⁶).
        Governs reflection at wood joints. Matched → better energy transfer.
        """
        c = self.speed_of_sound_computed_m_s
        if c and self.density_kg_m3:
            return round((self.density_kg_m3 * c) * 1e-6, 3)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def R_anis(self) -> Optional[float]:
        """Orthotropic ratio E_L/E_C. Typically 10-20 for tonewoods."""
        if self.modulus_of_elasticity_gpa and self.E_C_gpa and self.E_C_gpa > 0:
            return round(self.modulus_of_elasticity_gpa / self.E_C_gpa, 2)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def has_acoustic_data(self) -> bool:
        """True if this entry has enough data for acoustic index computation."""
        return (
            self.modulus_of_elasticity_gpa is not None
            and self.density_kg_m3 is not None
        )

    def matches_role(self, role: str) -> bool:
        """Check if this tonewood is suitable for a given instrument role."""
        return role in self.typical_uses


# ---------------------------------------------------------------------------
# Wood species entry — full CNC data record (from wood_species.json)
# ---------------------------------------------------------------------------

class WoodSpeciesEntry(BaseModel):
    """
    A single species record from wood_species.json.
    Contains full machining data (feed/speed/energy/heat partition).
    This is the source of CNC cutting parameters.
    """
    id: str
    name: str
    scientific_name: Optional[str] = None
    category: Optional[str] = None  # "hardwood" | "softwood"

    # Physical
    density_kg_m3: Optional[float] = None
    specific_gravity: Optional[float] = None
    janka_hardness_lbf: Optional[float] = None
    grain: Optional[str] = None
    workability: Optional[str] = None

    # CNC machining (from thermal/machining sections)
    specific_cutting_energy_j_per_mm3: Optional[float] = None
    hardness_scale: Optional[float] = None
    burn_tendency: Optional[float] = None
    tearout_tendency: Optional[float] = None
    chipload_multiplier: Optional[float] = None
    roughing_max_mm_min: Optional[float] = None
    finishing_max_mm_min: Optional[float] = None
    max_rpm: Optional[float] = None

    # Lutherie
    tone_character: Optional[str] = None
    typical_uses: List[str] = Field(default_factory=list)
    guitar_relevance: Optional[str] = None


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------

class TonewoodsResponse(BaseModel):
    """Response for GET /api/registry/tonewoods"""
    tonewoods: List[TonewoodEntry]
    total_count: int
    tier_1_count: int
    tier_2_count: int
    with_acoustic_data: int


class MaterialCompareRequest(BaseModel):
    """Request for POST /api/system/materials/compare"""
    species_ids: List[str] = Field(..., min_length=2, max_length=8)
    role: Optional[str] = Field(default=None, description="Instrument role to score for")


class MaterialCompareResult(BaseModel):
    """Comparison of two or more species for a given role."""
    species_id: str
    name: str
    role_score: Optional[float] = Field(
        default=None,
        description="Role suitability score 0-1 (None if role not specified or insufficient data)"
    )
    radiation_ratio: Optional[float] = None
    specific_moe: Optional[float] = None
    ashby_index: Optional[float] = None
    acoustic_impedance_mrayl: Optional[float] = None
    density_kg_m3: Optional[float] = None
    tone_character: Optional[str] = None
    machining_notes: Optional[MachiningNotes] = None


class MaterialCompareResponse(BaseModel):
    role: Optional[str]
    results: List[MaterialCompareResult]


class MaterialRecommendRequest(BaseModel):
    """Request for POST /api/system/materials/recommend"""
    role: str = Field(..., description="Instrument role: top, back_sides, neck, fretboard, bridge, bracing")
    instrument_type: Optional[str] = Field(default=None, description="acoustic_guitar, electric_guitar, etc.")
    limit: int = Field(default=10, ge=1, le=30)
