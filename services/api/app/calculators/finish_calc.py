"""
Finish Schedule Calculator — CONSTRUCTION-007.

Calculates finish schedules for various finish types including:
- Nitrocellulose lacquer
- Polyurethane
- Oil finishes
- French polish (shellac)

Key relationships:
- Grain fill coats = pore_depth_mm / coat_fill_mm_per_layer
- Total dry time based on finish type and coat count
- Sanding schedule between coats
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, List, Optional, Any


# ─── Finish Types ────────────────────────────────────────────────────────────

class FinishType(str, Enum):
    """Available finish types."""
    NITROCELLULOSE = "nitro"
    POLYURETHANE = "poly"
    WATER_BASED_POLY = "water_poly"
    OIL = "oil"
    TUNG_OIL = "tung_oil"
    FRENCH_POLISH = "french_polish"
    WAX = "wax"


# ─── Species Pore Data ───────────────────────────────────────────────────────
# Pore depth estimates in mm for grain filling calculation

PORE_DEPTH_MM: Dict[str, float] = {
    # Large pores (need significant filling)
    "rosewood": 0.30,
    "indian_rosewood": 0.30,
    "brazilian_rosewood": 0.32,
    "mahogany": 0.20,
    "honduran_mahogany": 0.20,
    "african_mahogany": 0.22,
    "sapele": 0.18,
    "walnut": 0.25,
    "ash": 0.35,
    "oak": 0.40,
    "koa": 0.22,
    "bubinga": 0.20,
    "cocobolo": 0.15,

    # Medium pores
    "cherry": 0.12,
    "alder": 0.10,
    "basswood": 0.08,

    # Small/closed pores (minimal filling needed)
    "maple": 0.05,
    "ebony": 0.03,
    "spruce": 0.02,
    "cedar": 0.02,
    "sitka_spruce": 0.02,
}


# ─── Finish Properties ───────────────────────────────────────────────────────
# Fill per coat and dry times by finish type

FINISH_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "nitro": {
        "fill_mm_per_coat": 0.025,
        "dry_time_between_coats_hours": 2,
        "cure_time_days": 30,
        "recoat_window_hours": 4,
        "recommended_coats": 8,
        "sanding_grit_sequence": [320, 400, 600, 800, 1000, 1500, 2000],
        "notes": "Classic vintage tone, ages beautifully, labor intensive",
    },
    "poly": {
        "fill_mm_per_coat": 0.040,
        "dry_time_between_coats_hours": 4,
        "cure_time_days": 7,
        "recoat_window_hours": 24,
        "recommended_coats": 4,
        "sanding_grit_sequence": [320, 400, 600],
        "notes": "Durable, fast cure, plastic appearance if too thick",
    },
    "water_poly": {
        "fill_mm_per_coat": 0.030,
        "dry_time_between_coats_hours": 2,
        "cure_time_days": 14,
        "recoat_window_hours": 4,
        "recommended_coats": 5,
        "sanding_grit_sequence": [320, 400, 600],
        "notes": "Low VOC, raises grain on first coat",
    },
    "oil": {
        "fill_mm_per_coat": 0.005,
        "dry_time_between_coats_hours": 24,
        "cure_time_days": 7,
        "recoat_window_hours": 48,
        "recommended_coats": 3,
        "sanding_grit_sequence": [400, 600],
        "notes": "Natural feel, easy repair, minimal protection",
    },
    "tung_oil": {
        "fill_mm_per_coat": 0.008,
        "dry_time_between_coats_hours": 24,
        "cure_time_days": 14,
        "recoat_window_hours": 48,
        "recommended_coats": 5,
        "sanding_grit_sequence": [400, 600],
        "notes": "Water resistant, natural look, long cure",
    },
    "french_polish": {
        "fill_mm_per_coat": 0.010,
        "dry_time_between_coats_hours": 0.5,
        "cure_time_days": 21,
        "recoat_window_hours": 1,
        "recommended_coats": 30,
        "sanding_grit_sequence": [600, 800, 1000],
        "notes": "Classical guitars, beautiful depth, fragile",
    },
    "wax": {
        "fill_mm_per_coat": 0.002,
        "dry_time_between_coats_hours": 1,
        "cure_time_days": 1,
        "recoat_window_hours": 24,
        "recommended_coats": 3,
        "sanding_grit_sequence": [400],
        "notes": "Topcoat only, minimal protection, natural feel",
    },
}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class CoatSpec:
    """Specification for a single coat."""
    coat_number: int
    coat_type: str  # "grain_fill", "sealer", "build", "topcoat"
    material: str
    dry_time_hours: float
    sand_after: bool
    sand_grit: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SandingStep:
    """Sanding step between coats."""
    after_coat: int
    grit: int
    wet_sand: bool
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinishSchedule:
    """Complete finish schedule."""
    finish_type: str
    wood_species: str
    coats: List[CoatSpec]
    total_coats: int
    grain_fill_coats: int
    build_coats: int
    total_dry_time_hours: float
    total_cure_days: int
    sanding_schedule: List[SandingStep]
    final_grit: int
    gate: str
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["coats"] = [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.coats]
        d["sanding_schedule"] = [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.sanding_schedule]
        return d


# ─── Core Functions ──────────────────────────────────────────────────────────

def compute_finish_schedule(
    finish_type: str,
    wood_species: str,
    target_build_mm: float = 0.15,
    include_grain_fill: bool = True,
) -> FinishSchedule:
    """
    Compute a complete finish schedule.

    Args:
        finish_type: Type of finish (nitro, poly, oil, etc.)
        wood_species: Wood species for grain fill calculation
        target_build_mm: Target finish thickness (default 0.15mm)
        include_grain_fill: Whether to include grain fill coats

    Returns:
        FinishSchedule with coat sequence and timing

    Raises:
        ValueError: If finish_type is unknown
    """
    finish_key = finish_type.lower().replace("-", "_").replace(" ", "_")

    if finish_key not in FINISH_PROPERTIES:
        raise ValueError(
            f"Unknown finish type: '{finish_type}'. "
            f"Supported: {list(FINISH_PROPERTIES.keys())}"
        )

    props = FINISH_PROPERTIES[finish_key]
    species_key = wood_species.lower().replace("-", "_").replace(" ", "_")

    # Get pore depth for grain fill calculation
    pore_depth = PORE_DEPTH_MM.get(species_key, 0.10)  # default for unknown

    notes: List[str] = []
    coats: List[CoatSpec] = []
    sanding_schedule: List[SandingStep] = []

    # Calculate grain fill coats needed
    fill_per_coat = props["fill_mm_per_coat"]
    grain_fill_coats = 0

    # Penetrating finishes don't fill grain - they soak in
    penetrating_finishes = {"oil", "tung_oil", "wax"}

    if include_grain_fill and pore_depth > 0.05 and finish_key not in penetrating_finishes:
        grain_fill_coats = int((pore_depth / fill_per_coat) + 0.5)
        grain_fill_coats = max(1, min(grain_fill_coats, 6))  # cap at 6

        for i in range(grain_fill_coats):
            coats.append(CoatSpec(
                coat_number=i + 1,
                coat_type="grain_fill",
                material=finish_key,
                dry_time_hours=props["dry_time_between_coats_hours"],
                sand_after=(i == grain_fill_coats - 1),
                sand_grit=320 if i == grain_fill_coats - 1 else None,
            ))

        if grain_fill_coats > 0:
            sanding_schedule.append(SandingStep(
                after_coat=grain_fill_coats,
                grit=320,
                wet_sand=False,
                notes="Level grain fill",
            ))

    # Calculate build coats
    # Penetrating finishes don't build film thickness - use recommended_coats directly
    if finish_key in penetrating_finishes:
        build_coats = props["recommended_coats"]
    else:
        build_coats = int((target_build_mm / fill_per_coat) + 0.5)
        build_coats = max(props["recommended_coats"], build_coats)

    # Add sealer coat
    sealer_coat_num = grain_fill_coats + 1
    coats.append(CoatSpec(
        coat_number=sealer_coat_num,
        coat_type="sealer",
        material=finish_key,
        dry_time_hours=props["dry_time_between_coats_hours"],
        sand_after=True,
        sand_grit=400,
    ))
    sanding_schedule.append(SandingStep(
        after_coat=sealer_coat_num,
        grit=400,
        wet_sand=False,
        notes="Scuff sealer",
    ))

    # Add build coats
    for i in range(build_coats - 2):  # -2 for sealer and final topcoat
        coat_num = sealer_coat_num + i + 1
        sand_after = (i % 3 == 2)  # sand every 3rd build coat
        coats.append(CoatSpec(
            coat_number=coat_num,
            coat_type="build",
            material=finish_key,
            dry_time_hours=props["dry_time_between_coats_hours"],
            sand_after=sand_after,
            sand_grit=400 if sand_after else None,
        ))
        if sand_after:
            sanding_schedule.append(SandingStep(
                after_coat=coat_num,
                grit=400,
                wet_sand=False,
                notes="Level build coats",
            ))

    # Final topcoat
    final_coat_num = len(coats) + 1
    coats.append(CoatSpec(
        coat_number=final_coat_num,
        coat_type="topcoat",
        material=finish_key,
        dry_time_hours=props["dry_time_between_coats_hours"],
        sand_after=True,
        sand_grit=props["sanding_grit_sequence"][-1],
    ))

    # Final leveling and buffing schedule
    for grit in props["sanding_grit_sequence"]:
        sanding_schedule.append(SandingStep(
            after_coat=final_coat_num,
            grit=grit,
            wet_sand=(grit >= 600),
            notes="Final leveling" if grit < 1000 else "Polish prep",
        ))

    # Calculate totals
    total_coats = len(coats)
    total_dry_time = sum(c.dry_time_hours for c in coats)

    # Gate assessment
    gate = "GREEN"
    if total_coats > 15:
        gate = "YELLOW"
        notes.append(f"High coat count ({total_coats}), consider thicker coats")
    if finish_key == "french_polish":
        notes.append("French polish requires experienced technique")
    if pore_depth > 0.25:
        notes.append(f"Large pores ({pore_depth}mm), consider pore filler")

    notes.append(props["notes"])

    return FinishSchedule(
        finish_type=finish_key,
        wood_species=species_key,
        coats=coats,
        total_coats=total_coats,
        grain_fill_coats=grain_fill_coats,
        build_coats=build_coats,
        total_dry_time_hours=round(total_dry_time, 1),
        total_cure_days=props["cure_time_days"],
        sanding_schedule=sanding_schedule,
        final_grit=props["sanding_grit_sequence"][-1],
        gate=gate,
        notes=notes,
    )


def estimate_grain_fill_coats(
    wood_species: str,
    finish_type: str = "nitro",
) -> int:
    """Estimate number of coats needed to fill grain."""
    species_key = wood_species.lower().replace("-", "_").replace(" ", "_")
    finish_key = finish_type.lower().replace("-", "_").replace(" ", "_")

    pore_depth = PORE_DEPTH_MM.get(species_key, 0.10)

    if finish_key not in FINISH_PROPERTIES:
        raise ValueError(f"Unknown finish type: '{finish_type}'")

    fill_per_coat = FINISH_PROPERTIES[finish_key]["fill_mm_per_coat"]

    if pore_depth <= 0.05:
        return 0  # Closed pore, no filling needed

    coats = int((pore_depth / fill_per_coat) + 0.5)
    return max(1, min(coats, 10))


def list_finish_types() -> List[str]:
    """Return list of supported finish types."""
    return list(FINISH_PROPERTIES.keys())


def list_wood_species_pores() -> Dict[str, float]:
    """Return pore depth by species."""
    return PORE_DEPTH_MM.copy()


def get_finish_properties(finish_type: str) -> Dict[str, Any]:
    """Get properties for a finish type."""
    finish_key = finish_type.lower().replace("-", "_").replace(" ", "_")

    if finish_key not in FINISH_PROPERTIES:
        raise ValueError(f"Unknown finish type: '{finish_type}'")

    return FINISH_PROPERTIES[finish_key].copy()
