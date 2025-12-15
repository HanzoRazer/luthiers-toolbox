"""
Alternative Temperament Fret Calculations

Implements non-equal temperament fret positions for the Smart Guitar concept.
Supports just intonation, Pythagorean, meantone, and key-specific optimization.

The Smart Guitar concept allows frets to be positioned at mathematically 
"perfect" intervals for a specific key, rather than the compromise positions
of equal temperament (12-TET).

Theory:
    In 12-TET, each semitone has ratio 2^(1/12) ≈ 1.05946
    This means intervals like major 3rds are ~14 cents sharp of pure 5:4
    
    In Just Intonation, intervals use simple ratios:
    - Perfect 5th: 3:2 (702 cents) vs 12-TET 700 cents
    - Major 3rd: 5:4 (386 cents) vs 12-TET 400 cents (14 cents sharp!)
    - Perfect 4th: 4:3 (498 cents) vs 12-TET 500 cents

References:
    - https://www.liutaiomottola.com/formulae/fret.htm
    - "Tuning and Temperament" by J. Murray Barbour
    - True Temperament guitars (commercial implementation)

Author: Luthier's Toolbox
Date: December 2025
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


# =============================================================================
# CONSTANTS: Temperament Ratio Tables
# =============================================================================

# Just Intonation - Major scale ratios (pure intervals)
JUST_MAJOR_RATIOS = {
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
PYTHAGOREAN_RATIOS = {
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
MEANTONE_RATIOS = {
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
EQUAL_12TET_RATIOS = {i: (2 ** (i / 12), 1) for i in range(13)}


class TemperamentSystem(str, Enum):
    """Available temperament systems."""
    EQUAL_12TET = "12-TET"
    JUST_MAJOR = "just_major"
    JUST_MINOR = "just_minor"
    PYTHAGOREAN = "pythagorean"
    MEANTONE_QUARTER = "meantone_1/4"
    CUSTOM = "custom"


@dataclass
class FretPosition:
    """
    Complete fret position data including temperament comparison.
    """
    fret_number: int
    equal_pos_mm: float
    alt_pos_mm: float
    deviation_cents: float
    interval_name: str
    ratio: Tuple[int, int]
    
    def to_dict(self) -> Dict:
        return {
            "fret_number": self.fret_number,
            "equal_pos_mm": self.equal_pos_mm,
            "alt_pos_mm": self.alt_pos_mm,
            "deviation_cents": self.deviation_cents,
            "interval_name": self.interval_name,
            "ratio": list(self.ratio),
        }


@dataclass
class StaggeredFret:
    """
    A fret with per-string positions (angled fret).
    """
    fret_number: int
    string_positions: List[float]
    endpoints: Tuple[Tuple[float, float], Tuple[float, float]]
    
    def to_dict(self) -> Dict:
        return {
            "fret_number": self.fret_number,
            "string_positions": self.string_positions,
            "endpoints": [list(p) for p in self.endpoints],
        }


# Standard guitar tuning: string open pitches relative to low E
STANDARD_TUNING_SEMITONES = [0, 5, 10, 15, 19, 24]  # E A D G B E

# Note names for reference
NOTE_NAMES = ["E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#"]

# Interval names
INTERVAL_NAMES = [
    "Unison", "Minor 2nd", "Major 2nd", "Minor 3rd", 
    "Major 3rd", "Perfect 4th", "Tritone", "Perfect 5th",
    "Minor 6th", "Major 6th", "Minor 7th", "Major 7th", "Octave"
]


# =============================================================================
# CORE CALCULATIONS
# =============================================================================

def ratio_to_float(ratio: Tuple[int, int]) -> float:
    """Convert (numerator, denominator) ratio to float."""
    num, den = ratio
    return num / den


def ratio_to_cents(ratio: Tuple[int, int]) -> float:
    """Convert frequency ratio to cents (100 cents = 1 semitone)."""
    return 1200 * math.log2(ratio_to_float(ratio))


def position_from_ratio(ratio: float, scale_length_mm: float) -> float:
    """
    Convert frequency ratio to fret position from nut.
    
    The string length at a fret = scale_length / ratio
    So fret position from nut = scale_length - (scale_length / ratio)
    """
    return scale_length_mm - (scale_length_mm / ratio)


def compute_equal_temperament_position(
    scale_length_mm: float,
    fret_number: int
) -> float:
    """Compute fret position using standard 12-TET."""
    ratio = 2 ** (fret_number / 12)
    return position_from_ratio(ratio, scale_length_mm)


def compute_deviation_cents(
    equal_pos_mm: float,
    alt_pos_mm: float,
    scale_length_mm: float
) -> float:
    """
    Compute deviation in cents between two fret positions.
    
    Positive = alternative is sharper (fret closer to nut)
    Negative = alternative is flatter (fret closer to bridge)
    """
    equal_length = scale_length_mm - equal_pos_mm
    alt_length = scale_length_mm - alt_pos_mm
    
    if alt_length <= 0 or equal_length <= 0:
        return 0.0
    
    freq_ratio = equal_length / alt_length
    return 1200 * math.log2(freq_ratio)


# =============================================================================
# TEMPERAMENT POSITION CALCULATORS
# =============================================================================

def compute_just_intonation_positions(
    scale_length_mm: float,
    fret_count: int = 22,
) -> List[FretPosition]:
    """
    Compute fret positions using just intonation (pure intervals).
    """
    positions: List[FretPosition] = []
    
    for fret in range(1, fret_count + 1):
        semitone = fret % 12
        if semitone == 0:
            semitone = 12
        
        octave = (fret - 1) // 12
        
        just_ratio = JUST_MAJOR_RATIOS[semitone]
        just_ratio_float = ratio_to_float(just_ratio) * (2 ** octave)
        
        equal_pos = compute_equal_temperament_position(scale_length_mm, fret)
        alt_pos = position_from_ratio(just_ratio_float, scale_length_mm)
        deviation = compute_deviation_cents(equal_pos, alt_pos, scale_length_mm)
        
        interval = INTERVAL_NAMES[semitone] if semitone <= 12 else f"Fret {fret}"
        if octave > 0:
            interval = f"{interval} (+{octave} oct)"
        
        positions.append(FretPosition(
            fret_number=fret,
            equal_pos_mm=round(equal_pos, 4),
            alt_pos_mm=round(alt_pos, 4),
            deviation_cents=round(deviation, 2),
            interval_name=interval,
            ratio=just_ratio
        ))
    
    return positions


def compute_pythagorean_positions(
    scale_length_mm: float,
    fret_count: int = 22
) -> List[FretPosition]:
    """
    Compute fret positions using Pythagorean tuning.
    """
    positions: List[FretPosition] = []
    
    pyth_interval_names = [
        "Unison", "Limma", "Whole tone", "Minor 3rd", 
        "Ditone", "Perfect 4th", "Tritone", "Perfect 5th",
        "Minor 6th", "Major 6th", "Minor 7th", "Major 7th", "Octave"
    ]
    
    for fret in range(1, fret_count + 1):
        semitone = fret % 12
        if semitone == 0:
            semitone = 12
        octave = (fret - 1) // 12
        
        pyth_ratio = PYTHAGOREAN_RATIOS[semitone]
        pyth_ratio_float = ratio_to_float(pyth_ratio) * (2 ** octave)
        
        equal_pos = compute_equal_temperament_position(scale_length_mm, fret)
        alt_pos = position_from_ratio(pyth_ratio_float, scale_length_mm)
        deviation = compute_deviation_cents(equal_pos, alt_pos, scale_length_mm)
        
        interval = pyth_interval_names[semitone] if semitone <= 12 else f"Fret {fret}"
        if octave > 0:
            interval = f"{interval} (+{octave} oct)"
        
        positions.append(FretPosition(
            fret_number=fret,
            equal_pos_mm=round(equal_pos, 4),
            alt_pos_mm=round(alt_pos, 4),
            deviation_cents=round(deviation, 2),
            interval_name=interval,
            ratio=pyth_ratio
        ))
    
    return positions


def compute_meantone_positions(
    scale_length_mm: float,
    fret_count: int = 22
) -> List[FretPosition]:
    """
    Compute fret positions using quarter-comma meantone temperament.
    """
    positions: List[FretPosition] = []
    
    for fret in range(1, fret_count + 1):
        semitone = fret % 12
        if semitone == 0:
            semitone = 12
        octave = (fret - 1) // 12
        
        mt_ratio = MEANTONE_RATIOS[semitone]
        mt_ratio_float = ratio_to_float(mt_ratio) * (2 ** octave)
        
        equal_pos = compute_equal_temperament_position(scale_length_mm, fret)
        alt_pos = position_from_ratio(mt_ratio_float, scale_length_mm)
        deviation = compute_deviation_cents(equal_pos, alt_pos, scale_length_mm)
        
        interval = INTERVAL_NAMES[semitone] if semitone <= 12 else f"Fret {fret}"
        if octave > 0:
            interval = f"{interval} (+{octave} oct)"
        
        positions.append(FretPosition(
            fret_number=fret,
            equal_pos_mm=round(equal_pos, 4),
            alt_pos_mm=round(alt_pos, 4),
            deviation_cents=round(deviation, 2),
            interval_name=interval,
            ratio=mt_ratio
        ))
    
    return positions


# =============================================================================
# STAGGERED FRETS (Per-String Positioning)
# =============================================================================

def compute_staggered_fret_positions(
    scale_length_mm: float,
    fret_count: int = 22,
    string_count: int = 6,
    tuning_semitones: Optional[List[int]] = None,
    target_key: str = "E",
    temperament: TemperamentSystem = TemperamentSystem.JUST_MAJOR,
    nut_width_mm: float = 43.0,
    fret_width_mm: float = 56.0,
) -> List[StaggeredFret]:
    """
    Compute staggered (angled) fret positions optimized for a specific key.
    """
    if tuning_semitones is None:
        tuning_semitones = STANDARD_TUNING_SEMITONES[:string_count]
    
    try:
        key_offset = NOTE_NAMES.index(target_key.upper().replace("♯", "#").replace("♭", "b"))
    except ValueError:
        key_offset = 0
    
    if temperament == TemperamentSystem.JUST_MAJOR:
        ratios = JUST_MAJOR_RATIOS
    elif temperament == TemperamentSystem.PYTHAGOREAN:
        ratios = PYTHAGOREAN_RATIOS
    elif temperament == TemperamentSystem.MEANTONE_QUARTER:
        ratios = MEANTONE_RATIOS
    else:
        ratios = EQUAL_12TET_RATIOS
    
    staggered_frets: List[StaggeredFret] = []
    
    for fret in range(1, fret_count + 1):
        string_positions: List[float] = []
        
        for string_idx, open_pitch in enumerate(tuning_semitones):
            fretted_pitch = (open_pitch + fret) % 12
            interval_from_key = (fretted_pitch - key_offset) % 12
            
            ratio = ratios.get(interval_from_key, (1, 1))
            full_ratio = ratio_to_float(ratio) * (2 ** (fret // 12))
            
            base_pos = compute_equal_temperament_position(scale_length_mm, fret)
            pure_pos = position_from_ratio(full_ratio, scale_length_mm)
            
            # Use pure intervals for primary chord tones (root, 3rd, 5th)
            if interval_from_key in [0, 4, 7]:
                string_positions.append(round(pure_pos, 4))
            else:
                string_positions.append(round(base_pos, 4))
        
        # Calculate fret endpoints based on taper
        avg_pos = sum(string_positions) / len(string_positions)
        width_at_fret = nut_width_mm + (fret_width_mm - nut_width_mm) * (avg_pos / scale_length_mm)
        
        bass_y = -width_at_fret / 2
        treble_y = width_at_fret / 2
        
        staggered_frets.append(StaggeredFret(
            fret_number=fret,
            string_positions=string_positions,
            endpoints=(
                (string_positions[0], bass_y),
                (string_positions[-1], treble_y)
            )
        ))
    
    return staggered_frets


# =============================================================================
# ANALYSIS & COMPARISON
# =============================================================================

def analyze_temperament_deviations(
    scale_length_mm: float,
    fret_count: int = 22
) -> Dict[str, List[Dict]]:
    """
    Generate comparison analysis of all temperament systems.
    """
    return {
        "equal_12tet": [
            {
                "fret_number": f,
                "equal_pos_mm": round(compute_equal_temperament_position(scale_length_mm, f), 4),
                "alt_pos_mm": round(compute_equal_temperament_position(scale_length_mm, f), 4),
                "deviation_cents": 0.0,
                "interval_name": f"Fret {f}",
                "ratio": [1, 1]
            } for f in range(1, fret_count + 1)
        ],
        "just_major": [p.to_dict() for p in compute_just_intonation_positions(scale_length_mm, fret_count)],
        "pythagorean": [p.to_dict() for p in compute_pythagorean_positions(scale_length_mm, fret_count)],
        "meantone": [p.to_dict() for p in compute_meantone_positions(scale_length_mm, fret_count)],
    }


def get_temperament_info(temperament: TemperamentSystem) -> Dict[str, str]:
    """Get human-readable description of a temperament system."""
    descriptions = {
        TemperamentSystem.EQUAL_12TET: {
            "name": "Equal Temperament (12-TET)",
            "description": "Standard modern tuning. All semitones equal (2^(1/12)). "
                          "Works in all keys but no intervals are perfectly pure.",
            "best_for": "All-purpose playing, jazz, chromatic music",
            "tradeoffs": "Major 3rds ~14 cents sharp, minor 3rds ~16 cents flat"
        },
        TemperamentSystem.JUST_MAJOR: {
            "name": "Just Intonation (Major)",
            "description": "Pure integer ratios for beatless intervals. "
                          "Perfect 5ths (3:2) and major 3rds (5:4).",
            "best_for": "Single-key music, choral, early music",
            "tradeoffs": "Only works well in one key, wolf intervals in others"
        },
        TemperamentSystem.PYTHAGOREAN: {
            "name": "Pythagorean Tuning",
            "description": "Built entirely on pure 5ths (3:2). Medieval European tuning. "
                          "Very sharp major 3rds (81:64).",
            "best_for": "Monophonic melody, plainchant, medieval music",
            "tradeoffs": "Harsh major 3rds, Pythagorean comma issues"
        },
        TemperamentSystem.MEANTONE_QUARTER: {
            "name": "Quarter-Comma Meantone",
            "description": "Compromise tuning with pure major 3rds (5:4) but narrow 5ths. "
                          "Popular in Renaissance/Baroque keyboard music.",
            "best_for": "Renaissance music, keyboard in few keys",
            "tradeoffs": "Wolf 5th in distant keys, limited modulation"
        },
    }
    return descriptions.get(temperament, {
        "name": str(temperament),
        "description": "Custom temperament system",
        "best_for": "Specialized applications",
        "tradeoffs": "Depends on configuration"
    })


def list_temperament_systems() -> List[Dict]:
    """List all available temperament systems with descriptions."""
    return [
        {"id": t.value, **get_temperament_info(t)}
        for t in TemperamentSystem
        if t != TemperamentSystem.CUSTOM
    ]
