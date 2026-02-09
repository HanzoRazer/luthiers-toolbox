"""
Rosette Preset Matrices — Traditional craftsman pattern library.

Each preset is a historical or modern matrix formula for rosette ring fabrication.
Extracted from pattern_generator.py during WP-3 God-Object Decomposition.
"""

from __future__ import annotations

from typing import Dict

from .pattern_schemas import MatrixFormula


PRESET_MATRICES: Dict[str, MatrixFormula] = {
    # =========================================================================
    # BASIC / BEGINNER PATTERNS
    # =========================================================================
    "classic_rope_5x9": MatrixFormula(
        name="Classic Rope 5x9",
        rows=[
            {"black": 5, "white": 2},
            {"black": 5, "white": 2},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 4, "white": 3},
        ],
        column_sequence=[1, 2, 2, 1, 3, 4, 5, 4, 3],
        strip_width_mm=1.0,
        strip_thickness_mm=0.6,
        chip_length_mm=2.0,
        notes="Traditional Spanish rope pattern from craftsman video"
    ),

    "simple_rope_3x5": MatrixFormula(
        name="Simple Rope 3x5",
        rows=[
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
            {"black": 3, "white": 2},
        ],
        column_sequence=[1, 2, 3, 2, 1],
        strip_width_mm=1.2,
        strip_thickness_mm=0.6,
        notes="Simplified rope pattern for beginners"
    ),

    "diagonal_stripe_4x7": MatrixFormula(
        name="Diagonal Stripe 4x7",
        rows=[
            {"black": 4, "white": 1},
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
            {"black": 1, "white": 4},
        ],
        column_sequence=[1, 2, 3, 4, 3, 2, 1],
        strip_width_mm=1.0,
        strip_thickness_mm=0.5,
        notes="Creates diagonal stripe effect"
    ),

    "chevron_5x7": MatrixFormula(
        name="Chevron 5x7",
        rows=[
            {"black": 1, "white": 4},
            {"black": 2, "white": 3},
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
            {"black": 1, "white": 4},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3],
        strip_width_mm=0.8,
        strip_thickness_mm=0.6,
        notes="V-shaped chevron pattern"
    ),

    # =========================================================================
    # ANTONIO DE TORRES PATTERNS (Spanish, c. 1850-1892)
    # =========================================================================
    "torres_simple_rope_4x7": MatrixFormula(
        name="Torres Simple Rope",
        rows=[
            {"black": 4, "white": 2},
            {"black": 3, "white": 3},
            {"black": 3, "white": 3},
            {"black": 4, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 3, 2, 1],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.5,
        notes="Torres-style simple rope, symmetric pattern. Common on his later instruments."
    ),

    "torres_ladder_6x9": MatrixFormula(
        name="Torres Ladder Pattern",
        rows=[
            {"black": 6, "white": 1},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Torres ladder/staircase pattern. Creates diagonal stepping effect."
    ),

    "torres_wave_5x11": MatrixFormula(
        name="Torres Wave Pattern",
        rows=[
            {"black": 2, "white": 5},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 2, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Torres wave/undulating pattern. Creates flowing visual movement."
    ),

    "torres_diamond_7x9": MatrixFormula(
        name="Torres Diamond Mosaic",
        rows=[
            {"black": 1, "white": 6},
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
            {"black": 1, "white": 6},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 6, 5],
        strip_width_mm=0.6,
        strip_thickness_mm=0.5,
        chip_length_mm=1.5,
        notes="Torres diamond/lozenge pattern. Classic Spanish mosaic style."
    ),

    # =========================================================================
    # HERMANN HAUSER PATTERNS (German, c. 1920-1952)
    # =========================================================================
    "hauser_rope_6x11": MatrixFormula(
        name="Hauser Classic Rope",
        rows=[
            {"black": 6, "white": 2},
            {"black": 5, "white": 3},
            {"black": 4, "white": 4},
            {"black": 4, "white": 4},
            {"black": 5, "white": 3},
            {"black": 6, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Hauser-style rope pattern. Refined German precision, symmetric."
    ),

    "hauser_herringbone_8x13": MatrixFormula(
        name="Hauser Herringbone",
        rows=[
            {"black": 1, "white": 7},
            {"black": 2, "white": 6},
            {"black": 3, "white": 5},
            {"black": 4, "white": 4},
            {"black": 5, "white": 3},
            {"black": 6, "white": 2},
            {"black": 7, "white": 1},
            {"black": 8, "white": 0},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3],
        strip_width_mm=0.6,
        strip_thickness_mm=0.4,
        chip_length_mm=1.5,
        notes="Hauser herringbone variation. High contrast diagonal effect."
    ),

    "hauser_segovia_7x11": MatrixFormula(
        name="Hauser Segovia Model",
        rows=[
            {"black": 5, "white": 3},
            {"black": 4, "white": 4},
            {"black": 3, "white": 5},
            {"black": 2, "white": 6},
            {"black": 3, "white": 5},
            {"black": 4, "white": 4},
            {"black": 5, "white": 3},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3],
        strip_width_mm=0.65,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Pattern style used on Hauser guitars made for Andrés Segovia."
    ),

    # =========================================================================
    # JOSÉ ROMANILLOS PATTERNS (Spanish/British, contemporary master)
    # =========================================================================
    "romanillos_rope_5x9": MatrixFormula(
        name="Romanillos Rope",
        rows=[
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Romanillos-style rope. Clean, balanced Spanish tradition."
    ),

    "romanillos_mosaic_6x11": MatrixFormula(
        name="Romanillos Mosaic",
        rows=[
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Romanillos mosaic pattern. Elegant Spanish-British fusion."
    ),

    # =========================================================================
    # IGNACIO FLETA PATTERNS (Spanish, c. 1930-1977)
    # =========================================================================
    "fleta_rope_6x9": MatrixFormula(
        name="Fleta Barcelona Rope",
        rows=[
            {"black": 6, "white": 1},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
            {"black": 6, "white": 1},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3],
        strip_width_mm=0.75,
        strip_thickness_mm=0.5,
        chip_length_mm=1.7,
        notes="Fleta-style rope pattern. Bold, high-contrast Barcelona tradition."
    ),

    "fleta_wave_7x11": MatrixFormula(
        name="Fleta Wave",
        rows=[
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 5, "white": 2},
            {"black": 6, "white": 1},
            {"black": 5, "white": 2},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Fleta wave pattern. Dramatic visual flow."
    ),

    # =========================================================================
    # ROBERT BOUCHET PATTERNS (French, c. 1946-1986)
    # =========================================================================
    "bouchet_french_rope_5x9": MatrixFormula(
        name="Bouchet French Rope",
        rows=[
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1],
        strip_width_mm=0.85,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Bouchet-style rope. Refined French elegance, subtle contrast."
    ),

    "bouchet_mosaic_6x11": MatrixFormula(
        name="Bouchet Mosaic",
        rows=[
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.75,
        strip_thickness_mm=0.5,
        chip_length_mm=1.7,
        notes="Bouchet mosaic pattern. Lighter, airy French aesthetic."
    ),

    # =========================================================================
    # FRANCISCO SIMPLICIO PATTERNS (Spanish, c. 1920-1932)
    # =========================================================================
    "simplicio_ornate_8x13": MatrixFormula(
        name="Simplicio Ornate",
        rows=[
            {"black": 2, "white": 6},
            {"black": 3, "white": 5},
            {"black": 5, "white": 3},
            {"black": 6, "white": 2},
            {"black": 6, "white": 2},
            {"black": 5, "white": 3},
            {"black": 3, "white": 5},
            {"black": 2, "white": 6},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3],
        strip_width_mm=0.6,
        strip_thickness_mm=0.45,
        chip_length_mm=1.4,
        notes="Simplicio ornate pattern. Complex, decorative Barcelona style."
    ),

    "simplicio_zigzag_6x11": MatrixFormula(
        name="Simplicio Zigzag",
        rows=[
            {"black": 6, "white": 1},
            {"black": 4, "white": 3},
            {"black": 2, "white": 5},
            {"black": 2, "white": 5},
            {"black": 4, "white": 3},
            {"black": 6, "white": 1},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Simplicio zigzag pattern. Bold angular design."
    ),

    # =========================================================================
    # MODERN / CONTEMPORARY PATTERNS
    # =========================================================================
    "modern_minimalist_3x5": MatrixFormula(
        name="Modern Minimalist",
        rows=[
            {"black": 2, "white": 3},
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
        ],
        column_sequence=[1, 2, 3, 2, 1],
        strip_width_mm=1.0,
        strip_thickness_mm=0.6,
        chip_length_mm=2.0,
        notes="Contemporary minimalist design. Clean, simple, modern aesthetic."
    ),

    "modern_bold_4x7": MatrixFormula(
        name="Modern Bold Stripe",
        rows=[
            {"black": 5, "white": 1},
            {"black": 3, "white": 3},
            {"black": 3, "white": 3},
            {"black": 5, "white": 1},
        ],
        column_sequence=[1, 2, 3, 4, 3, 2, 1],
        strip_width_mm=1.2,
        strip_thickness_mm=0.6,
        chip_length_mm=2.2,
        notes="Modern bold stripe. High contrast contemporary look."
    ),

    "modern_asymmetric_5x8": MatrixFormula(
        name="Modern Asymmetric",
        rows=[
            {"black": 5, "white": 1},
            {"black": 4, "white": 2},
            {"black": 3, "white": 3},
            {"black": 2, "white": 4},
            {"black": 1, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2],
        strip_width_mm=0.9,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Contemporary asymmetric gradient. Non-traditional, artistic."
    ),

    # =========================================================================
    # THREE-COLOR PATTERNS (Advanced)
    # =========================================================================
    "tricolor_spanish_6x9": MatrixFormula(
        name="Tricolor Spanish",
        rows=[
            {"black": 3, "white": 2, "brown": 2},
            {"black": 2, "white": 3, "brown": 2},
            {"black": 2, "white": 2, "brown": 3},
            {"black": 2, "white": 2, "brown": 3},
            {"black": 2, "white": 3, "brown": 2},
            {"black": 3, "white": 2, "brown": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Three-color Spanish pattern. Ebony, maple, rosewood combination."
    ),

    "tricolor_gradient_5x9": MatrixFormula(
        name="Tricolor Gradient",
        rows=[
            {"black": 4, "white": 1, "brown": 2},
            {"black": 3, "white": 2, "brown": 2},
            {"black": 2, "white": 3, "brown": 2},
            {"black": 2, "white": 2, "brown": 3},
            {"black": 1, "white": 2, "brown": 4},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1],
        strip_width_mm=0.75,
        strip_thickness_mm=0.5,
        chip_length_mm=1.7,
        notes="Three-color gradient. Transitions dark to light to medium."
    ),

    "german_tricolor_rope_6x11": MatrixFormula(
        name="German Tricolor Rope",
        rows=[
            {"red": 3, "white": 2, "green": 2},
            {"red": 2, "white": 3, "green": 2},
            {"red": 2, "white": 2, "green": 3},
            {"red": 2, "white": 2, "green": 3},
            {"red": 2, "white": 3, "green": 2},
            {"red": 3, "white": 2, "green": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="German tricolor twisted rope (Seil) pattern. Red, white, green dyed veneers. Classic Central European lutherie tradition."
    ),

    # =========================================================================
    # SIMPLE / BEGINNER PATTERNS
    # =========================================================================
    "simple_trapezoid_2x1": MatrixFormula(
        name="Simple Trapezoid",
        rows=[
            {"cherry": 1, "mahogany": 1},
        ],
        column_sequence=[1, 1, 1, 1, 1, 1, 1, 1],
        strip_width_mm=3.0,
        strip_thickness_mm=0.6,
        chip_length_mm=6.0,
        notes="Simple alternating trapezoidal segments. Cherry and mahogany. Beginner-friendly, minimal cuts."
    ),

    "simple_alternating_2x8": MatrixFormula(
        name="Simple Alternating",
        rows=[
            {"light": 1, "dark": 0},
            {"light": 0, "dark": 1},
        ],
        column_sequence=[1, 2, 1, 2, 1, 2, 1, 2],
        strip_width_mm=2.5,
        strip_thickness_mm=0.6,
        chip_length_mm=5.0,
        notes="Basic alternating light/dark pattern. Any two contrasting woods. Simplest rosette design."
    ),
}
