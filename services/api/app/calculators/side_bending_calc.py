"""
Side Bending Parameters Calculator — GEOMETRY-010

Species-specific side thickness targets, bending iron temperatures, moisture
preparation, minimum bend radii (physics-derived), spring-back estimation,
and failure mode guidance.

Physics model
=============

MINIMUM BEND RADIUS
    Outer fiber strain when a strip of thickness t is bent to radius R:
        ε = t / (2R)

    Outer fiber stress:
        σ = E × ε = E × t / (2R)

    Elastic failure (cracking) when σ exceeds MOR:
        R_min_elastic = E × t / (2 × MOR)

    With adequate heat and moisture, wood becomes viscoelastic (lignin
    softens above Tg). The practical hot-bending minimum is approximately:
        R_min_hot ≈ 0.45 × R_min_elastic

    The 0.45 factor is empirical — derived from builder practice. It
    represents the combined effect of: (a) partial plasticization of the
    lignin matrix, (b) moisture migration under the bending iron, (c) the
    steel strap support on the outer face. It is not derivable from first
    principles alone.
    Source: Gore & Gilet Vol.1 §3.4; Cumpiano & Natelson pp.180-186

BENDING TEMPERATURE
    Lignin glass transition temperature (Tg) as a function of moisture:
        Tg(MC) ≈ 200 - 8 × MC   [°C, MC in percent]

    Source: Goring, D.A.I. "Thermal softening of lignin, hemicellulose and
    cellulose." Pulp and Paper Magazine of Canada, 1963. Simplified from
    the full relationship by Hillis & Rozsa (1985).

    Bending temperature = Tg + 30°C (to ensure adequate flow above Tg).
    This is cross-validated against published builder recommendations and
    matches empirical values within ±5°C for most species at 8% MC.

SPRING-BACK
    After the side cools on the form, the elastic component of the strain
    recovers. Spring-back depends primarily on:
        1. How effectively the lignin plasticized (density/porosity → heat penetration)
        2. The MOR/E ratio (higher = more elastic energy stored)

    The values in SPECIES_DATA are empirical calibrations from builder
    literature (Cumpiano & Natelson; Siminoff; Gore & Gilet; GAL consensus),
    not pure physics. The physics-based formula (0.5 × MOR × 2R / (E × t))
    gives the right relative ordering but underestimates the effect of
    density on plasticization efficiency. Dense species spring back more
    than the formula alone predicts because their cores stay elastic.

THICKNESS EFFECT ON TEMPERATURE
    Thicker sides require higher temperatures because:
        1. The outer fiber strain (t/2R) increases with t → more stress
        2. More thermal mass to heat through for uniform plasticization
    Temperature increase per 0.5mm above 2.0mm: +5°C (empirical).

Source honesty
==============

PHYSICS-DERIVED (exact given inputs):
    - R_min_elastic = E × t / (2 × MOR)
    - Tg(MC) = 200 - 8 × MC  [simplified model from Goring 1963]
    - T_bend = Tg + 30°C  [30°C above Tg for flow]

EMPIRICAL — wood science literature:
    - E (MOE along grain) and MOR values: USDA Wood Handbook 2021,
      Hoadley "Understanding Wood" 2nd ed. 2000
    - Density values: same sources

EMPIRICAL — builder practice:
    - 0.45 factor for R_min_hot: Gore/Gilet, Cumpiano/Natelson, builder consensus
    - Spring-back values: Cumpiano/Natelson p.185; Siminoff "The Luthier's
      Handbook"; Gore & Gilet Vol.1; GAL Quarterly builder survey
    - Species-specific failure modes: accumulated luthier practice
    - Pre-soak guidance: empirical; varies by kiln vs air-dried wood

References:
    USDA Forest Products Laboratory. "Wood Handbook: Wood as an Engineering
        Material." FPL-GTR-282. Madison, WI, 2021.
    Hoadley, R.B. "Understanding Wood." Taunton Press, 2000.
    Goring, D.A.I. Pulp Paper Mag. Can. 64(12), 1963.
    Gore, T. and Gilet, G. "Contemporary Acoustic Guitar Design and Build"
        Vol. 1. Tonedevil, 2011.
    Cumpiano, W. and Natelson, J. "Guitarmaking: Tradition and Technology."
        Chronicle Books, 1994.
    Siminoff, R. "The Luthier's Handbook." Hal Leonard, 2002.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Wood property database
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WoodSpec:
    """
    Bending-specific properties for a wood species.

    Physical properties (E_GPa, MOR_MPa, density_kg_m3) are loaded from
    wood_species.json when available. The values here are fallbacks for
    species the DB has density data for but is missing E/MOR.

    Bending-specific fields (spring_back_deg, preferred_MC_pct,
    bendability_factor, etc.) are curated here — they are not in the DB.
    """
    # Physical — overridden by DB when available; fallback for DB gaps
    E_GPa:            float = 11.0
    MOR_MPa:          float = 85.0
    density_kg_m3:    int   = 650
    # Bending-specific (not in DB — curated from builder literature)
    spring_back_deg:  float = 6.5
    preferred_MC_pct: float = 9.0
    bendability_factor: float = 0.45
    oil_temp_bonus_c: float = 0.0
    inner_compression_risk: bool = False
    failure_modes:    List[str] = field(default_factory=list)
    notes:            str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Wood species database loader
# ─────────────────────────────────────────────────────────────────────────────

_DB_PATH = (
    Path(__file__).parent.parent
    / "data_registry" / "system" / "materials" / "wood_species.json"
)

def _load_wood_db() -> Dict[str, dict]:
    """Load the canonical wood species database."""
    try:
        with open(_DB_PATH) as f:
            return json.load(f)["species"]
    except (FileNotFoundError, KeyError):
        return {}

_WOOD_DB: Dict[str, dict] = _load_wood_db()

# Alias map: normalize user input and legacy IDs → canonical DB IDs
ALIAS_MAP: Dict[str, str] = {
    "mahogany":               "mahogany_honduran",
    "mahogany_honduras":      "mahogany_honduran",
    "mahogany_honduran":      "mahogany_honduran",
    "mahogany_african":       "mahogany_african",
    "rosewood":               "rosewood_east_indian",
    "rosewood_indian":        "rosewood_east_indian",
    "rosewood_east_indian":   "rosewood_east_indian",
    "rosewood_brazilian":     "rosewood_brazilian",
    "maple":                  "maple_hard",
    "maple_hard":             "maple_hard",
    "maple_soft":             "bigleaf_maple",
    "koa":                    "koa",
    "sapele":                 "sapele",
    "walnut":                 "walnut_black",
    "walnut_black":           "walnut_black",
    "cherry":                 "cherry_black",
    "cherry_black":           "cherry_black",
    "blackwood":              "australian_blackwood",
    "tasmanian_blackwood":    "tasmanian_blackwood",
    "african_blackwood":      "african_blackwood",
    "ziricote":               "ziricote",
    "cocobolo":               "cocobolo",
    "ebony":                  "african_blackwood",
    "cedar":                  "cedar_western_red",
    "cedar_western_red":      "cedar_western_red",
    "spruce":                 "spruce_sitka",
    "spruce_sitka":           "spruce_sitka",
    "ovangkol":               "ovangkol",
    "bubinga":                "bubinga",
    "bloodwood":              "bloodwood",
    "wenge":                  "wenge",
    "ash":                    "european_ash",
    "european_ash":           "european_ash",
    "padauk":                 "african_padauk",
    "african_padauk":         "african_padauk",
    "bocote":                 "bocote",
    "pau_ferro":              "pau_ferro",
    "purpleheart":            "purpleheart",
    "teak":                   "teak",
    "merbau":                 "merbau",
    "zebrawood":              "zebrawood",
}


def _resolve_db_id(species_key: str) -> Optional[str]:
    """Resolve a species key to its canonical DB ID."""
    key = species_key.lower().strip().replace(" ", "_")
    # Try alias map first
    db_id = ALIAS_MAP.get(key, key)
    if db_id in _WOOD_DB:
        return db_id
    # Try direct lookup without alias
    if key in _WOOD_DB:
        return key
    return None


def _get_physical_props(db_id: str, overlay: WoodSpec) -> tuple:
    """
    Get E_GPa, MOR_MPa, density_kg_m3 for a species.

    Priority: DB (if has E and MOR) → overlay fallback → DEFAULT_SPEC fallback.
    This ensures the DB values (from USDA FPL Wood Handbook) are used
    when available, while the module's curated values fill gaps.
    """
    if db_id and db_id in _WOOD_DB:
        phys = _WOOD_DB[db_id].get("physical", {})
        E    = phys.get("modulus_of_elasticity_gpa")
        MOR  = phys.get("modulus_of_rupture_mpa")
        dens = phys.get("density_kg_m3")
        if E and MOR:
            return float(E), float(MOR), int(dens or overlay.density_kg_m3)
        # DB has density but not E/MOR — use overlay values
        return overlay.E_GPa, overlay.MOR_MPa, int(dens or overlay.density_kg_m3)
    return overlay.E_GPa, overlay.MOR_MPa, overlay.density_kg_m3


# ─────────────────────────────────────────────────────────────────────────────
# Bending overlays — curated species-specific bending data
# Keys use canonical DB IDs. E/MOR/density present only where DB lacks them.
# ─────────────────────────────────────────────────────────────────────────────

# Sources: USDA Wood Handbook 2021 (E/MOR fallbacks);
#          builder literature (all bending-specific fields)
SPECIES_DATA: Dict[str, WoodSpec] = {
    "mahogany_honduran": WoodSpec(
        # DB has E=11.97/MOR=98.4 — physical fields here are fallbacks only
        spring_back_deg=5.0, preferred_MC_pct=8.0,
        bendability_factor=0.45,
        failure_modes=["inner surface compression buckle if overheated"],
        notes="Benchmark flexible side wood. Bends easily at standard temp/moisture. "
              "Most forgiving species for beginners.",
    ),
    "mahogany_african": WoodSpec(
        E_GPa=9.4, MOR_MPa=76, density_kg_m3=530,  # DB missing E/MOR
        spring_back_deg=5.5, preferred_MC_pct=8.0,
        bendability_factor=0.46,
        failure_modes=["inner compression buckling on tight waist bends"],
        notes="Very similar to Honduras mahogany. Slightly denser. "
              "Watch for runout in African mahogany — it affects bendability.",
    ),
    "rosewood_east_indian": WoodSpec(
        E_GPa=11.9, MOR_MPa=93, density_kg_m3=830,  # DB missing E/MOR
        spring_back_deg=7.0, preferred_MC_pct=10.0,
        bendability_factor=0.52,
        failure_modes=[
            "surface checking if heated too fast",
            "delamination if moisture is too low before bending",
        ],
        notes="Needs higher MC and slower heating than mahogany. "
              "Dense — needs adequate time for heat to penetrate to core.",
    ),
    "rosewood_brazilian": WoodSpec(
        E_GPa=13.9, MOR_MPa=109, density_kg_m3=835,  # DB missing E/MOR
        spring_back_deg=7.5, preferred_MC_pct=10.0,
        bendability_factor=0.54,
        failure_modes=[
            "surface checking — more brittle than Indian when cold",
            "fiber tear at outer face on tight upper-bout bends",
        ],
        notes="Stiffer than Indian rosewood. More spring-back. "
              "CITES controlled — verify legal provenance.",
    ),
    "maple_hard": WoodSpec(
        # DB has E=13.49/MOR=118.5
        spring_back_deg=8.5, preferred_MC_pct=9.0,
        bendability_factor=0.48,
        failure_modes=[
            "fiber tear at outer face (particularly on figured grain)",
            "more spring-back than expected if underheated",
            "whitening / checking of figure if moisture too low",
        ],
        notes="Most spring-back of common guitar woods. "
              "Figured maple (curly, quilted) — heat very slowly. "
              "Stainless steel strap essential. Overbend by 8-9° at waist.",
    ),
    "bigleaf_maple": WoodSpec(
        # DB has E=10.0/MOR=73.8 — soft maple proxy
        spring_back_deg=6.0, preferred_MC_pct=8.5,
        bendability_factor=0.46,
        failure_modes=["inner surface buckling if overheated"],
        notes="More forgiving than hard maple. Similar bending behavior to mahogany.",
    ),
    "koa": WoodSpec(
        # DB has E=10.37/MOR=87.0
        spring_back_deg=5.5, preferred_MC_pct=8.0,
        bendability_factor=0.44,
        failure_modes=["interlocked grain can cause fiber tear — check grain direction"],
        notes="Bends very well. Similar to mahogany. "
              "Interlocked grain is common — always check runout before bending.",
    ),
    "sapele": WoodSpec(
        # DB has E=12.04/MOR=99.4
        spring_back_deg=6.0, preferred_MC_pct=8.5,
        bendability_factor=0.46,
        failure_modes=[
            "interlocked grain fiber tear — direction reverses along length",
            "inner surface compression crinkle on tight bends",
        ],
        notes="Highly interlocked grain. Check grain direction before each bend — "
              "it reverses along the length.",
    ),
    "walnut_black": WoodSpec(
        # DB has E=11.34/MOR=90.7
        spring_back_deg=7.0, preferred_MC_pct=9.0,
        bendability_factor=0.50,
        failure_modes=[
            "surface checking if moisture too low before bending",
        ],
        notes="Benefits significantly from pre-soaking (20-30 min). "
              "MC is critical — walnut below 7% MC is prone to checking.",
    ),
    "cherry_black": WoodSpec(
        # DB has E=10.24/MOR=78.0
        spring_back_deg=5.5, preferred_MC_pct=8.0,
        bendability_factor=0.45,
        failure_modes=["minor inner face buckling on tight bends"],
        notes="Very forgiving. Bends similarly to mahogany.",
    ),
    "australian_blackwood": WoodSpec(
        # DB has E=14.82/MOR=103.6
        spring_back_deg=8.0, preferred_MC_pct=10.0,
        bendability_factor=0.53,
        failure_modes=[
            "surface checking if heated unevenly",
            "fiber tear on tight bends",
        ],
        notes="Australian blackwood (Acacia melanoxylon). "
              "Dense — treat like hard rosewood. Needs slow heating.",
    ),
    "tasmanian_blackwood": WoodSpec(
        # DB has E=11.82/MOR=96.5
        spring_back_deg=7.5, preferred_MC_pct=9.0,
        bendability_factor=0.50,
        failure_modes=["surface checking if moisture inadequate"],
        notes="Tasmanian blackwood. Slightly easier to bend than Australian blackwood.",
    ),
    "ziricote": WoodSpec(
        E_GPa=13.0, MOR_MPa=100, density_kg_m3=815,  # DB missing E/MOR
        spring_back_deg=7.5, preferred_MC_pct=10.0,
        bendability_factor=0.52,
        failure_modes=[
            "BRITTLE when dry — high fracture risk below 8% MC",
            "surface checking if heated too fast",
        ],
        notes="Moisture content critical — ziricote is unusually brittle when dry. "
              "Pre-soak minimum 30 min. Heat very slowly.",
    ),
    "cocobolo": WoodSpec(
        E_GPa=14.5, MOR_MPa=107, density_kg_m3=1095,  # DB missing E/MOR
        spring_back_deg=9.0, preferred_MC_pct=11.0,
        bendability_factor=0.55,
        oil_temp_bonus_c=15.0,
        failure_modes=[
            "natural oils inhibit plasticization — needs extended soak time",
            "fiber tear on tight upper-bout bends",
            "allergenic dust — respiratory protection mandatory",
        ],
        notes="Very oily — oils inhibit lignin plasticization. "
              "Pre-soak 45-60 min minimum. Respiratory PPE required.",
    ),
    "african_blackwood": WoodSpec(
        # DB has E=17.95/MOR=213.6
        spring_back_deg=12.0, preferred_MC_pct=12.0,
        bendability_factor=0.60,
        failure_modes=[
            "extremely brittle — high cracking risk on any tight bend",
            "very high spring-back — may not hold bend",
        ],
        notes="NOT RECOMMENDED for guitar sides. Extremely hard and brittle. "
              "Ebony proxy — same cautions apply.",
    ),
    "cedar_western_red": WoodSpec(
        # DB has E=7.78/MOR=53.1
        spring_back_deg=3.5, preferred_MC_pct=7.5,
        bendability_factor=0.45,
        inner_compression_risk=True,
        failure_modes=[
            "inner face compression crush on tight bends — very easy to overdrive",
            "delicate — avoid excessive pressure with bending strap",
        ],
        notes="Rarely used for sides. Failure mode is inner compression, not outer "
              "tension — the elastic formula overpredicts minimum radius. "
              "Practical minimum ~50mm.",
    ),
    "spruce_sitka": WoodSpec(
        E_GPa=9.5, MOR_MPa=65, density_kg_m3=425,  # DB missing E/MOR
        spring_back_deg=4.0, preferred_MC_pct=7.5,
        bendability_factor=0.45,
        inner_compression_risk=True,
        failure_modes=[
            "inner compression buckling — spruce compresses rather than bends",
        ],
        notes="Not commonly used for sides. Inner compression limits rather "
              "than outer tension.",
    ),
    "ovangkol": WoodSpec(
        # DB has E=18.6/MOR=140.3 — significantly higher than our original estimate
        spring_back_deg=7.5, preferred_MC_pct=9.5,
        bendability_factor=0.51,
        failure_modes=["interlocked grain — check direction before bending"],
        notes="Common rosewood substitute. DB shows it is stiffer than commonly assumed "
              "(E=18.6GPa). Spring-back adjusted accordingly.",
    ),
    "bubinga": WoodSpec(
        # DB has E=18.41/MOR=168.3 — significantly higher than our original estimate
        spring_back_deg=8.5, preferred_MC_pct=10.0,
        bendability_factor=0.53,
        failure_modes=["surface checking if moisture inadequate"],
        notes="Dense African species. DB confirms very high stiffness (E=18.4GPa). "
              "Treat aggressively — more like wenge than rosewood.",
    ),
    "bloodwood": WoodSpec(
        # DB has E=20.78/MOR=174.4 — much stiffer than our original estimate
        spring_back_deg=9.5, preferred_MC_pct=10.0,
        bendability_factor=0.56,
        failure_modes=[
            "hard and dense — high breakage risk on tight bends",
            "surface checking common",
        ],
        notes="Very dense and stiff per DB (E=20.8GPa). "
              "Keep thickness at lower end (1.8-2.0mm). "
              "Spring-back revised upward from DB values.",
    ),
    "wenge": WoodSpec(
        # DB has E=14.75/MOR=136.9
        spring_back_deg=8.0, preferred_MC_pct=10.0,
        bendability_factor=0.52,
        failure_modes=[
            "coarse open grain can chip or splinter during bending",
            "sliver hazard — wear gloves",
        ],
        notes="Open coarse grain — splintering risk at inner face. "
              "Wear gloves throughout.",
    ),
    "african_padauk": WoodSpec(
        # DB has E=13.07/MOR=126.7
        spring_back_deg=7.0, preferred_MC_pct=9.0,
        bendability_factor=0.50,
        failure_modes=["color bleeds into adjacent wood when wet — keep separate"],
        notes="Dense orange dye bleeds when wet — keep isolated during soaking.",
    ),
    "european_ash": WoodSpec(
        # DB has E=12.31/MOR=103.6
        spring_back_deg=8.0, preferred_MC_pct=9.0,
        bendability_factor=0.50,
        failure_modes=["open grain fiber tear on tight bends"],
        notes="Ring-porous wood — heat penetration uneven; heat slowly.",
    ),
    "bocote": WoodSpec(
        # DB has E=12.19/MOR=114.4
        spring_back_deg=7.0, preferred_MC_pct=9.0,
        bendability_factor=0.50,
        failure_modes=["interlocked grain — check direction"],
        notes="Mexican rosewood family. Bends moderately well.",
    ),
    "pau_ferro": WoodSpec(
        # DB has E=14.0/MOR=131.0
        spring_back_deg=8.0, preferred_MC_pct=9.5,
        bendability_factor=0.51,
        failure_modes=["surface checking if inadequate moisture"],
        notes="Rosewood substitute. Stiff — use DB E=14.0GPa for accurate radius calc.",
    ),
    "purpleheart": WoodSpec(
        # DB has E=16.7/MOR=168.6
        spring_back_deg=9.0, preferred_MC_pct=10.0,
        bendability_factor=0.54,
        failure_modes=["high stiffness — brittle on tight bends"],
        notes="Very stiff per DB (E=16.7GPa). Treat conservatively.",
    ),
    "teak": WoodSpec(
        # DB has E=12.28/MOR=97.1
        spring_back_deg=7.5, preferred_MC_pct=9.5,
        bendability_factor=0.50,
        oil_temp_bonus_c=10.0,  # teak has natural oils
        failure_modes=["oily — oils inhibit plasticization, similar to cocobolo"],
        notes="Oily species — moderate pre-soak (25-30 min). "
              "Extra temperature margin for oils.",
    ),
}


# Default for unlisted species — conservative mid-range values
DEFAULT_SPEC = WoodSpec(
    E_GPa=11.0, MOR_MPa=85, density_kg_m3=650,
    spring_back_deg=6.5, preferred_MC_pct=9.0,
    notes="Unknown species — using conservative defaults. "
          "Test a scrap piece before bending.",
)



# ─────────────────────────────────────────────────────────────────────────────
# Side thickness targets by instrument type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ThicknessTarget:
    min_mm: float
    max_mm: float
    optimal_mm: float
    rationale: str


THICKNESS_TARGETS: Dict[str, ThicknessTarget] = {
    "steel_string_acoustic": ThicknessTarget(
        min_mm=2.0, max_mm=2.5, optimal_mm=2.3,
        rationale="Structural stiffness for steel string tension; "
                  "thick enough to take finish without telegraphing grain.",
    ),
    "classical": ThicknessTarget(
        min_mm=1.8, max_mm=2.2, optimal_mm=2.0,
        rationale="Lower string tension; thinner sides reduce mass and "
                  "improve resonance coupling. Nylon string instruments "
                  "tolerate and benefit from lighter construction.",
    ),
    "archtop_jazz": ThicknessTarget(
        min_mm=2.5, max_mm=3.2, optimal_mm=2.8,
        rationale="Thicker sides for archtop structural integrity and "
                  "the deeper body depth typical of jazz archtops. "
                  "Sustain and projection benefit from stiffer sides.",
    ),
    "electric_hollow": ThicknessTarget(
        min_mm=1.8, max_mm=2.3, optimal_mm=2.0,
        rationale="Thin for light feel; not acoustically primary. "
                  "Adequate for glue joint strength.",
    ),
    "ukulele": ThicknessTarget(
        min_mm=1.5, max_mm=2.0, optimal_mm=1.8,
        rationale="Small instrument; thin sides keep overall weight low "
                  "and allow tight ukulele waist bends.",
    ),
    "parlor": ThicknessTarget(
        min_mm=2.0, max_mm=2.4, optimal_mm=2.2,
        rationale="Parlor waist radii are tight (45-55mm); thinner sides "
                  "reduce bending stress at the waist. Not as thin as "
                  "classical but keep toward lower end.",
    ),
    "12_string": ThicknessTarget(
        min_mm=2.3, max_mm=2.8, optimal_mm=2.5,
        rationale="Higher string tension; stiffer sides better resist the "
                  "increased load. Thick end of the range for rosewood/maple.",
    ),
    "bass_acoustic": ThicknessTarget(
        min_mm=2.5, max_mm=3.5, optimal_mm=3.0,
        rationale="Deep body and high string tension require robust sides.",
    ),
    "mandolin_f5": ThicknessTarget(
        min_mm=1.5, max_mm=2.0, optimal_mm=1.8,
        rationale="Small body; very tight upper bout bends. "
                  "Keep thin for bendability.",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Bending method parameters
# ─────────────────────────────────────────────────────────────────────────────

BENDING_METHODS = {
    "bending_iron": {
        "label": "Bending Iron / Pipe Iron",
        "description": "Curved metal form heated by internal element or pipe. "
                       "Builder moves wood across the surface.",
        "temp_note": "Iron surface at T_bend. Check with thermocouple or "
                     "paper-browning test (~150°C). Move slowly — dwell time "
                     "matters more than speed.",
        "soak_min": 5,
        "soak_max": 15,
        "best_for": ["waist bends", "moderate curves", "repair work"],
        "risks": ["scorching if held too long", "uneven heating if moved too fast"],
    },
    "fox_bender": {
        "label": "Fox Bender (Side Bending Machine)",
        "description": "Heated form with clamping cauls. Side clamped in shape "
                       "during cooling for consistent results.",
        "temp_note": "Set element to T_bend + 10°C to account for heat loss "
                     "to the cauls. Clamp while still hot; release after full cooling.",
        "soak_min": 10,
        "soak_max": 20,
        "best_for": ["production runs", "consistent results", "complex curves"],
        "risks": ["overheating if element stays on too long"],
        "overbend_note": "Form must overbend by spring_back_deg to account for "
                         "spring-back on release.",
    },
    "pipe_bender": {
        "label": "Wet Pipe / Steam Bending",
        "description": "Tube of water placed inside the pipe generates steam "
                       "as the pipe heats. Steam and heat together.",
        "temp_note": "Outer pipe at 170-190°C; inner steam near 100°C. "
                     "The combination gives very effective plasticization.",
        "soak_min": 0,
        "soak_max": 5,
        "best_for": ["tight waist bends", "dense species"],
        "risks": ["water can spit unexpectedly", "temperature less controllable"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Core physics functions
# ─────────────────────────────────────────────────────────────────────────────

def r_min_elastic_mm(E_GPa: float, MOR_MPa: float, thickness_mm: float) -> float:
    """
    Minimum bend radius before elastic failure (cracking without heat).
    R_min = E × t / (2 × MOR)   [exact, from fiber stress model]
    """
    return (E_GPa * 1e9) * (thickness_mm / 1000.0) / (2.0 * MOR_MPa * 1e6) * 1000.0


def r_min_hot_mm(
    E_GPa: float,
    MOR_MPa: float,
    thickness_mm: float,
    bendability_factor: float = 0.45,
) -> float:
    """
    Practical minimum bend radius for hot bending with steel strap.
    R_min_hot = R_min_elastic × bendability_factor

    The bendability_factor (default 0.45) is species-specific: accounts for
    density, oils, and grain structure that affect practical hot-bending.
    Higher factor = harder to bend in practice than elastic formula predicts.
    """
    return r_min_elastic_mm(E_GPa, MOR_MPa, thickness_mm) * bendability_factor


def lignin_tg_celsius(mc_pct: float) -> float:
    """
    Lignin glass transition temperature at given moisture content.
    Tg(MC) ≈ 200 - 8 × MC   [simplified from Goring 1963]
    """
    return 200.0 - 8.0 * mc_pct


def bending_temperature_celsius(
    mc_pct: float,
    thickness_mm: float,
    density_kg_m3: float = 600,
    oil_temp_bonus_c: float = 0.0,
    ref_thickness_mm: float = 2.0,
) -> float:
    """
    Recommended bending iron temperature.

    T_bend = Tg(MC) + 30°C (minimum for adequate lignin flow)
           + density_margin  (denser wood needs more surface heat for core penetration)
           + oil_bonus        (oily species resist plasticization)
           + thickness_adj    (thicker = more thermal mass)

    density_margin = max(0, (density - 500) / 100 × 5°C)  [empirical]
    """
    tg = lignin_tg_celsius(mc_pct)
    base_temp = tg + 30.0
    density_margin = max(0.0, (density_kg_m3 - 500) / 100.0 * 5.0)
    thickness_adj = max(0.0, (thickness_mm - ref_thickness_mm) / 0.5 * 5.0)
    return base_temp + density_margin + oil_temp_bonus_c + thickness_adj


def spring_back_for_thickness(
    base_spring_back_deg: float,
    thickness_mm: float,
    ref_thickness_mm: float = 2.3,
) -> float:
    """
    Adjust empirical spring-back for actual thickness vs reference.
    Spring-back scales roughly linearly with thickness (more material = more elastic recovery).
    +0.5° per 0.5mm above reference.
    """
    adj = (thickness_mm - ref_thickness_mm) / 0.5 * 0.5
    return round(max(1.0, base_spring_back_deg + adj), 1)


def assess_bend_risk(
    waist_radius_mm: float,
    r_min_hot: float,
) -> Tuple[str, Optional[str]]:
    """
    Assign risk level for a given waist radius vs minimum hot radius.
    Returns (risk_level, warning_message).
    """
    yellow_threshold = r_min_hot * 0.85
    if waist_radius_mm >= r_min_hot:
        return "GREEN", None
    elif waist_radius_mm >= yellow_threshold:
        return "YELLOW", (
            f"Radius {waist_radius_mm:.0f}mm is within 15% of "
            f"minimum safe radius ({r_min_hot:.0f}mm). "
            "Reduce thickness by 0.2-0.3mm or increase moisture content to reduce risk."
        )
    else:
        return "RED", (
            f"Radius {waist_radius_mm:.0f}mm is below minimum safe radius "
            f"({r_min_hot:.0f}mm) for this species/thickness. "
            "Reduce thickness, increase moisture, or use a different species."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Output dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BendingPlan:
    """Complete bending plan for a species/thickness/body combination."""
    species:              str
    side_thickness_mm:    float
    waist_radius_mm:      float
    instrument_type:      str

    # Physics-derived
    r_min_elastic_mm:     float
    r_min_hot_mm:         float
    temp_c:               float
    lignin_tg_c:          float

    # From species data
    moisture_pct:         float
    spring_back_deg:      float
    density_kg_m3:        int

    # Assessment
    risk:                 str      # GREEN | YELLOW | RED
    notes:                List[str]
    failure_modes:        List[str]

    # Preparation guidance
    pre_soak_min:         int      # minutes of soaking recommended
    pre_soak_max:         int
    bending_method_notes: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SideThicknessSpec:
    """Recommended side thickness for an instrument/species combination."""
    instrument_type:  str
    species:          str
    target_mm:        float
    min_mm:           float
    max_mm:           float
    note:             str
    rationale:        str

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# Main computation functions
# ─────────────────────────────────────────────────────────────────────────────

def compute_bending_parameters(
    species: str,
    side_thickness_mm: float,
    waist_radius_mm: float,
    instrument_type: str = "steel_string_acoustic",
    bending_method: str = "bending_iron",
) -> BendingPlan:
    """
    Compute complete bending parameters for a species/thickness/body combination.

    Args:
        species:           Wood species key (see SPECIES_DATA)
        side_thickness_mm: Side thickness in mm
        waist_radius_mm:   Tightest bend radius (guitar waist) in mm
        instrument_type:   Instrument type for thickness validation
        bending_method:    'bending_iron' | 'fox_bender' | 'pipe_bender'

    Returns:
        BendingPlan with complete preparation and risk assessment.
    """
    key    = species.lower().strip().replace(" ", "_")
    db_id  = _resolve_db_id(key)
    # Get bending overlay (or default)
    overlay = SPECIES_DATA.get(db_id) or SPECIES_DATA.get(key) or DEFAULT_SPEC
    is_known = (db_id in SPECIES_DATA or key in SPECIES_DATA or
                (db_id is not None and db_id in _WOOD_DB))

    # Physical properties: DB first, overlay fallback
    E_GPa, MOR_MPa, density = _get_physical_props(db_id, overlay)

    # Physics-derived values
    r_el  = r_min_elastic_mm(E_GPa, MOR_MPa, side_thickness_mm)
    r_hot = r_min_hot_mm(E_GPa, MOR_MPa, side_thickness_mm,
                         bendability_factor=overlay.bendability_factor)
    tg    = lignin_tg_celsius(overlay.preferred_MC_pct)
    temp  = bending_temperature_celsius(
        overlay.preferred_MC_pct, side_thickness_mm,
        density_kg_m3=density,
        oil_temp_bonus_c=overlay.oil_temp_bonus_c,
    )
    sb = spring_back_for_thickness(overlay.spring_back_deg, side_thickness_mm)

    notes: List[str] = []

    if not is_known:
        notes.append(
            f"Unknown species '{species}' — using conservative defaults. "
            "Test a scrap piece before bending."
        )

    # Thickness check
    instr_key = instrument_type.lower().strip().replace(" ", "_")
    tt = THICKNESS_TARGETS.get(instr_key)
    if tt:
        if side_thickness_mm < tt.min_mm:
            notes.append(
                f"Thickness {side_thickness_mm}mm is below minimum "
                f"({tt.min_mm}mm) for {instrument_type}. Risk of breakage "
                "and poor glue surface. Sand to final thickness after bending."
            )
        elif side_thickness_mm > tt.max_mm:
            notes.append(
                f"Thickness {side_thickness_mm}mm exceeds maximum "
                f"({tt.max_mm}mm) for {instrument_type}. "
                "Will be harder to bend — expect more heat and moisture needed."
            )
        else:
            notes.append(
                f"Thickness {side_thickness_mm}mm is within target range "
                f"({tt.min_mm}–{tt.max_mm}mm) for {instrument_type}. ✓"
            )

    # Risk assessment
    risk, risk_note = assess_bend_risk(waist_radius_mm, r_hot)
    if risk_note:
        notes.append(risk_note)

    # Species-specific note
    if overlay.notes:
        notes.append(overlay.notes)

    # Method-specific notes
    method_info = BENDING_METHODS.get(bending_method, BENDING_METHODS["bending_iron"])
    method_note = (
        f"{method_info['label']}: {method_info['temp_note']} "
        f"Pre-soak: {method_info['soak_min']}–{method_info['soak_max']} min."
    )
    if bending_method == "fox_bender":
        method_note += f" Overbend form by {sb}° to account for spring-back."

    # Pre-conditioning guidance — use canonical DB IDs
    mc = overlay.preferred_MC_pct
    soak_min = method_info["soak_min"]
    soak_max = method_info["soak_max"]
    if db_id in ("cocobolo", "teak"):
        soak_min, soak_max = 45, 60
        notes.append("Oily species — extended pre-soak required (45-60 min).")
    elif db_id in ("rosewood_east_indian", "rosewood_brazilian",
                   "australian_blackwood", "african_blackwood", "ziricote",
                   "bubinga", "ovangkol", "wenge"):
        soak_min, soak_max = max(soak_min, 20), max(soak_max, 30)
        notes.append("Dense species — pre-soak at least 20-30 min for full moisture penetration.")

    return BendingPlan(
        species=species,
        side_thickness_mm=side_thickness_mm,
        waist_radius_mm=waist_radius_mm,
        instrument_type=instrument_type,
        r_min_elastic_mm=round(r_el, 1),
        r_min_hot_mm=round(r_hot, 1),
        temp_c=round(temp, 0),
        lignin_tg_c=round(tg, 0),
        moisture_pct=mc,
        spring_back_deg=sb,
        density_kg_m3=density,
        risk=risk,
        notes=notes,
        failure_modes=overlay.failure_modes,
        pre_soak_min=soak_min,
        pre_soak_max=soak_max,
        bending_method_notes=method_note,
    )


def check_side_thickness(
    instrument_type: str,
    species: str,
) -> SideThicknessSpec:
    """
    Recommended side thickness for an instrument/species combination.

    Dense, hard-to-bend species (maple, rosewood, blackwood) are
    recommended toward the lower end of the range for the instrument type,
    as thinner sides reduce bending stress. Soft, pliable species may
    use the upper end for better durability.
    """
    instr_key = instrument_type.lower().strip().replace(" ", "_")
    sp_key    = species.lower().strip().replace(" ", "_")

    tt = THICKNESS_TARGETS.get(instr_key)
    if not tt:
        tt = THICKNESS_TARGETS["steel_string_acoustic"]
        instr_note = f"Unknown instrument type '{instrument_type}' — using steel-string defaults. "
    else:
        instr_note = ""

    # Resolve through DB and overlay
    db_id   = _resolve_db_id(sp_key)
    overlay = SPECIES_DATA.get(db_id) or SPECIES_DATA.get(sp_key)
    _, _, density = _get_physical_props(db_id, overlay or DEFAULT_SPEC)

    # Species-specific thickness adjustment within the instrument range
    optimal = tt.optimal_mm
    note_parts = [instr_note] if instr_note else []

    if db_id or overlay:
        if density > 650:
            optimal = tt.min_mm + (tt.optimal_mm - tt.min_mm) * 0.3
            note_parts.append(
                f"Dense species ({density} kg/m³) — recommend toward minimum "
                f"({tt.min_mm}mm) to reduce bending stress. "
                f"Minimum bend radius scales with thickness."
            )
        elif density < 500:
            optimal = tt.optimal_mm + (tt.max_mm - tt.optimal_mm) * 0.5
            note_parts.append(
                f"Light species ({density} kg/m³) — use upper end of range "
                f"({tt.max_mm}mm) for structural durability."
            )
        if overlay and overlay.notes:
            note_parts.append(overlay.notes)
    else:
        note_parts.append(f"Unknown species '{species}' — using standard target.")

    note_parts.append(tt.rationale)

    return SideThicknessSpec(
        instrument_type=instrument_type,
        species=species,
        target_mm=round(optimal, 2),
        min_mm=tt.min_mm,
        max_mm=tt.max_mm,
        note="; ".join(note_parts),
        rationale=tt.rationale,
    )


def compare_species_for_body(
    instrument_type: str,
    waist_radius_mm: float,
    thickness_mm: float,
    species_list: Optional[List[str]] = None,
) -> List[dict]:
    """
    Compare multiple species for bendability at a given radius and thickness.

    When species_list is None, uses all species that have bending overlays.
    Returns list sorted from easiest to hardest to bend.
    Physical properties (E, MOR, density) are drawn from wood_species.json
    where available, falling back to curated overlay values.
    """
    if species_list is None:
        species_list = list(SPECIES_DATA.keys())

    results = []
    for sp in species_list:
        key    = sp.lower().strip().replace(" ", "_")
        db_id  = _resolve_db_id(key)
        overlay = SPECIES_DATA.get(db_id) or SPECIES_DATA.get(key) or DEFAULT_SPEC
        E_GPa, MOR_MPa, density = _get_physical_props(db_id, overlay)

        r_hot = r_min_hot_mm(E_GPa, MOR_MPa, thickness_mm,
                             bendability_factor=overlay.bendability_factor)
        risk, _ = assess_bend_risk(waist_radius_mm, r_hot)
        temp = bending_temperature_celsius(
            overlay.preferred_MC_pct, thickness_mm,
            density_kg_m3=density,
            oil_temp_bonus_c=overlay.oil_temp_bonus_c,
        )
        sb = spring_back_for_thickness(overlay.spring_back_deg, thickness_mm)

        # Identify where E/MOR came from
        db_sp  = _WOOD_DB.get(db_id or "", {})
        phys   = db_sp.get("physical", {})
        source = "db" if phys.get("modulus_of_elasticity_gpa") else "overlay"

        results.append({
            "species":              sp,
            "db_id":                db_id,
            "risk":                 risk,
            "r_min_hot_mm":         round(r_hot, 1),
            "temp_c":               round(temp, 0),
            "spring_back_deg":      sb,
            "density_kg_m3":        density,
            "E_GPa":                round(E_GPa, 2),
            "MOR_MPa":              round(MOR_MPa, 1),
            "props_source":         source,
            "inner_compression":    overlay.inner_compression_risk,
        })

    # Sort: GREEN first, then by r_min_hot ascending
    risk_order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    results.sort(key=lambda x: (risk_order[x["risk"]], x["r_min_hot_mm"]))
    return results


def list_supported_species() -> List[str]:
    """
    Return all species that have bending overlays (curated bending guidance).
    These are the species with species-specific spring-back, failure modes, etc.
    For any other DB species, compute_bending_parameters will still work
    using DB physical properties with default bending parameters.
    """
    return list(SPECIES_DATA.keys())


def list_all_bendable_species() -> List[str]:
    """
    Return all species in the wood DB that have E and MOR data,
    making them calculable even without a bending overlay.
    """
    return [
        sp_id for sp_id, sp in _WOOD_DB.items()
        if sp.get("physical", {}).get("modulus_of_elasticity_gpa")
        and sp.get("physical", {}).get("modulus_of_rupture_mpa")
    ]


def list_instrument_types() -> List[str]:
    return list(THICKNESS_TARGETS.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY EXPORTS
# These maintain API compatibility with legacy tests and code
# ═══════════════════════════════════════════════════════════════════════════════

# Legacy alias: BENDING_PARAMS maps to BENDING_METHODS
BENDING_PARAMS = BENDING_METHODS

# Legacy alias: SIDE_THICKNESS_TARGETS_MM generated from THICKNESS_TARGETS
SIDE_THICKNESS_TARGETS_MM = {
    key: {
        "nominal_mm": tt.optimal_mm,
        "min_mm": tt.min_mm,
        "max_mm": tt.max_mm,
    }
    for key, tt in THICKNESS_TARGETS.items()
}
