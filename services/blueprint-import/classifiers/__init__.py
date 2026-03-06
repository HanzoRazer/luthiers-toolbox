"""
Blueprint Instrument Classifiers
================================

ML-assisted classification system for identifying instrument types from blueprints.

Classifier Families:
- latin_american: Cuatro, Tiple, Requinto, Charango, Bandola
- grid_zone: STEM Guitar body grid zone classifier
- (future) acoustic_guitar: Dreadnought, OM, 000, Parlor, Jumbo
- (future) electric_guitar: Stratocaster, Telecaster, Les Paul, etc.
- (future) mandolin: A-style, F-style, Bouzouki

Author: Luthier's Toolbox
Version: 4.0.0
"""

from .latin_american import LatinAmericanStringsClassifier
from .grid_zone import (
    GridZoneClassifier,
    GridZone,
    GridZoneType,
    ZoneClassificationResult,
    ELECTRIC_GUITAR_GRID
)

__all__ = [
    'LatinAmericanStringsClassifier',
    'GridZoneClassifier',
    'GridZone',
    'GridZoneType',
    'ZoneClassificationResult',
    'ELECTRIC_GUITAR_GRID'
]

__version__ = '4.0.0'
