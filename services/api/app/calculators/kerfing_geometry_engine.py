# services/api/app/calculators/kerfing_calc.py
"""
Kerfing Geometry Calculator — GEOMETRY-003

Computes kerfed-lining specifications for flat-top and archtop guitars.
Kerfed lining (also called kerfing) is the flexible material that glues
the top and back plates to the sides. The kerfs allow rigid wood stock
to bend to the body contour.

Physical model:
    The kerfing stock is a rectangular section (width × height) with
    parallel saw cuts (kerfs) running across the width, leaving a thin
    web of uncut wood that acts as a flexible hinge.

    Geometric minimum bend radius:
        R_geom = web_thickness × kerf_spacing / kerf_width
        where:
            web_thickness = stock_height × (1 - kerf_depth_fraction)
            kerf_spacing  = center-to-center kerf spacing (mm)
            kerf_width    = actual saw blade kerf width (mm)

    Material failure limit (secondary):
        R_mat = E_C × web_thickness / (2 × MOR_C)
        where E_C and MOR_C are cross-grain modulus and MOR.
        This limit is rarely governing for standard guitar kerfing dimensions.

    In practice: R_min = max(R_geom, R_mat)
    For typical guitar dimensions both limits are well below the tightest
    guitar bend radius (~45mm for archtop waist), so standard kerfing
    works easily if dimensions are correct.

    Glue area per unit length:
        A_glue/mm = stock_height - (kerf_depth × kerf_width / kerf_spacing)
        Total: A_glue = A_glue/mm × body_perimeter_mm

References:
    - Gore & Gilet, Vol.1, Ch.4 (kerfing dimensions)
    - BACKLOG.md GEOMETRY-003
    - martin_d28_1937.py: SIDE_PROFILE_WITH_KERFING_IN confirms kerfing
      adds ~6.35mm (0.25") to side depth measurements
    - jumbo_archtop.json: kerfed_lining {width_mm:12, height_mm:18}

Connection to binding_geometry.py:
    BendRadiusCheck in binding_geometry.py covers binding strips.
    This module covers the kerfed lining that accepts the binding channel.
    Both feed into the construction sequence for body assembly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Species data for kerfing materials
# Bending modulus and strength are CROSS-GRAIN values because the web
# bends perpendicular to the grain direction of the kerfing stock.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KerfingSpecies:
    """
    Cross-grain mechanical properties for a kerfing species.

    MOR_C_MPa is the cross-grain bending (flexural) strength — not the along-grain
    MOR from Wood Database tables. Cross-grain flexural MOR ≈ 30–35% of along-grain
    MOR for spruce (calibrated to Hayward's empirical 1/16" minimum web thickness).
    These values are sourced from USDA Wood Handbook tables and calibrated to
    match known working dimensions.

    E_C_GPa is the cross-grain Young's modulus (stiffness perpendicular to grain).
    This governs how stiff the web hinge is — higher values require closer spacing
    or smaller web to achieve the same bend radius without web fracture.
    """
    key: str
    label: str
    E_C_GPa: float       # Cross-grain Young's modulus (GPa)
    MOR_C_MPa: float     # Cross-grain bending strength (MPa) — calibrated
    typical_spacing_mm: float   # Recommended kerf spacing for this species
    # Species stiffness group: "flexible" | "standard" | "stiff"
    # Influences spacing recommendation and binding vs. lining suitability
    stiffness_group: str = "standard"
    notes: str = ""


KERFING_SPECIES: Dict[str, KerfingSpecies] = {
    # ── Flexible group: E_C < 0.55 GPa ────────────────────────────────────────
    # Forgiving — can tolerate wider spacing and thicker webs.
    "basswood": KerfingSpecies(
        key="basswood", label="American Basswood",
        E_C_GPa=0.40, MOR_C_MPa=15.0, typical_spacing_mm=5.0,
        stiffness_group="flexible",
        notes="Very flexible — wider spacing acceptable. "
              "Common in production instruments; lighter than spruce.",
    ),
    "poplar": KerfingSpecies(
        key="poplar", label="Yellow Poplar",
        E_C_GPa=0.45, MOR_C_MPa=14.0, typical_spacing_mm=5.0,
        stiffness_group="flexible",
        notes="Very flexible. Common in factory instruments; "
              "good glue surface, easy to work.",
    ),
    # ── Standard group: E_C 0.55–0.90 GPa ────────────────────────────────────
    # Standard guitar kerfing species. 3–4mm spacing, 1.6mm minimum web.
    "mahogany": KerfingSpecies(
        key="mahogany", label="Honduran Mahogany",
        E_C_GPa=0.65, MOR_C_MPa=25.0, typical_spacing_mm=4.0,
        stiffness_group="standard",
        notes="Moderate flexibility. High MOR_C — strong web. "
              "Used when kerfing must match mahogany sides.",
    ),
    "engelmann_spruce": KerfingSpecies(
        key="engelmann_spruce", label="Engelmann Spruce",
        E_C_GPa=0.65, MOR_C_MPa=11.5, typical_spacing_mm=4.0,
        stiffness_group="standard",
        notes="Slightly softer than Sitka. Suitable for kerfing stock.",
    ),
    "cedar_wrc": KerfingSpecies(
        key="cedar_wrc", label="Western Red Cedar",
        E_C_GPa=0.70, MOR_C_MPa=11.0, typical_spacing_mm=4.0,
        stiffness_group="standard",
        notes="Low MOR_C — more brittle cross-grain than spruce. "
              "Keep web at minimum (1.6mm). Used when matching cedar construction.",
    ),
    "european_spruce": KerfingSpecies(
        key="european_spruce", label="European Spruce",
        E_C_GPa=0.75, MOR_C_MPa=14.0, typical_spacing_mm=4.0,
        stiffness_group="standard",
        notes="Slightly softer E_C than Sitka, higher MOR_C. "
              "Common in classical and European instruments.",
    ),
    "sitka_spruce": KerfingSpecies(
        key="sitka_spruce", label="Sitka Spruce",
        E_C_GPa=0.85, MOR_C_MPa=13.0, typical_spacing_mm=4.0,
        stiffness_group="standard",
        notes="Most common kerfing material. MOR_C calibrated to Hayward's "
              "empirical 1/16in minimum web (1.6mm). Light, flexible, strong glue bond.",
    ),
    "rosewood_indian": KerfingSpecies(
        key="rosewood_indian", label="Indian Rosewood",
        E_C_GPa=0.90, MOR_C_MPa=20.0, typical_spacing_mm=3.5,
        stiffness_group="standard",
        notes="Denser than spruce. Higher MOR_C but also stiffer — keep spacing ≤4mm. "
              "Used to match rosewood sides in period-correct instruments.",
    ),
    # ── Stiff group: E_C > 0.90 GPa ──────────────────────────────────────────
    # Requires closer spacing. Not ideal for kerfed lining; suitable for binding bending.
    "maple": KerfingSpecies(
        key="maple", label="Hard Maple",
        E_C_GPa=1.10, MOR_C_MPa=38.0, typical_spacing_mm=3.0,
        stiffness_group="stiff",
        notes="Very stiff cross-grain. High MOR_C means it resists web fracture, "
              "but high E_C means more force required to bend. "
              "Requires 3mm maximum spacing for tight radius work. "
              "Pre-wetting or steam strongly recommended for radii < 80mm.",
    ),
    "redwood": KerfingSpecies(
        key="redwood", label="Redwood",
        E_C_GPa=0.60, MOR_C_MPa=11.0, typical_spacing_mm=4.0,
        stiffness_group="standard",
        notes="Similar to cedar. Used in redwood-topped instruments.",
    ),
}

# Standard kerf depth fraction
KERF_DEPTH_FRACTION: float = 0.70  # 70% of stock height — well-established rule
KERF_WEB_FRACTION: float = 0.30    # Remaining 30% is the web (hinge)

# Minimum glue area as fraction of total face area
# Below this the glue joint is structurally inadequate
MIN_GLUE_FRACTION: float = 0.60   # 60% minimum solid glue surface

# Minimum web thickness (uncut hinge between kerfs)
# Source: Hayward (Lost Art Press, 2023): 1/16" = 1.587mm empirical minimum.
# Below this the web splits along the grain under bending stress.
MIN_WEB_MM: float = 1.6   # 1/16" rounded to nearest 0.1mm

# Bandsaw kerf width (typical 3/16" blade): 1.5–2.0mm
# Table saw thin-kerf blade: 0.7mm
# Default: bandsaw (most builders use a bandsaw for kerfing)
DEFAULT_KERF_WIDTH_MM: float = 1.5


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class KerfingStripGeometrySpec:
    """
    Complete kerfing specification for a guitar body.

    All dimensions are for the kerfing stock in its manufactured state
    (before installation). The stock runs along the full body perimeter;
    dimensions are per the cross-section perpendicular to the body axis.

    Physical conventions:
        stock_height_mm:  the dimension that contacts the plate glue face.
                         Runs from top edge to side edge. Vertical in the
                         assembled guitar. Appears in SIDE_PROFILE data as
                         the kerfing offset (~6.35mm for Martin, 12–18mm
                         for archtop).
        stock_width_mm:  the dimension visible from inside the box.
                         Usually = stock_height_mm (square stock) or
                         slightly larger for archtop lining.
        kerf_depth_mm:   how deep the saw cuts — 70% of stock_height.
        web_thickness_mm: remaining uncut hinge — 30% of stock_height.
        kerf_spacing_mm: center-to-center distance between kerfs.
        kerf_width_mm:   actual saw blade kerf (cutting width).
    """
    # Species
    species_key: str
    species_label: str

    # Dimensions
    stock_height_mm: float       # glue face height (vertical in assembled guitar)
    stock_width_mm: float        # width visible from inside box
    kerf_depth_mm: float         # 70% of stock_height
    web_thickness_mm: float      # 30% of stock_height
    kerf_spacing_mm: float       # center-to-center
    kerf_width_mm: float         # saw blade kerf

    # Computed geometry
    min_bend_radius_geom_mm: float   # geometric limit (kerf closes)
    min_bend_radius_mat_mm: float    # material failure limit (web yields)
    min_bend_radius_mm: float        # governing limit = max of both

    # Glue area (for body_perimeter_mm supplied at compute time)
    body_perimeter_mm: float
    glue_area_mm2: float
    glue_fraction: float   # solid glue surface fraction (0–1)
    kerf_count: int

    # Status
    status: str             # "OK" | "TIGHT" | "INCREASE_KERF_DEPTH" | "REDUCE_SPACING"
    tightest_radius_mm: float  # tightest bend required for this body
    fits_tightest_radius: bool

    # Notes
    notes: str
    construction_note: str

    def to_dict(self) -> dict:
        return {
            "species": self.species_label,
            "stock_height_mm": self.stock_height_mm,
            "stock_width_mm": self.stock_width_mm,
            "kerf_depth_mm": self.kerf_depth_mm,
            "web_thickness_mm": self.web_thickness_mm,
            "kerf_spacing_mm": self.kerf_spacing_mm,
            "kerf_width_mm": self.kerf_width_mm,
            "min_bend_radius_mm": self.min_bend_radius_mm,
            "min_bend_radius_geom_mm": self.min_bend_radius_geom_mm,
            "min_bend_radius_mat_mm": self.min_bend_radius_mat_mm,
            "glue_area_mm2": round(self.glue_area_mm2, 0),
            "glue_fraction_pct": round(self.glue_fraction * 100, 1),
            "kerf_count": self.kerf_count,
            "status": self.status,
            "fits_tightest_radius": self.fits_tightest_radius,
        }


@dataclass
class KerfingResult:
    """
    Full kerfing analysis including top and back lining specifications.
    Top and back linings may have different heights in some designs.
    """
    top_lining: KerfingStripGeometrySpec
    back_lining: KerfingStripGeometrySpec
    body_perimeter_mm: float
    tightest_radius_mm: float   # tightest bend on this body (typically upper waist)
    overall_status: str
    design_notes: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Core calculation functions
# ─────────────────────────────────────────────────────────────────────────────

def compute_kerfing_geometry(
    species_key: str,
    stock_height_mm: float,
    kerf_spacing_mm: float,
    tightest_radius_mm: float,
    body_perimeter_mm: float,
    stock_width_mm: Optional[float] = None,
    kerf_width_mm: float = DEFAULT_KERF_WIDTH_MM,
    kerf_depth_fraction: float = KERF_DEPTH_FRACTION,
) -> KerfingStripGeometrySpec:
    """
    Compute full kerfing geometry specification.

    Args:
        species_key:         Species from KERFING_SPECIES (default "sitka_spruce")
        stock_height_mm:     Kerfing stock height (the glue face dimension, mm)
        kerf_spacing_mm:     Center-to-center kerf spacing (mm)
        tightest_radius_mm:  Tightest bend required on this body (mm).
                             For a flat-top OM this is the upper C-bout radius (~109mm).
                             For an archtop it's the upper waist (~60mm).
        body_perimeter_mm:   Total body perimeter (mm) for kerf count and glue area.
        stock_width_mm:      Stock width (perpendicular to glue face). Defaults to
                             stock_height_mm (square stock). Archtops often use wider
                             stock for the taller rim depth.
        kerf_width_mm:       Saw blade cutting width (mm). Default 1.5mm (bandsaw).
                             Use 0.7mm for thin-kerf table saw.
        kerf_depth_fraction: Kerf depth as fraction of stock_height (default 0.70).

    Returns:
        KerfingStripGeometrySpec with full geometry, status, and construction notes.
    """
    species = KERFING_SPECIES.get(species_key, KERFING_SPECIES["sitka_spruce"])
    if stock_width_mm is None:
        stock_width_mm = stock_height_mm

    # Derived dimensions
    kerf_depth_mm = stock_height_mm * kerf_depth_fraction
    web_thickness_mm = stock_height_mm * (1.0 - kerf_depth_fraction)

    # ── Geometric minimum bend radius ────────────────────────────────────────
    # The kerfing cannot bend tighter than the angle at which the kerf slot
    # fully closes. Each kerf slot of width W can accommodate a bend of:
    #   theta_per_kerf = W / web_thickness   (radians, small angle)
    # For center-to-center spacing S:
    #   R_geom = S / theta_per_kerf = S * web_thickness / W
    #
    # NOTE: the classical beam bending formula R_mat = E_C * web/2 / MOR_C
    # does NOT apply to kerfing. Kerfing webs are discrete hinges, not
    # continuous beams. Each web only bends by theta = kerf_w/web_thickness
    # (a tiny angle) regardless of total body radius. Material failure in
    # guitar kerfing is always cracking at thin webs (<1mm), not bending.
    if kerf_width_mm > 0:
        R_geom = (kerf_spacing_mm * web_thickness_mm) / kerf_width_mm
    else:
        R_geom = float('inf')

    # ── Web thickness structural check (replaces R_mat) ──────────────────────
    # Below 1mm the web splits along the grain under bending.
    # Above 1mm the geometry (R_geom) is the only practical constraint.
    web_too_thin = web_thickness_mm < MIN_WEB_MM

    # Governing minimum radius
    R_min = R_geom
    R_mat = 0.0   # kept for dataclass compatibility — not a radius constraint

    # ── Glue area ────────────────────────────────────────────────────────────
    # Solid glue area per mm of perimeter:
    #   A/mm = stock_height - (kerf_depth × kerf_width / kerf_spacing)
    glue_per_mm = stock_height_mm - (kerf_depth_mm * kerf_width_mm / kerf_spacing_mm)
    glue_area = glue_per_mm * body_perimeter_mm
    total_face_area = stock_height_mm * body_perimeter_mm
    glue_fraction = glue_area / total_face_area if total_face_area > 0 else 0
    kerf_count = int(body_perimeter_mm / kerf_spacing_mm)

    # ── Status ───────────────────────────────────────────────────────────────
    fits = R_min <= tightest_radius_mm
    if web_too_thin:
        status = "INCREASE_KERF_DEPTH"
        notes = (
            f"Web thickness {web_thickness_mm:.1f}mm is below 1.0mm structural minimum. "
            f"Reduce kerf depth fraction below {kerf_depth_fraction:.0%} or increase stock height."
        )
    elif not fits:
        status = "REDUCE_SPACING"
        max_sp = _max_spacing_for_radius(web_thickness_mm, tightest_radius_mm, kerf_width_mm)
        notes = (
            f"Kerf spacing {kerf_spacing_mm:.0f}mm with {kerf_width_mm:.1f}mm kerf produces "
            f"R_min = {R_min:.0f}mm, which exceeds tightest required radius {tightest_radius_mm:.0f}mm. "
            f"Reduce spacing to ≤{max_sp:.1f}mm or widen the saw kerf width."
        )
    elif glue_fraction < MIN_GLUE_FRACTION:
        status = "TIGHT"
        notes = (
            f"Kerfing will bend adequately (R_min {R_min:.0f}mm ≤ {tightest_radius_mm:.0f}mm) "
            f"but glue surface fraction {glue_fraction:.0%} is below recommended minimum "
            f"{MIN_GLUE_FRACTION:.0%}. Reduce kerf depth or spacing."
        )
    else:
        status = "OK"
        notes = (
            f"R_min = {R_min:.0f}mm — fits tightest radius {tightest_radius_mm:.0f}mm with "
            f"{tightest_radius_mm - R_min:.0f}mm margin. "
            f"Glue fraction {glue_fraction:.0%} — adequate."
        )

    # ── Construction note ─────────────────────────────────────────────────────
    construction_note = (
        f"Cut {kerf_count} kerfs at {kerf_spacing_mm:.0f}mm spacing "
        f"({kerf_depth_mm:.1f}mm deep, {web_thickness_mm:.1f}mm web). "
        f"Species: {species.label}. "
        f"Min bend radius: {R_min:.0f}mm. "
        f"Glue area: {glue_area:.0f}mm² ({glue_fraction:.0%} solid)."
    )

    return KerfingStripGeometrySpec(
        species_key=species_key,
        species_label=species.label,
        stock_height_mm=stock_height_mm,
        stock_width_mm=stock_width_mm,
        kerf_depth_mm=round(kerf_depth_mm, 2),
        web_thickness_mm=round(web_thickness_mm, 2),
        kerf_spacing_mm=kerf_spacing_mm,
        kerf_width_mm=kerf_width_mm,
        min_bend_radius_geom_mm=round(R_geom, 1),
        min_bend_radius_mat_mm=round(R_mat, 1),
        min_bend_radius_mm=round(R_min, 1),
        body_perimeter_mm=round(body_perimeter_mm, 0),
        glue_area_mm2=round(glue_area, 0),
        glue_fraction=round(glue_fraction, 3),
        kerf_count=kerf_count,
        status=status,
        tightest_radius_mm=tightest_radius_mm,
        fits_tightest_radius=fits,
        notes=notes,
        construction_note=construction_note,
    )


def _max_spacing_for_radius(
    web_thickness_mm: float,
    target_radius_mm: float,
    kerf_width_mm: float,
) -> float:
    """Maximum kerf spacing to achieve a target bend radius."""
    return (target_radius_mm * kerf_width_mm) / web_thickness_mm


def solve_spacing_for_radius(
    species_key: str,
    stock_height_mm: float,
    target_radius_mm: float,
    kerf_width_mm: float = DEFAULT_KERF_WIDTH_MM,
    kerf_depth_fraction: float = KERF_DEPTH_FRACTION,
) -> float:
    """
    Compute the maximum kerf spacing that will achieve a target bend radius.

    Useful for working backwards from a known body geometry:
    "I have a 60mm waist radius — what kerf spacing do I need?"

    Args:
        species_key:         Species from KERFING_SPECIES
        stock_height_mm:     Kerfing stock height (mm)
        target_radius_mm:    Required minimum bend radius (mm)
        kerf_width_mm:       Saw blade kerf (mm)
        kerf_depth_fraction: Kerf depth fraction (default 0.70)

    Returns:
        Maximum spacing_mm that achieves target_radius. Round DOWN to
        nearest 0.5mm for a safety margin.
    """
    web = stock_height_mm * (1.0 - kerf_depth_fraction)
    spacing = _max_spacing_for_radius(web, target_radius_mm, kerf_width_mm)
    return round(spacing, 2)


def estimate_body_perimeter(
    lower_bout_mm: float,
    upper_bout_mm: float,
    waist_mm: float,
    body_length_mm: float,
) -> float:
    """
    Estimate body perimeter from bout and body dimensions.

    Uses an elliptical arc approximation for each body section.
    Accuracy: ±5% for typical guitar shapes.

    Args:
        lower_bout_mm: Maximum lower bout width (mm)
        upper_bout_mm: Maximum upper bout width (mm)
        waist_mm:      Waist width (mm)
        body_length_mm: Full body length (mm)

    Returns:
        Estimated perimeter in mm. Multiply by 2 for kerfing total
        (top and back both need lining).
    """
    # Divide body into three sections: upper bout, waist transition, lower bout
    # Each approximated as an ellipse arc
    section_lower = body_length_mm * 0.45
    section_waist = body_length_mm * 0.15
    section_upper = body_length_mm * 0.40

    # Each section: half-ellipse perimeter ≈ π × √((a² + b²)/2) (Ramanujan approx)
    def half_ellipse(a, b):
        # a = half-length, b = half-width
        return math.pi * math.sqrt((a**2 + b**2) / 2.0)

    p_lower = half_ellipse(section_lower / 2, lower_bout_mm / 2)
    p_upper = half_ellipse(section_upper / 2, upper_bout_mm / 2)
    p_waist = 2 * section_waist  # waist section is approximately straight

    # Total half-perimeter (one side of the body)
    half_perim = p_lower + p_waist + p_upper

    # Full perimeter = 2 × half-perimeter (the body has two sides)
    return round(half_perim * 2, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Standard presets
# ─────────────────────────────────────────────────────────────────────────────

def kerfing_for_flat_top(
    body_style: str = "om",
    species_key: str = "sitka_spruce",
    kerf_spacing_mm: float = 4.0,
    kerf_width_mm: float = DEFAULT_KERF_WIDTH_MM,
) -> KerfingResult:
    """
    Compute kerfing for a standard flat-top guitar body.

    Uses standard dimensions per body style from instrument_geometry specs.
    Top and back use the same lining height (standard for flat-tops).

    Args:
        body_style:     "om" | "dreadnought" | "000" | "parlor" | "classical" | "jumbo"
        species_key:    Kerfing wood species
        kerf_spacing_mm: Center-to-center spacing (mm)
        kerf_width_mm:  Saw blade kerf (mm)

    Returns:
        KerfingResult with top and back lining specs.
    """
    # Body geometry lookup (from instrument_geometry specs)
    BODY_STYLES = {
        "om":          {"lower": 381, "upper": 300, "waist": 241, "length": 495,
                        "stock_h": 10.0, "tightest_r": 109.0},
        "dreadnought": {"lower": 397, "upper": 311, "waist": 280, "length": 508,
                        "stock_h": 10.0, "tightest_r": 130.0},
        "000":         {"lower": 369, "upper": 292, "waist": 231, "length": 486,
                        "stock_h": 10.0, "tightest_r": 100.0},
        "parlor":      {"lower": 330, "upper": 270, "waist": 210, "length": 450,
                        "stock_h": 8.0,  "tightest_r": 80.0},
        "jumbo":       {"lower": 432, "upper": 330, "waist": 295, "length": 520,
                        "stock_h": 12.0, "tightest_r": 150.0},
        "classical":   {"lower": 370, "upper": 285, "waist": 225, "length": 480,
                        "stock_h": 8.0,  "tightest_r": 90.0},
        "grand_auditorium": {"lower": 400, "upper": 305, "waist": 260, "length": 502,
                        "stock_h": 10.0, "tightest_r": 120.0},
    }
    dims = BODY_STYLES.get(body_style.lower(), BODY_STYLES["om"])

    perim = estimate_body_perimeter(
        dims["lower"], dims["upper"], dims["waist"], dims["length"]
    )

    spec = compute_kerfing_geometry(
        species_key=species_key,
        stock_height_mm=dims["stock_h"],
        kerf_spacing_mm=kerf_spacing_mm,
        tightest_radius_mm=dims["tightest_r"],
        body_perimeter_mm=perim,
        kerf_width_mm=kerf_width_mm,
    )

    notes = [
        f"Body style: {body_style.upper()}. "
        f"Estimated perimeter: {perim:.0f}mm.",
        f"Tightest bend (upper C-bout): {dims['tightest_r']:.0f}mm.",
    ]
    if spec.status != "OK":
        notes.append(f"⚠ {spec.notes}")

    return KerfingResult(
        top_lining=spec,
        back_lining=spec,   # flat-tops use same height top and back
        body_perimeter_mm=perim,
        tightest_radius_mm=dims["tightest_r"],
        overall_status=spec.status,
        design_notes=notes,
    )


def kerfing_for_archtop(
    species_key: str = "sitka_spruce",
    lower_bout_mm: float = 432.0,
    stock_height_top_mm: float = 18.0,  # taller for archtop rim depth
    stock_height_back_mm: float = 18.0,
    kerf_spacing_mm: float = 4.0,
    kerf_width_mm: float = DEFAULT_KERF_WIDTH_MM,
) -> KerfingResult:
    """
    Compute kerfing for an archtop guitar.

    Archtop kerfing uses taller stock (18–25mm height) to match the
    deeper rim. The tightest bend radius on an archtop is the upper
    waist, which is gentler than flat-top C-bouts (~60–80mm).

    Args:
        species_key:            Kerfing wood species
        lower_bout_mm:          Lower bout width (mm)
        stock_height_top_mm:    Top lining height (mm). Matches rim depth.
        stock_height_back_mm:   Back lining height (mm).
        kerf_spacing_mm:        Center-to-center spacing
        kerf_width_mm:          Saw blade kerf

    Returns:
        KerfingResult for archtop construction.
    """
    # Standard 17" archtop: lower bout 432mm, upper bout 330mm, waist 280mm
    upper_bout = lower_bout_mm * 0.764
    waist = lower_bout_mm * 0.648
    body_length = 520.0
    tightest_r = 60.0  # archtop upper waist is gentler than flat-top

    perim = estimate_body_perimeter(lower_bout_mm, upper_bout, waist, body_length)

    top_spec = compute_kerfing_geometry(
        species_key=species_key,
        stock_height_mm=stock_height_top_mm,
        kerf_spacing_mm=kerf_spacing_mm,
        tightest_radius_mm=tightest_r,
        body_perimeter_mm=perim,
        stock_width_mm=stock_height_top_mm,
        kerf_width_mm=kerf_width_mm,
    )
    back_spec = compute_kerfing_geometry(
        species_key=species_key,
        stock_height_mm=stock_height_back_mm,
        kerf_spacing_mm=kerf_spacing_mm,
        tightest_radius_mm=tightest_r,
        body_perimeter_mm=perim,
        stock_width_mm=stock_height_back_mm,
        kerf_width_mm=kerf_width_mm,
    )

    overall = "OK" if top_spec.status == "OK" and back_spec.status == "OK" else "ISSUE"
    return KerfingResult(
        top_lining=top_spec,
        back_lining=back_spec,
        body_perimeter_mm=perim,
        tightest_radius_mm=tightest_r,
        overall_status=overall,
        design_notes=[
            f"Archtop. Lower bout {lower_bout_mm:.0f}mm. "
            f"Tightest bend: {tightest_r:.0f}mm (upper waist).",
            "Archtop kerfing uses taller stock to match deeper rim. "
            "Top and back may differ if rim depth tapers.",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Binding kerf cuts — compute_binding_kerf_cuts()
# Formula confirmed by multiple independent sources:
#   - Blocklayer.com KerfEng_V18.js (empirical calculator)
#   - KERF_BENDING.pdf (explicit 3-step derivation)
#   - Capone & Lanzara 2019, §3.1: "find the geometric spacing of the cuts
#     so when bent, the inside edges of the cuts join to create the curve"
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class BindingKerfResult:
    """
    Kerf cut specification for bending a wood strip to a target radius.

    This is for bending solid binding, purfling, or panel strips by CNC
    or saw kerf cuts that CLOSE COMPLETELY when the strip is bent.
    The cuts are spaced so the inner edge of each slot contacts the
    adjacent wood exactly when the full target curve is achieved.

    This is different from kerfed lining (which only needs to flex).
    Here the cuts must accommodate the full arc difference between
    inner and outer faces.

    Formula (confirmed by Blocklayer, Hayward, and Capone/Lanzara):
        n_cuts = ceil(thickness_mm × sweep_rad / kerf_width_mm)
        spacing = outer_arc / n_cuts   (even spacing along outer arc)

    Physics:
        Outer arc = R × sweep_rad
        Inner arc = (R - thickness) × sweep_rad
        Arc difference = thickness × sweep_rad  (this material must be removed)
        Each kerf removes kerf_width_mm of material when closed
        → n_cuts = arc_difference / kerf_width

    Species note:
        MOE affects how much force is needed to close the kerfs, not the
        count or spacing. For stiff species (maple, rosewood), more clamping
        force is required and pre-wetting may be necessary.
        The web_stress_check_ok field indicates whether the web thickness
        is within safe limits for the species (σ = E_C × web/(2R) ≤ MOR_C).
    """
    # Inputs
    species_key: str
    thickness_mm: float
    radius_mm: float
    sweep_degrees: float
    kerf_width_mm: float

    # Computed geometry
    n_cuts: int
    spacing_mm: float           # center-to-center along outer arc
    outer_arc_mm: float
    inner_arc_mm: float
    arc_difference_mm: float

    # Web check (remaining wood between cuts)
    web_thickness_mm: float     # spacing - kerf_width
    web_min_mm: float           # Hayward floor = 1.6mm
    web_ok: bool

    # Material stress check
    web_stress_MPa: float       # σ = E_C × web_depth/(2R_in) at min web
    web_allowable_MPa: float    # MOR_C × 0.5 (sf=0.5)
    web_stress_check_ok: bool

    # Cut positions from start of strip (outer arc)
    cut_positions_mm: List[float]

    # Status and notes
    status: str                 # "OK" | "WEB_TOO_THIN" | "MATERIAL_STRESS"
    construction_note: str


def compute_binding_kerf_cuts(
    thickness_mm: float,
    radius_mm: float,
    sweep_degrees: float,
    kerf_width_mm: float = 1.5,
    species_key: str = "sitka_spruce",
    radius_is_outside: bool = True,
) -> BindingKerfResult:
    """
    Modified Blocklayer-Hayward formula for bending a wood strip to a target radius.

    Combines two independent constraints derived from first principles:

    BLOCKLAYER (geometric lower bound on n):
        Each kerf slot removes kerf_width when closed. The arc difference
        between outer and inner faces = thickness × sweep_rad must be fully
        removed by the cuts.
            n_min = ceil(t × θ / w)

    HAYWARD (structural upper bound on n):
        Hayward (The Woodworker, 1939-1967) states empirically that the
        remaining web must be at least 1/16" = 1.6mm. More cuts → tighter
        spacing → thinner web. Maximum allowable cuts:
            n_max = floor(R_out × θ / (w + m))   where m = 1.6mm

    FEASIBILITY CONDITION (derived by combining):
        The constraints are simultaneously satisfiable when:
            w ≥ w_min = t × m / R_in
        Below w_min no valid n exists. This gives the minimum blade kerf
        width needed for a given geometry.

    OPTIMAL SOLUTION:
        n = n_min (fewest cuts → widest web → strongest joint)
        spacing = R_out × θ / n
        web = spacing - w   (guaranteed ≥ m by construction)

    GEOMETRIC IDENTITY (exact at non-integer n, conservative at ceil):
        n_exact × web_exact = R_in × θ = inner arc length
        The total uncut wood exactly equals the inner arc. Kerf bending
        is simply distributing the inner arc into n equal web segments.

    Args:
        thickness_mm:       Strip thickness (radial dimension, mm)
        radius_mm:          Target bend radius (mm), outer face by default
        sweep_degrees:      Angle of the curve (degrees)
        kerf_width_mm:      Actual blade/bit cutting width (mm)
        species_key:        Species from KERFING_SPECIES for stress check
        radius_is_outside:  True (default) = radius_mm is outside radius

    Returns:
        BindingKerfResult with n_cuts, spacing, feasibility, and stress check
    """
    sweep_rad = sweep_degrees * math.pi / 180.0

    # Normalize to outside radius
    if radius_is_outside:
        R_out = radius_mm
        R_in = radius_mm - thickness_mm
    else:
        R_in = radius_mm
        R_out = radius_mm + thickness_mm

    # Arc lengths
    outer_arc = R_out * sweep_rad
    inner_arc = R_in * sweep_rad
    arc_diff = outer_arc - inner_arc   # = thickness × sweep_rad (exactly)

    # Modified Blocklayer-Hayward formula
    # w_min: minimum blade width for Hayward feasibility
    w_min = (thickness_mm * MIN_WEB_MM) / R_in if R_in > 0 else float('inf')
    hayward_feasible = kerf_width_mm >= w_min

    # n_min: blocklayer geometric lower bound (must remove arc_diff)
    n_min = math.ceil(arc_diff / kerf_width_mm)
    if n_min < 1:
        n_min = 1

    # n_max: Hayward structural upper bound (web must be ≥ MIN_WEB_MM)
    n_max = math.floor(outer_arc / (kerf_width_mm + MIN_WEB_MM))

    # Optimal: fewest cuts → widest web → strongest joint
    # n_min ≤ n_max is guaranteed when w ≥ w_min (same algebraic condition)
    n_cuts = n_min
    spacing = outer_arc / n_cuts

    # Web (wood between adjacent cuts)
    web = spacing - kerf_width_mm

    # Cut positions along outer face (first cut at spacing/2 from edge
    # for symmetric arrangement, matching blocklayer convention)
    cut_positions = [spacing * (i + 0.5) for i in range(n_cuts)]

    # Web thickness check
    web_ok = web >= MIN_WEB_MM

    # Material stress check: σ = E_C × web_depth/(2R_in) ≤ MOR_C × sf
    #
    # The critical web depth is the REMAINING THICKNESS at the bottom of each kerf
    # slot — not the spacing between cuts (which is the horizontal gap along the strip).
    # For a properly cut kerf, the remaining depth approaches Hayward's MIN_WEB_MM.
    # We check at MIN_WEB_MM (the design floor) to flag whether even the minimum
    # web depth is safe for this species and bend radius.
    #
    # This is where MOE matters: stiffer species (higher E_C) produce more stress
    # at the same web depth and radius, requiring either steam/pre-wetting (reduces
    # effective E_C by 30-50%) or a larger radius.
    species = KERFING_SPECIES.get(species_key, KERFING_SPECIES["sitka_spruce"])
    E_C_Pa = species.E_C_GPa * 1e9
    MOR_C_Pa = species.MOR_C_MPa * 1e6
    SF = 0.50
    web_depth = MIN_WEB_MM  # design floor — check worst case (thinnest allowed web)
    sigma = E_C_Pa * (web_depth / 1000) / (2 * (R_in / 1000))  # Pa
    allowable = MOR_C_Pa * SF  # Pa
    stress_ok = sigma <= allowable

    # Status — report w_min, n_min, n_max for transparency
    if not hayward_feasible:
        status = "BLADE_TOO_NARROW"
        note = (
            f"Kerf {kerf_width_mm:.2f}mm < w_min {w_min:.4f}mm. "
            f"No valid n exists that satisfies both Blocklayer and Hayward constraints. "
            f"Minimum feasible kerf = t × m / R_in = "
            f"{thickness_mm:.1f} × {MIN_WEB_MM:.1f} / {R_in:.1f} = {w_min:.3f}mm. "
            f"Use a wider blade or increase the bend radius."
        )
    elif not web_ok:
        status = "WEB_TOO_THIN"
        note = (
            f"Web {web:.2f}mm < {MIN_WEB_MM:.1f}mm (Hayward). "
            f"n_min={n_min}, n_max={n_max}. "
            f"Reduce n or widen blade."
        )
    elif not stress_ok:
        status = "MATERIAL_STRESS"
        note = (
            f"Web stress {sigma/1e6:.1f} MPa exceeds allowable "
            f"{allowable/1e6:.1f} MPa for {species.label}. "
            f"Species is stiff (E_C = {species.E_C_GPa:.2f} GPa). "
            f"Use closer spacing (≤{math.floor(2 * R_in / 1000 * allowable / E_C_Pa * 1000 + kerf_width_mm):.0f}mm) "
            f"or pre-wet/steam the strip before bending."
        )
    else:
        status = "OK"
        note = (
            f"n_min={n_min}, n_max={n_max}, n={n_cuts}. "
            f"w_min={w_min:.3f}mm (blade feasibility). "
            f"{n_cuts} cuts × {kerf_width_mm:.1f}mm at {spacing:.2f}mm spacing. "
            f"Web {web:.2f}mm. "
            f"Stress {sigma/1e6:.1f}/{allowable/1e6:.1f} MPa. "
            f"Species: {species.label} ({species.stiffness_group})."
        )

    return BindingKerfResult(
        species_key=species_key,
        thickness_mm=thickness_mm,
        radius_mm=radius_mm,
        sweep_degrees=sweep_degrees,
        kerf_width_mm=kerf_width_mm,
        n_cuts=n_cuts,
        spacing_mm=round(spacing, 3),
        outer_arc_mm=round(outer_arc, 2),
        inner_arc_mm=round(inner_arc, 2),
        arc_difference_mm=round(arc_diff, 3),
        web_thickness_mm=round(web, 3),
        web_min_mm=MIN_WEB_MM,
        web_ok=web_ok,
        web_stress_MPa=round(sigma / 1e6, 2),
        web_allowable_MPa=round(allowable / 1e6, 2),
        web_stress_check_ok=stress_ok,
        cut_positions_mm=[round(p, 2) for p in cut_positions],
        status=status,
        construction_note=note,
    )
