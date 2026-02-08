"""Temperament ratio constant tables.

Extracted from alternative_temperaments.py (WP-3) for god-object decomposition.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


# =============================================================================
# CONSTANTS: Temperament Ratio Tables
# =============================================================================

# Just Intonation - Major scale ratios (pure intervals)
JUST_MAJOR_RATIOS: Dict[int, Tuple[int, int]] = {
    0: (1, 1),      # Unison: 1/1
    1: (16, 15),    # Minor 2nd: 16/15 (diatonic semitone)
    2: (9, 8),      # Major 2nd: 9/8 (whole tone)
    3: (6, 5),      # Minor 3rd: 6/5
    4: (5, 4),      # Major 3rd: 5/4 (the "sweet" third)
    5: (4, 3),      # Perfect 4th: 4/3
    6: (45, 32),    # Tritone: 45/32 (augmented 4th)
    7: (3, 2),      # Perfect 5th: 3/2 (the anchor)
    8: (8, 5),      # Minor 6th: 8/5
    9: (5, 3),      # Major 6th: 5/3
    10: (9, 5),     # Minor 7th: 9/5 (harmonic)
    11: (15, 8),    # Major 7th: 15/8
    12: (2, 1),     # Octave: 2/1
}

# Pythagorean tuning - built on pure 5ths (3:2)
PYTHAGOREAN_RATIOS: Dict[int, Tuple[int, int]] = {
    0: (1, 1),
    1: (256, 243),   # Pythagorean limma
    2: (9, 8),       # Pythagorean whole tone
    3: (32, 27),     # Pythagorean minor 3rd
    4: (81, 64),     # Pythagorean major 3rd (ditone - quite sharp!)
    5: (4, 3),
    6: (729, 512),   # Pythagorean tritone
    7: (3, 2),
    8: (128, 81),
    9: (27, 16),
    10: (16, 9),
    11: (243, 128),
    12: (2, 1),
}

# Quarter-comma Meantone - compromise for better 3rds
MEANTONE_RATIOS: Dict[int, Tuple[int, int]] = {
    0: (1, 1),
    1: (1.0449, 1),
    2: (1.1180, 1),
    3: (1.1963, 1),
    4: (5, 4),        # Pure major 3rd
    5: (1.3375, 1),
    6: (1.3975, 1),
    7: (1.4953, 1),   # Narrow 5th
    8: (1.6000, 1),
    9: (1.6719, 1),
    10: (1.7889, 1),
    11: (1.8692, 1),
    12: (2, 1),
}

# Equal temperament ratios for reference
EQUAL_12TET_RATIOS: Dict[int, Tuple[float, int]] = {
    i: (2 ** (i / 12), 1) for i in range(13)
}

# Standard guitar tuning: string open pitches relative to low E
STANDARD_TUNING_SEMITONES: List[int] = [0, 5, 10, 15, 19, 24]  # E A D G B E

# Note names for reference
NOTE_NAMES: List[str] = [
    "E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#",
]

# Interval names
INTERVAL_NAMES: List[str] = [
    "Unison", "Minor 2nd", "Major 2nd", "Minor 3rd",
    "Major 3rd", "Perfect 4th", "Tritone", "Perfect 5th",
    "Minor 6th", "Major 6th", "Minor 7th", "Major 7th", "Octave",
]
